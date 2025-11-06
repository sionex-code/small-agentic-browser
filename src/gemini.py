import requests
import json

# Using the API key from your bash script
API_KEY = "" # add your api key here
MODEL_ID = "gemini-flash-lite-latest"
GENERATE_CONTENT_API = "streamGenerateContent"

def send_prompt(prompt):
    """
    Send a prompt to the Gemini API and return the response text.
    
    Args:
        prompt (str): The prompt to send to the Gemini API
    
    Returns:
        str: The text response from the API
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:{GENERATE_CONTENT_API}?key={API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "thinkingConfig": {
                "thinkingBudget": 0
            }
        }
    }
    
    try:
        # Note: We are NOT using stream=True, so requests buffers the whole response
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        response_text = ""
        
        # --- START OF FIX ---
        # The response.text is a single string containing a JSON array.
        # We need to parse it as one JSON object.
        try:
            # Parse the entire response as a list of chunks
            chunks = json.loads(response.text)
            
            # Iterate through the list of chunks
            for chunk in chunks:
                if 'candidates' in chunk and len(chunk['candidates']) > 0:
                    candidate = chunk['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        for part in candidate['content']['parts']:
                            if 'text' in part:
                                response_text += part['text']
                                
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON response.")
            print(f"Raw response: {response.text}")
            return "Error parsing response"
        # --- END OF FIX ---
            
        return response_text if response_text else "No response text found"
        
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        # Print response text if available, as it might contain error details
        if e.response is not None:
            print(f"Error response: {e.response.text}")
        return None

