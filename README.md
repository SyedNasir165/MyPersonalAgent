# 🤖 My Personal AI Agent

<p align="center">
  <strong>A Local AI Agent Built from Scratch with Python & Ollama</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Ollama-Local%20LLM-black?style=for-the-badge" alt="Ollama">
  <img src="https://img.shields.io/badge/Phi--3%20Mini-Local%20AI-7B68EE?style=for-the-badge" alt="Phi-3 Mini">
  <img src="https://img.shields.io/badge/Status-Active%20Development-F59E0B?style=for-the-badge" alt="Status">
</p>

A locally running personal AI assistant developed to explore how AI agents work — combining a local LLM with practical tools, memory, web search, Python execution, and file operations.

---

## ✨ Features

| Feature | Status |
|---|---|
| 💬 Normal AI Conversation | ✅ |
| 🧮 Calculator | ✅ |
| 🕐 Date & Time | ✅ |
| 🌐 Web Search | ✅ |
| 🐍 Python Execution | ✅ |
| 📄 File Operations | ✅ |
| 🧠 Short-Term Memory | ✅ |
| 💾 Long-Term Memory | ✅ |
| 🤖 Tool Selection | ✅ |
| 🔄 Continuous Conversation | ✅ |
| 🧩 Multi-Step Autonomous Tasks | ✅ |
| 🌐 Web Interface (Streamlit) | ✅ |
| 💻 IDE Integration | 🚧 |

---

## 🧠 How It Works

```text
User
  ↓
Python Agent
  ↓
Understand / Route Request
  ↓
Select Tool
  ↓
┌────────────┬────────────┬────────────┐
│ Calculator │  Web Search│   Memory   │
├────────────┼────────────┼────────────┤
│ Date/Time  │   Python   │   Files    │
└────────────┴────────────┴────────────┘
  ↓
Ollama / Phi-3 Mini
  ↓
Final Response
```

The project combines deterministic Python tools with an LLM so that tasks such as calculations and date/time are handled reliably, while normal questions and tool decisions can use the local model.

---

## 🛠️ Tech Stack

**Core:** Python, Ollama, Phi-3 Mini, JSON

**Libraries:**
- `ollama`
- `requests`
- `beautifulsoup4`
- Python standard libraries including `ast`, `datetime`, `json`, `re`, and `operator`

---

## 🔧 Current Capabilities

### 🧮 Calculator
Supports common mathematical operations including:

`+` `-` `*` `/` `%` `**` `//`

Uses Python's `ast` module for safer expression handling.

### 🕐 Date & Time
Gets the current date and time directly from Python instead of relying on the model's knowledge.

### 🌐 Web Search
Uses `Requests` and `BeautifulSoup` to search the web and provide information through the local AI.

### 🐍 Python Execution
Runs Python code locally, including multi-line programs and indentation through the dedicated Python workspace.

### 🧠 Memory
- Short-term conversation memory
- Persistent long-term memory stored in `memory.json`

### 📄 File Operations
Supports local file creation, reading, and appending.

---

## 📁 Project Structure

```text
MyPersonalAgent/
│
├── agent.py
├── app.py
├── memory.py
├── memory.json
├── file_tools.py
├── python_tool.py
├── requirements.txt
│
└── python_workspace/
    └── agent_script.py
```

| File | Purpose |
|---|---|
| `agent.py` | Agent logic, tool routing, task planning & execution (CLI + reusable API) |
| `app.py` | Streamlit web UI — presentation layer only, calls `agent.handle_message()` |
| `memory.py` | Persistent memory |
| `memory.json` | Long-term stored information |
| `file_tools.py` | Local file operations |
| `python_tool.py` | Python execution |
| `requirements.txt` | Python dependencies |
| `python_workspace/` | Python execution workspace |

---

## ▶️ Run Locally

### 1. Open Command Prompt / PowerShell

```cmd
D:
cd MyPersonalAgent
```

### 2. Make sure Ollama and the model are available

```text
phi3:mini
```

### 3. Start the agent

```cmd
python agent.py
```

### 4. Example requests

```text
hello
88+7
what time is it
who is Virat Kohli
run python: print(10+10)
what is my favorite language
```

Use `exit` or `quit` to close the agent.

### 5. Or run the Streamlit web UI

```cmd
pip install -r requirements.txt
streamlit run app.py
```

The web UI is a thin presentation layer over `agent.py` — all tool logic, planning, and execution stays in the agent module. It requires the same local Ollama + `phi3:mini` setup as the CLI.

**Deployment note:** this currently only works where a local Ollama server is reachable (e.g. your own machine or a VM you control). Hosted platforms like Streamlit Community Cloud have no local Ollama instance, so the agent won't work there out of the box. `agent.ask_ai()` is the single point where all LLM calls go through — swapping it for a hosted LLM API is the only change needed to make the UI deployable to a public host.

---

## 🗺️ Development Progress

### ✅ Completed

- Agent fundamentals
- Ollama and local LLM integration
- Calculator
- Date & Time
- Web Search
- Tool-based architecture
- Python execution
- Multi-line Python execution
- File operations
- Short-term memory
- Long-term memory
- Continuous conversation
- Basic AI tool selection
- Multi-step task planning (Phase 14.1)
- Sequential task execution (Phase 14.2)
- Passing results between steps (Phase 14.3)
- Error recovery in task plans (Phase 14.4)
- Final summarized agent response (Phase 14.5)
- Streamlit web UI

### 🚧 Planned

- Advanced intent detection
- Improved memory retrieval
- VS Code / IDE integration
- Stronger security and permissions
- Optional hosted-LLM backend for cloud deployment

---

## 🎯 Vision

The project is evolving from a simple local chatbot into a capable personal AI agent:

```text
Local Chatbot
     ↓
Tool-Using Assistant
     ↓
Memory-Based Assistant
     ↓
Multi-Step AI Agent
     ↓
Local Personal AI
     ↓
Web + IDE Integrated AI
```

The long-term goal is an agent that can understand a request, select the appropriate tools, execute tasks locally, use the results, and provide a final response.

---

## 📊 Status

**Current Stage:** Phase 14 (14.1–14.5 complete) + Streamlit Web UI  
**Status:** 🚧 Active Development  
**Execution:** Local Computer  
**LLM Runtime:** Ollama  
**Model:** Phi-3 Mini

---

## 👨‍💻 Developer

### Nasir Syed

**Final Year Student | AI/ML | Generative AI | Python | Software Development**

**Interests:** Artificial Intelligence, Machine Learning, Generative AI, AI Agents, Python, and Software Engineering.

**GitHub:** [@SyedNasir165](https://github.com/SyedNasir165)

---

<p align="center">
  <strong>Built locally. Learned from scratch. Evolving into a Personal AI Agent. 🚀</strong>
</p>
