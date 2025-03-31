import streamlit as st
import google.generativeai as genai
import toml

# Manually load secrets from secrets.toml
secrets = toml.load(".streamlit/secrets.toml")

# Extract API keys
GEMINI_API_KEY = secrets.get("GEMINI_API_KEY")
TMDB_API_KEY = secrets.get("TMDB_API_KEY")

# Validate API keys
if not GEMINI_API_KEY or not TMDB_API_KEY:
    st.error("⚠️ API Keys are missing! Please check your secrets file.")
    st.stop()

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)