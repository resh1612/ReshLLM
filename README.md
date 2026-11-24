# ReshLLM — Professional Local LLM Chatbot

A polished, modern LLM chatbot web application powered by your local Ollama `qwen2.5:1.5b` model and DuckDuckGo Search (DDGS). Features a ChatGPT-like user experience with real-time token streaming, persistent conversation history, deterministic date/time handling, and smart live web search.

---

## 🌟 Key Features

- **ChatGPT-like UI/UX**: Clean dark/light theme, modern typography, right-aligned user bubbles, syntax-highlighted code blocks with one-click copy, and collapsible web sources.
- **Local AI Powered**: Seamlessly runs on your local Ollama instance with `qwen2.5:1.5b` without relying on paid external APIs.
- **Smart Web & News Search**: Automatically detects when fresh news or current affairs are needed, queries DDGS in real-time, cites evidence, and displays source links.
- **Instant Deterministic Queries**: Answers date and time queries instantaneously using Python `datetime`.
- **Persistent Multi-Chat History**: Creates and saves individual chat sessions to disk in `chat_history/` as JSON files, allowing sessions to persist across restarts without overwriting each other.
- **Full CLI Backward Compatibility**: The original terminal assistant remains 100% functional via `python assistant.py`.
- **Hardware Optimized**: Lightweight streaming pipeline designed to run smoothly on laptops with Intel i5 processors and 8 GB RAM.

---

## 📂 Project Structure

```text
MyPythonAI/
├── app.py                     # Streamlit web application frontend
├── assistant.py               # Core AI router, search logic & CLI entry point
├── chat_storage.py            # Local JSON conversation persistence manager
├── chat_history/              # Persisted chat session files (*.json)
├── assets/
│   └── style.css              # Custom ChatGPT-style CSS styling
├── requirements.txt           # Minimal project dependencies
└── README.md                  # Project documentation and launch instructions
```

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure Ollama is installed and running with your existing model:
```powershell
ollama list
```
You should see `qwen2.5:1.5b` listed.

### 2. Install Dependencies
If not already installed:
```powershell
pip install -r requirements.txt
```

### 3. Launch the Web Application
Run the Streamlit application:
```powershell
streamlit run app.py
```
Streamlit will automatically open your default browser at `http://localhost:8501`.

### 4. Launch the CLI Assistant (Optional)
To use the original terminal assistant:
```powershell
python assistant.py
```

---

## ⚙️ Configuration & Settings

Inside the Web App sidebar:
- **➕ New Chat**: Starts a fresh conversation with suggested starter prompts.
- **Conversations List**: Displays all past conversations with custom titles; click any conversation to resume, or click the 🗑️ icon to delete.
- **🧹 Clear Messages**: Clears the conversation history of the active session.
- **Temperature Slider**: Adjust response creativity (default `0.2` for concise, deterministic answers).
- **Max Response Tokens**: Set the maximum tokens returned by Ollama (default `700`).
- **Web Search Mode**:
  - `Auto-Detect (Smart DDGS)`: Searches only when questions involve recent events, news, or current year.
  - `Always Search Web`: Forces web search on every query.
  - `Offline (Local AI Only)`: Disables internet search entirely.

