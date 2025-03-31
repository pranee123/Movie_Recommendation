import streamlit as st
import google.generativeai as genai
import requests
import os
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

# Fetch API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Validate API keys
if not GEMINI_API_KEY or not TMDB_API_KEY:
    st.error("⚠️ API Keys are missing! Set them in the `.env` file.")
    st.stop()

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Streamlit UI
st.title("🎬 Movie Recommender System")
movie_input = st.text_input("Enter a Movie Title, Genre, or Keyword 👇")

# Function to get movie details from TMDB API
def fetch_movie_details(movie_name):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    response = requests.get(search_url).json()
    
    if "results" not in response or not response["results"]:
        return None
    
    movie = response["results"][0]  # Get the first search result
    movie_id = movie["id"]
    
    # Get full movie details
    details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,recommendations"
    movie_data = requests.get(details_url).json()

    # Extract details with error handling
    poster_url = f"https://image.tmdb.org/t/p/w300{movie.get('poster_path', '')}" if movie.get("poster_path") else None
    story = movie_data.get("overview", "No description available.")

    # Handle missing release date
    release_date = movie_data.get("release_date", "")
    release_year = release_date[:4] if release_date else "Unknown"

    # Get director from the crew list
    director = "Unknown"
    if "credits" in movie_data and "crew" in movie_data["credits"]:
        director_list = [crew["name"] for crew in movie_data["credits"]["crew"] if crew.get("job") == "Director"]
        if director_list:
            director = director_list[0]

    # Get top 5 cast members
    cast = [
        {"character": c.get("character", "Unknown"), "real_name": c.get("name", "Unknown")}
        for c in movie_data.get("credits", {}).get("cast", [])[:5]
    ]

    # Get top 5 similar movies
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

# Function to generate detailed movie info using Gemini AI
def generate_movie_description(movie_name, story, cast, similar_movies):
    prompt = f"""Provide a detailed description of the movie "{movie_name}". 
    - **Story Summary**: {story}
    - **Main Characters & Actors**: {', '.join([f"{c['character']} (played by {c['real_name']})" for c in cast])}
    - **Similar Movies**: {', '.join(similar_movies)}
    """
    
    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
    response = model.generate_content(prompt)
    
    return response.text if response else "No additional details available."

# Main logic
if movie_input:
    movie_details = fetch_movie_details(movie_input)

    if movie_details:
        st.subheader(f"🎬 {movie_details['title']}")
        if movie_details["poster"]:
            st.image(movie_details["poster"], caption=movie_details["title"], width=500)

        st.write(f"📅 **Release Year:** {movie_details['release_year']}")
        st.write(f"🎬 **Director:** {movie_details['director']}")
        st.write("📖 **Story:**", movie_details["story"])
        
        st.write("🎭 **Main Characters:**")
        for c in movie_details["cast"]:
            st.write(f"- {c['character']} (Played by {c['real_name']})")

        st.write("🔗 **Similar Movies:**", ", ".join(movie_details["similar"]))

        # Generate additional description using Gemini AI
        st.subheader("📜 More Details (AI Generated)")
        movie_description = generate_movie_description(
            movie_details["title"], 
            movie_details["story"], 
            movie_details["cast"], 
            movie_details["similar"]
        )
        st.write(movie_description)
    else:
        st.error("❌ Movie not found. Try another title!")
