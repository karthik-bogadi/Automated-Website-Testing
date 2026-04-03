# 🤖 AI Agent for Automated Website Testing

## 📌 Overview

This project is an AI-powered testing agent that converts natural language instructions into automated browser tests using Playwright.

## 🚀 Features

* Natural language test input
* Intelligent instruction parsing
* Automated Playwright execution
* Assertion validation (PASS/FAIL)
* Clean UI reporting

## 🧠 Architecture

User Input → LangGraph Agent → Parser → Playwright → Execution → Report

## 🛠️ Tech Stack

* Python
* Flask
* LangGraph
* Playwright
* Groq (LLM)
* HTML, CSS, JavaScript

## ⚙️ Setup Instructions

```bash
git clone <your-repo>
cd MILESTONE-2

python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt
playwright install

python app.py
```

## 💡 Example Input

"Open Google and search for AI"

## 📊 Output

* Step-by-step execution
* PASS/FAIL results
* Error messages (if any)

## 🔮 Future Enhancements

* Self-healing selectors
* Screenshot on failure
* Multi-browser support
* Dashboard analytics


👨‍💻 Author

Karthik Kumar

Infosys Springboard Internship Project👨‍💻 Author
