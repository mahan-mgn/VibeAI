"""
YouTube Service
Builds YouTube search URLs — no API key required.
"""
import urllib.parse


def search_url(title: str, artist: str) -> str:
    """Return a YouTube search URL for the given track."""
    query = f"{title} {artist}"
    return f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"