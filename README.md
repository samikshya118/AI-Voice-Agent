# 🎯 30 Days of AI Voice Agents Challenge

Welcome to my repository for the **30 Days of AI Voice Agents Challenge**!  
This project documents my journey in building a sophisticated, **voice-activated conversational AI** from the ground up.  
Over the course of the challenge, a simple webpage evolves into a **fully interactive AI voice agent** capable of holding context-aware conversations.

---

## 🤖 About the Project
This is a hands-on project to build a **voice-based conversational AI** using modern web technologies and powerful AI APIs.  
You can engage in continuous, **voice-to-voice conversations** with an AI powered by Google's Generative AI (Gemini) LLM.  
The agent remembers the context of the conversation, enabling **natural follow-up questions** and a more human-like interaction.

The repository is organized **day-by-day**, with each folder representing a step in the development process — from setting up the server to creating a fully functional conversation loop with memory.

---

## 🔑 Key Features
- **🎤 Voice-to-Voice Interaction** – Speak to the agent and receive a spoken response for seamless conversations.
- **🧠 Contextual Conversations** – Maintains chat history per session for natural, follow-up interactions.
- **🔗 End-to-End AI Pipeline** – Speech-to-Text → LLM → Text-to-Speech, all fully integrated.
- **💻 Modern UI** – Minimal, intuitive interface with single-button control and visual feedback for states like *ready*, *recording*, and *thinking*.
- **🛡️ Robust Error Handling** – Fallback audio responses if an API call fails, ensuring smooth user experience.

---

## 🛠 Tech Stack

### **Backend**
- **FastAPI** – High-performance Python API framework
- **Uvicorn** – ASGI server for running FastAPI
- **Python-Dotenv** – Manage environment variables

### **Frontend**
- **HTML, CSS, JavaScript** – Structure, styling, and interactivity
- **Bootstrap** – Responsive, clean UI components
- **MediaRecorder API** – Capture audio directly from the browser

### **AI & Voice APIs**
- **Murf AI** – Natural-sounding Text-to-Speech
- **AssemblyAI** – Fast and accurate Speech-to-Text
- **Google Gemini** – Large Language Model for conversational intelligence

---

## 🗂 Architecture

The application follows a **client-server** architecture.  
The **frontend** handles audio capture and UI, while the **backend** orchestrates transcription, AI processing, and speech synthesis.

**Conversation Flow:**
1. **Client** captures voice using the MediaRecorder API.
2. **FastAPI Server** receives and processes audio.
3. Audio is sent to **AssemblyAI** for transcription.
4. Server retrieves chat history and sends transcript to **Google Gemini**.
5. Gemini generates a conversational response.
6. Server sends the AI’s text to **Murf AI** for Text-to-Speech.
7. The client plays back the generated voice response.

---

## 🚀 Getting Started

### **Prerequisites**
- Python 3.8+
- API Keys for:
  - **Murf AI**
  - **AssemblyAI**
  - **Google Gemini**

---

## 🚀 Getting Started

Follow these steps to set up and run the AI Voice Agent on your local machine.

### **Prerequisites**
- Python 3.8+
- API Keys for:
  - Murf AI
  - AssemblyAI
  - Google Gemini

### **Installation & Running**
```bash
# 1. Clone the repository
git clone https://github.com/samikhya118/AI-Voice-Agent.git
cd AI-Voice-Agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create and configure environment variables
echo "ASSEMBLYAI_API_KEY=your_key_here" >> .env
echo "MURF_API_KEY=your_key_here" >> .env
echo "GOOGLE_API_KEY=your_key_here" >> .env

# 4. Run the FastAPI server
uvicorn main:app --reload

# 5. Open the frontend
# Simply open index.html in your browser to interact with the AI Voice Agent
