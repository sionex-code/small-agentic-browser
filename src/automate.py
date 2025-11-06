import asyncio
import json
import re
from patchright.async_api import async_playwright
from gemini import send_prompt
# Action planning prompt
ACTION_PROMPT = """
You are an autonomous browser agent. Your goal: {goal}

Current page visible elements:
{page_elements}

Current URL: {current_url}
Previous actions taken: {action_history}

Your task is to decide the NEXT action to take towards achieving the goal.
Supported actions:
1. click - Click an element (provide selector)
2. type - Type text into an input (provide selector and value)
3. press_enter - Press enter key on focused element (provide selector)
4. scroll_down - Scroll page down
5. scroll_up - Scroll page up
6. go_back - Go back in browser history
7. wait - Wait for page to load (2 seconds)
8. goal_completed - Mark goal as completed (provide reason)
Respond with ONLY a valid JSON object in this exact format:
{{
  "reasoning": "Your thought process about what to do next",
  "action": {{
    "type": "click|type|press_enter|scroll_down|scroll_up|go_back|wait|goal_completed",
    "selector": "CSS selector (for click/type/press_enter)",
    "value": "text to type (only for type action)",
    "reason": "why goal is completed (only for goal_completed)"
  }}
}}
IMPORTANT:
- Analyze the page elements carefully
- Choose selectors that uniquely identify elements (use id, class, or tag combinations)
- For search boxes, look for input elements with type="text" or role="search"
- After typing in search, use press_enter action
- If you see relevant links, click them
- If goal is achieved, use goal_completed action
- Keep trying different approaches if stuck

Respond with ONLY the JSON, no other text.
"""
class BrowserAgent:
    def __init__(self, page, goal, max_steps=30):
        self.page = page
        self.goal = goal
        self.action_history = []
        self.max_steps = max_steps
        self.step_count = 0
    async def get_visible_elements(self):
        """Get visible elements from the page"""
        js_code = """
(() => {
  const isVisible = el => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return (
      rect.width > 0 &&
      rect.height > 0 &&
      rect.bottom >= 0 &&
      rect.right >= 0 &&
      rect.top <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.left <= (window.innerWidth || document.documentElement.clientWidth) &&
      style.visibility !== "hidden" &&
      style.display !== "none" &&
      style.opacity !== "0"
    );
  };
  const getInfo = el => {
    const info = {
      tag: el.tagName.toLowerCase(),
      id: el.id || undefined,
      classes: el.classList ? [...el.classList] : [],
    };
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      info.type = el.type || undefined;
      info.name = el.name || undefined;
      info.placeholder = el.placeholder || undefined;
      info.value = el.value || undefined;
    } else if (el.tagName === 'BUTTON') {
      info.text = el.innerText.trim() || el.value || undefined;
    } else if (el.tagName === 'A') {
      info.text = el.innerText.trim() || undefined;
      info.href = el.href || undefined;
    } else {
      const text = el.innerText?.trim();
      if (text && text.length < 200) info.text = text;
    }
    return info;
  };
  const elements = [...document.querySelectorAll('*')].filter(isVisible);
  const data = elements.map(getInfo).filter(obj =>
    Object.values(obj).some(v => v !== undefined && v !== '')
  );
  return JSON.stringify(data);
})();
"""
        result = await self.page.evaluate(js_code)
        return result
    
    def extract_json_from_response(self, response_text):
        """Extract JSON from response text, handling markdown code blocks"""
        try:
            return json.loads(response_text)
        except:
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            json_match = re.search(r'{.*}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError("No valid JSON found in response")
    async def decide_next_action(self):
        page_elements = await self.get_visible_elements()
        current_url = self.page.url
        elements_data = json.loads(page_elements)
        if len(elements_data) > 100:
            elements_data = elements_data[:100]
        prompt = ACTION_PROMPT.format(
            goal=self.goal,
            page_elements=json.dumps(elements_data, indent=2),
            current_url=current_url,
            action_history="\n".join(self.action_history[-5:]) if self.action_history else "None"
        )
        print(f"\n{'='*60}")
        print(f"Step {self.step_count + 1}: Thinking...")
        print(f"Current URL: {current_url}")   
        response = send_prompt(prompt)
        print(f"\nAI Response:\n{response}")
        try:
            action_data = self.extract_json_from_response(response)
            return action_data
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None
    async def execute_action(self, action_data):
        """Execute the decided action"""
        if not action_data or 'action' not in action_data:
            print("Invalid action data")
            return False
        reasoning = action_data.get('reasoning', 'No reasoning provided')
        action = action_data['action']
        action_type = action.get('type')
        print(f"\nReasoning: {reasoning}")
        print(f"Action: {action_type}")
        try:
            if action_type == 'click':
                selector = action.get('selector')
                print(f"Clicking: {selector}")
                await self.page.click(selector, timeout=5000)
                await asyncio.sleep(1)
                self.action_history.append(f"Clicked: {selector}")  
            elif action_type == 'type':
                selector = action.get('selector')
                value = action.get('value', '')
                print(f"Typing '{value}' into: {selector}")
                await self.page.fill(selector, value, timeout=5000)
                await asyncio.sleep(0.5)
                self.action_history.append(f"Typed '{value}' into: {selector}")   
            elif action_type == 'press_enter':
                selector = action.get('selector')
                print(f"Pressing Enter on: {selector}")
                await self.page.press(selector, 'Enter', timeout=5000)
                await asyncio.sleep(2)
                self.action_history.append(f"Pressed Enter on: {selector}")    
            elif action_type == 'scroll_down':
                print("Scrolling down")
                await self.page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
                await asyncio.sleep(1)
                self.action_history.append("Scrolled down")
            elif action_type == 'scroll_up':
                print("Scrolling up")
                await self.page.evaluate("window.scrollBy(0, -window.innerHeight * 0.8)")
                await asyncio.sleep(1)
                self.action_history.append("Scrolled up")  
            elif action_type == 'go_back':
                print("Going back")
                await self.page.go_back()
                await asyncio.sleep(2)
                self.action_history.append("Went back")
            elif action_type == 'wait':
                print("Waiting for page to load...")
                await asyncio.sleep(2)
                self.action_history.append("Waited")
            elif action_type == 'goal_completed':
                reason = action.get('reason', 'Goal completed')
                print(f"\n🎉 GOAL COMPLETED: {reason}")
                return True 
            else:
                print(f"Unknown action type: {action_type}")
                return False
            return False 
        except Exception as e:
            print(f"Error executing action: {e}")
            self.action_history.append(f"Failed: {action_type} - {str(e)}")
            return False
    async def run(self):
        """Run the autonomous agent"""
        print(f"\n🚀 Starting autonomous browser agent")
        print(f"Goal: {self.goal}")
        print(f"Max steps: {self.max_steps}")
        while self.step_count < self.max_steps:
            self.step_count += 1
            action_data = await self.decide_next_action()
            if not action_data:
                print("Failed to get valid action, retrying...")
                await asyncio.sleep(2)
                continue
            goal_completed = await self.execute_action(action_data)
            if goal_completed:
                print(f"\n✅ Goal achieved in {self.step_count} steps!")
                return True
            await asyncio.sleep(1)
        print(f"\n⚠️ Reached maximum steps ({self.max_steps}) without completing goal")
        return False
async def main():
    goal = input("Enter your goal (or press Enter for default): ").strip()
    if not goal:
        goal = "find shoes under 2000 pkr"
    print(f"\nGoal set: {goal}")
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="test",
            channel="chrome",
            headless=False,
            no_viewport=True,
        )
        page = browser.pages[0]
        await page.goto('https://www.google.com/')
        await asyncio.sleep(2)
        agent = BrowserAgent(page, goal, max_steps=30)
        success = await agent.run()
        print("\n" + "="*60)
        if success:
            print("✅ Task completed successfully!")
        else:
            print("⚠️ Task did not complete fully")
        print("="*60)
        input("\nPress Enter to close browser...")
        await browser.close()
if __name__ == "__main__":
    asyncio.run(main())
