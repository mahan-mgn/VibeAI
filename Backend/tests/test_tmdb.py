"""
Tests for TMDB Service (requires valid TMDB_API_KEY in .env)
Run: pytest tests/test_tmdb.py -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from config.settings import settings


@pytest.mark.skipif(not settings.TMDB_API_KEY, reason="No TMDB_API_KEY set")
@pytest.mark.asyncio
async def test_discover_movies_returns_results():
    from services.tmdb_service import discover_movies
    results = await discover_movies(
        genre_ids=[35],        # comedy
        sort_by="popularity.desc",
        max_runtime=150,
    )
    assert len(results) > 0
    assert "title" in results[0] or "original_title" in results[0]


@pytest.mark.skipif(not settings.TMDB_API_KEY, reason="No TMDB_API_KEY set")
@pytest.mark.asyncio
async def test_genre_map_returns_dict():
    from services.tmdb_service import get_genre_map
    genre_map = await get_genre_map()
    assert isinstance(genre_map, dict)
    assert len(genre_map) > 0


@pytest.mark.skipif(not settings.TMDB_API_KEY, reason="No TMDB_API_KEY set")
@pytest.mark.asyncio
async def test_movie_recommender_full_flow():
    from recommender.movie import recommend
    movies = await recommend(mood="tired", energy="low", time_period="night")
    assert len(movies) > 0
    first = movies[0]
    assert "title" in first
    assert "reasoning" in first
    assert "poster_url" in first