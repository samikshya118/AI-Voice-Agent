# 🎙️ AI Voice Agent – Day 14 Refactored

This project is part of my **30 Days of AI Voice Agents** challenge.  
On **Day 14**, the focus was on **refactoring** the existing conversational bot code to make it more readable, maintainable, and production-ready.

## 🚀 What's New in Day 14
- 🛠 **Code Refactoring**
  - Created **`/services`** folder to store Speech-to-Text (STT), Text-to-Speech (TTS), and LLM logic.
  - Added **Pydantic schemas** in a `/schemas` folder for structured API requests and responses.
  - Removed unused imports, variables, and functions.
  - Introduced **logging** for better debugging and tracking.
- 🎤 **Working conversational bot**
  - Listens to voice input.
  - Transcribes speech to text.
  - Generates AI responses using LLM.
  - Converts AI response to audio and plays it back.

## 🗂 Project Structure
📂 project-root
├── 📂 static/ # Frontend assets (JS, CSS)
├── 📂 templates/ # HTML files
├── 📂 services/ # STT, TTS, LLM service logic
├── 📂 schemas/ # Request & response Pydantic models
├── main.py # FastAPI app entry point
├── requirements.txt # Dependencies
└── README.md # Documentation



## ⚙️ Tech Stack
- **Frontend:** HTML, CSS, JavaScript (MediaRecorder API)
- **Backend:** FastAPI (Python)
- **APIs Used:**
  - AssemblyAI – Speech-to-Text
  - Murf AI – Text-to-Speech
  - OpenAI – LLM

## 📌 How It Works
1. **Record** voice in the browser using the Record button.
2. Backend:
   - Converts audio to text (STT).
   - Sends text to LLM for a response.
   - Converts LLM response back to speech (TTS).
3. Browser plays back the AI’s reply and shows it in chat format.

## 🖥️ Setup & Run Locally
```bash
# Clone the repo
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# Install dependencies
pip install -r requirements.txt

# Add API keys to .env
ASSEMBLYAI_API_KEY=your_key
MURF_API_KEY=your_key
OPENAI_API_KEY=your_key

# Run the app
uvicorn main:app --reload
