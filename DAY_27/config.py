# config.py
import os
from dotenv import load_dotenv
import assemblyai as aai
import google.generativeai as genai
import logging

load_dotenv()

MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")  # ✅ NEW

if ASSEMBLYAI_API_KEY:
    aai.settings.api_key = ASSEMBLYAI_API_KEY
else:
    logging.warning("ASSEMBLYAI_API_KEY not found in .env file.")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logging.warning("GEMINI_API_KEY not found in .env file.")

if not MURF_API_KEY:
    logging.warning("MURF_API_KEY not found in .env file.")

if not SERPAPI_API_KEY:
    logging.warning("SERPAPI_API_KEY not found in .env file.")  # ✅ NEW
