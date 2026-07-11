"""
TMDB Service
Handles all communication with The Movie Database API.
fa-IR → en-US fallback built in.
"""
import aiohttp
from config.settings import settings


async def discover_movies(
    genre_ids: list[int],
    sort_by: str,
    max_runtime: int,
    min_votes: int = 100,
    min_rating: float = 6.0,
    page: int = 1,
) -> list[dict]:
    """
    Query TMDB /discover/movie.
    Returns raw TMDB result items with Persian data when available.
    """
    params = {
        "api_key":           settings.TMDB_API_KEY,
        "with_genres":       ",".join(str(g) for g in genre_ids[:2]),
        "sort_by":           sort_by,
        "vote_count.gte":    min_votes,
        "vote_average.gte":  min_rating,
        "with_runtime.lte":  max_runtime,
        "page":              page,
        "language":          settings.TMDB_LANGUAGE_PRIMARY,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{settings.TMDB_BASE_URL}/discover/movie", params=params
        ) as resp:
            data = await resp.json()

        results = data.get("results", [])

        # If none have a Persian overview, retry in English
        if results and not any(r.get("overview") for r in results):
            params["language"] = settings.TMDB_LANGUAGE_FALLBACK
            async with session.get(
                f"{settings.TMDB_BASE_URL}/discover/movie", params=params
            ) as resp:
                data = await resp.json()
            results = data.get("results", [])

    return results


async def get_genre_map() -> dict[int, str]:
    """Return {genre_id: genre_name} in Persian."""
    params = {
        "api_key":  settings.TMDB_API_KEY,
        "language": settings.TMDB_LANGUAGE_PRIMARY,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{settings.TMDB_BASE_URL}/genre/movie/list", params=params
        ) as resp:
            data = await resp.json()
    return {g["id"]: g["name"] for g in data.get("genres", [])}


def poster_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"{settings.TMDB_IMAGE_BASE}{path}"