# 🤖 small agentic browser - Autonomous Browser Agent (under 250 lines)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A minimalist, self-contained Python agent that uses LLMs to autonomously browse the web and achieve user-defined goals.

## ✨ Features

- **Goal-Driven**: Accepts natural language goals (e.g., "find shoes under 2000 pkr")
- **Smart Perception**: Extracts visible and interactive HTML elements
- **LLM Decision Making**: Uses structured prompts for intelligent action planning
- **Browser Automation**: Executes actions via Playwright (click, type, scroll)

## 🔄 How It Works

The agent operates in a continuous **Observe → Decide → Act** loop:

1. **👁️ Observe**: Extracts visible elements (inputs, buttons, links) and their attributes
2. **🧠 Decide**: Sends page state + goal to LLM, receives JSON action plan
3. **✋ Act**: Executes the action in browser using Playwright

This loop continues until the LLM determines the goal is achieved.

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Configured Gemini API environment

### Setup
```bash
# Install dependencies
pip install playwright patchright

# Install browser engine
playwright install chromium
```

## 🚀 Usage
```bash
python browser_agent.py
```

Enter your goal when prompted, or press Enter to use the default goal. A Chrome window will launch and execute actions autonomously.

## 📋 Example
```python
# Example goal
"Find running shoes under 2000 PKR on an e-commerce site"
```

The agent will:
- Navigate to the site
- Search for products
- Filter by price
- Report findings

## 🏗️ Architecture
```
User Goal → Observe Page → LLM Planning → Execute Action → Repeat
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## ⚠️ Disclaimer

This tool is for educational purposes. Ensure compliance with website terms of service when using automated browsing.

---

Made with ❤️ using Python & LLMs
