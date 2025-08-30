# 🎙️ CORA – Conversational Voice Agent

Welcome to the repository for **CORA (Conversational Responsive Agent)**, built as part of the **30 Days of Voice Agents Challenge**.  
CORA started as a simple FastAPI echo bot and evolved into a **fully deployed, voice-first AI assistant** capable of contextual conversations and natural-sounding responses.

---

## 🤖 About CORA

CORA is a **voice-driven conversational AI** that listens, understands, and responds naturally. It can:  

- Remember **conversation history** for context-aware replies  
- Respond with **human-like voice** using TTS  
- Fetch **live information from the web** when needed  
- Provide **interactive, voice-to-voice chat** through a simple web interface  

This repository documents the full journey of building CORA, day by day.

---

## ✨ Features

- **🎤 Voice-to-Voice Chat** – Talk naturally and hear AI responses in real-time  
- **🧠 Conversational Memory** – Maintains context across multiple turns  
- **⚡ End-to-End AI Pipeline** – STT → LLM → TTS fully integrated  
- **💻 Minimal, Intuitive UI** – Single-button interface with live feedback  
- **🛡️ Robust Error Handling** – Fallback audio responses for API failures  
- **☁️ Cloud Deployment** – Accessible online from anywhere

---

## 🛠️ Tech Stack

**Backend**  
- FastAPI – API server  
- Uvicorn – ASGI server  
- WebSockets – Real-time streaming  
- python-dotenv – Environment variable management  

**Frontend**  
- HTML, CSS, JavaScript – Core UI  
- Bootstrap – Responsive styling  
- MediaRecorder API – Capture microphone input  
- WebSocket API – Audio streaming  

**AI & Voice APIs**  
- AssemblyAI – Real-time Speech-to-Text  
- Google Gemini – Conversational LLM  
- Murf AI – Text-to-Speech  
- SerpAPI – Web search integration  

**Deployment**  
- Render.com – Cloud hosting  

---

## ⚙️ How CORA Works

1. User speaks into the microphone 🎤  
2. Audio is streamed to FastAPI via WebSocket  
3. AssemblyAI transcribes speech to text  
4. Text + chat history sent to Gemini LLM → generates response  
5. Response sent to Murf AI → converts text to speech  
6. Audio returned to browser and played automatically  

---

## 🚀 Getting Started

### 🔗 Live Demo
Try CORA here: [https://marvis-voice-agent-l7da.onrender.com/](https://marvis-voice-agent-l7da.onrender.com/)  

1. Click the **settings icon** to enter your API keys  
2. Grant microphone access  
3. Start chatting 🎙️  

### 💻 Run Locally

**Requirements**  
- Python 3.8+  
- API keys for Murf AI, AssemblyAI, Gemini, SerpAPI  

**Steps**  
```bash
# Clone the repository
git clone https://github.com/your-username/cora-voice-agent.git
cd cora-voice-agent/day-29

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
echo 'MURF_API_KEY=your_key
ASSEMBLYAI_API_KEY=your_key
GEMINI_API_KEY=your_key
SERP_API_KEY=your_key' > .env

# Start FastAPI server
uvicorn main:app --reload


CORA/
├── main.py          # FastAPI entrypoint
├── services/        # AI integrations
│   ├── llm.py       # Gemini LLM logic
│   ├── stt.py       # Speech-to-Text
│   └── tts.py       # Text-to-Speech
├── schemas.py       # Data models
├── templates/       
│   └── index.html   # Web UI
├── static/          
│   ├── script.js    # Frontend logic
│   └── style.css    # Styling
├── requirements.txt # Dependencies
└── .env             # API keys


## 🗓️ Journey: Day 1 to Day 29

Day 01–05: FastAPI basics + echo bot

Day 06–09: Added STT & TTS → full voice-to-voice loop

Day 10–15: Memory, persona, modular structure

Day 16–20: Real-time streaming + WebSockets

Day 21–23: Web search integration & function calling

Day 24–26: Polished UI + named the agent CORA

Day 27–28: Settings panel + cloud deployment

Day 29: Final documentation & cleanup

## 🙌 Credits

Thanks to 30 Days of Voice Agents Challenge, AssemblyAI, Murf AI, Google Gemini, and SerpAPI for making this project possible.
