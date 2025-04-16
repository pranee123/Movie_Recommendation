import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests

# Ensure set_page_config is at the top of the script
st.set_page_config(page_title="🤖 ChatRobo - Movie Recommender", page_icon="🎬", layout="wide")

# ---- Load API keys ----
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not GEMINI_API_KEY or not TMDB_API_KEY:
    st.error("⚠️ API Keys are missing! Set them in the `.env` file.")
    st.stop()

# ---- Initialize Gemini Configuration ----
genai.configure(api_key=GEMINI_API_KEY)

# ---- Define convert_history_for_gemini Function ----
def convert_history_for_gemini(chat_history):
    """Convert chat history into the format required by Gemini AI."""
    formatted_history = []
    for message in chat_history:
        content = {
            "role": message["role"],  # Keep the role ('user' or 'assistant')
            "parts": [{"text": message["parts"][0]["text"]}]  # Wrap the text in 'parts' list
        }
        formatted_history.append(content)
    return formatted_history

# ---- Initialize chat history ----
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---- Movie Recommendation UI ----
st.markdown("""
    <style>
        .stTextInput>div>input {
            width: 350px;  /* Reduce width of movie input */
        }
        .stButton>button {
            background-color: #FF5733; /* Change button color */
            color: white;
            font-weight: bold;
        }
        .stImage>img {
            border-radius: 10px;
        }
        .chat-box {
            background-color: #f8f8f8;
            border-radius: 10px;
            padding: 20px;
        }
        .chat-box .user {
            background-color: #ffcdd2;  /* Light Red */
            padding: 12px 15px;
            border-radius: 15px;
            margin-bottom: 5px;
            color: #b71c1c;
            font-size: 16px;
        }
        .chat-box .assistant {
            background-color: #f8bbd0;  /* Light Pink */
            padding: 12px 15px;
            border-radius: 15px;
            margin-bottom: 5px;
            color: #880e4f;
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)


st.title("🎬 Movie Recommender System with ChatRobo 🤖")

# Movie search input
movie_input = st.text_input("Enter a Movie Title, Genre, or Keyword 👇")

# ---- TMDB API Function ----
def fetch_movie_details(movie_name):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    response = requests.get(search_url).json()

    if "results" not in response or not response["results"]:
        return None

    movie = response["results"][0]
    movie_id = movie["id"]

    details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,recommendations"
    movie_data = requests.get(details_url).json()

    poster_url = f"https://image.tmdb.org/t/p/w300{movie.get('poster_path', '')}" if movie.get("poster_path") else "https://via.placeholder.com/300x450?text=No+Poster"
    story = movie_data.get("overview", "No description available.")
    release_date = movie_data.get("release_date", "")
    release_year = release_date[:4] if release_date else "Unknown"

    director = "Unknown"
    if "credits" in movie_data and "crew" in movie_data["credits"]:
        director_list = [crew["name"] for crew in movie_data["credits"]["crew"] if crew.get("job") == "Director"]
        if director_list:
            director = director_list[0]

    cast = [
        {"character": c.get("character", "Unknown"), "real_name": c.get("name", "Unknown")}
        for c in movie_data.get("credits", {}).get("cast", [])[:5]
    ]

    similar_movies = [rec.get("title", "Unknown") for rec in movie_data.get("recommendations", {}).get("results", [])[:5]]

    return {
        "title": movie.get("title", "Unknown"),
        "story": story,
        "cast": cast,
        "poster": poster_url,
        "similar": similar_movies,
        "release_year": release_year,
        "director": director
    }

# ---- Gemini AI Description Generator ----
def generate_movie_description(movie_name, story, cast, similar_movies):
    prompt = f"""Provide a detailed description of the movie "{movie_name}". 
    - **Story Summary**: {story}
    - **Main Characters & Actors**: {', '.join([f"{c['character']} (played by {c['real_name']})" for c in cast])}
    - **Similar Movies**: {', '.join(similar_movies)}
    """

    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
    response = model.generate_content(prompt)

    return response.text if response else "No additional details available."

# ---- Show Movie Details ----
if movie_input:
    movie_details = fetch_movie_details(movie_input)

    if movie_details:
        st.markdown("""
        <div style="background-color:#1e1e1e; padding: 20px; border-radius: 10px; color: #f5f5f5;">
        """, unsafe_allow_html=True)

        st.subheader(f"🎬 {movie_details['title']}")
        st.image(movie_details["poster"], caption=movie_details["title"], width=500)

        st.write(f"📅 **Release Year:** {movie_details['release_year']}")
        st.write(f"🎬 **Director:** {movie_details['director']}")
        st.write("📖 **Story:**", movie_details["story"])

        st.write("🎭 **Main Characters:**")
        for c in movie_details["cast"]:
            st.write(f"- {c['character']} (Played by {c['real_name']})")

        st.write("🔗 **Similar Movies:**", ", ".join(movie_details["similar"]))

        st.markdown("</div>", unsafe_allow_html=True)

# ---- Chatbot UI ----
col1, col2 = st.columns([4, 1])

# --- Chat Title in Large Font --- 
with col1:
    st.markdown("<h1 style='text-align: center;'>🤖 ChatRobo - Your Movie Buddy 🎬</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: gray;'>Ask me anything about movies or get movie recommendations!</p>", unsafe_allow_html=True)

# --- Chatbot Message UI ---
with col2:
    user_input = st.text_input("🗨️ Type your message here...", key="user_input")

# --- On User Message ---
if user_input:
    st.session_state.chat_history.append({
        "role": "user",
        "parts": [{"text": user_input}]
    })

    # Initialize Gemini model
    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
    formatted_history = convert_history_for_gemini(st.session_state.chat_history)

    # Start chat session
    chat = model.start_chat(history=formatted_history)

    # Model Response
    response = chat.send_message(user_input)

    st.session_state.chat_history.append({
        "role": "assistant",
        "parts": [{"text": response.text}]
    })

# --- Display Chat History ---
with col1:
    for msg in st.session_state.chat_history:
        role = "🧑 You" if msg["role"] == "user" else "🤖 ChatRobo"
        text = msg["parts"][0]["text"]
        message_class = "user" if msg["role"] == "user" else "assistant"
        st.markdown(f'<div class="chat-box"><div class="{message_class}"><strong>{role}:</strong> {text}</div></div>', unsafe_allow_html=True)

# --- Floating Robot Icon ---
st.markdown("""
    <div style="position: fixed; bottom: 20px; right: 30px; background-color: #FFFFFF; border-radius: 50%; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
        <img src="https://img.icons8.com/ios-filled/50/000000/robot.png" alt="robot" />
    </div>
""", unsafe_allow_html=True)
