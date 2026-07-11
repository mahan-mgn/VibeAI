import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))


class Settings:
    # API Keys
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./vibeai.db")

    # TMDB
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE: str = "https://image.tmdb.org/t/p/w500"
    TMDB_LANGUAGE_PRIMARY: str = "fa-IR"
    TMDB_LANGUAGE_FALLBACK: str = "en-US"

    # Engine
    CONFIDENCE_THRESHOLD: float = 0.40
    MAX_MOVIE_RESULTS: int = 4
    MAX_MUSIC_RESULTS: int = 4

    # App
    APP_TITLE: str = "VibeAI"
    APP_VERSION: str = "1.0.0-mvp"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()