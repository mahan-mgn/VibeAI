"""
VibeAI - Movie Recommendation Engine
======================================

پیشنهاد فیلم بر اساس Mood/Energy/Activity کاربر، با استفاده از TMDB API.

تنوع: هر درخواست یک page تصادفی (1-4) از TMDB انتخاب می‌کند و
سپس از نمونه‌برداری وزن‌دار برای انتخاب top_n فیلم استفاده می‌شود.
این تضمین می‌کند که دو درخواست یکسان پشت سر هم، لیست‌های متفاوت می‌دهند.
"""

import os
import random
from typing import Dict, List, Optional

import requests

from cache import cache
from database import db
from recommender import personalization
from recommender.ranking import (
    calculate_final_score,
    energy_match_score,
    genre_match_score,
    weighted_sample,
)


TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

TOP_N_MOVIES = 5

# تعداد صفحات TMDB که برای تنوع به‌صورت تصادفی انتخاب می‌شود
TMDB_PAGE_POOL = 4

# نگاشت mood به ژانرهای TMDB
MOOD_GENRE_MAPPING = {
    "tired": ["Comedy", "Family", "Drama"],
    "stressed": ["Family", "Adventure"],
    "happy": ["Comedy", "Adventure"],
    "excited": ["Action", "Science Fiction"],
    "calm": ["Documentary", "Drama"],
    "anxious": ["Family"],
    "sad": ["Family"],
    "bored": ["Action", "Comedy"],
    "neutral": ["Comedy", "Drama"],
}

# نگاشت نام ژانر به genre_id در TMDB
TMDB_GENRE_IDS = {
    "Action": 28,
    "Adventure": 12,
    "Animation": 16,
    "Comedy": 35,
    "Crime": 80,
    "Documentary": 99,
    "Drama": 18,
    "Family": 10751,
    "Fantasy": 14,
    "History": 36,
    "Horror": 27,
    "Music": 10402,
    "Mystery": 9648,
    "Romance": 10749,
    "Science Fiction": 878,
    "TV Movie": 10770,
    "Thriller": 53,
    "War": 10752,
    "Western": 37,
}

TMDB_ID_TO_GENRE = {v: k for k, v in TMDB_GENRE_IDS.items()}


# ----------------------------------------------------------------------
# Mock Data
# ----------------------------------------------------------------------
MOCK_MOVIES = [
    {
        "title": "زوتوپیا",
        "genres": ["Animation", "Comedy", "Family", "Adventure"],
        "rating": 8.0,
        "overview": "یک کارآگاه خرگوش و یک روباه کلاهبردار باید با هم همکاری کنند تا یک توطئه را کشف کنند.",
        "poster_path": None,
    },
    {
        "title": "زندگی زیباست",
        "genres": ["Comedy", "Drama", "Family"],
        "rating": 8.6,
        "overview": "یک پدر با استفاده از تخیل و شوخ‌طبعی، فرزندش را در شرایط سخت دلگرم نگه می‌دارد.",
        "poster_path": None,
    },
    {
        "title": "اینتراستلار",
        "genres": ["Adventure", "Drama", "Science Fiction"],
        "rating": 8.6,
        "overview": "گروهی از فضانوردان برای یافتن سیاره‌ای جدید برای بقای بشریت سفر می‌کنند.",
        "poster_path": None,
    },
    {
        "title": "کوکو",
        "genres": ["Animation", "Family", "Comedy", "Adventure"],
        "rating": 8.4,
        "overview": "پسری به دنیای مردگان سفر می‌کند تا رازهای خانوادگی خود را کشف کند.",
        "poster_path": None,
    },
    {
        "title": "پلنگ صورتی",
        "genres": ["Comedy", "Family"],
        "rating": 6.8,
        "overview": "یک کارآگاه ناشی به دنبال یافتن یک الماس دزدیده‌شده است.",
        "poster_path": None,
    },
    {
        "title": "مأموریت غیرممکن",
        "genres": ["Action", "Adventure", "Thriller"],
        "rating": 7.4,
        "overview": "یک عامل مخفی برای جلوگیری از یک فاجعه جهانی وارد عمل می‌شود.",
        "poster_path": None,
    },
    {
        "title": "سفر به پانیاری",
        "genres": ["Animation", "Family", "Fantasy"],
        "rating": 8.2,
        "overview": "دختری در دنیایی جادویی گرفتار می‌شود و باید راهی برای بازگشت پیدا کند.",
        "poster_path": None,
    },
    {
        "title": "یک روز خوب",
        "genres": ["Documentary"],
        "rating": 7.5,
        "overview": "روایتی آرام از زندگی روزمره‌ی افراد در یک شهر کوچک.",
        "poster_path": None,
    },
]


class MovieRecommender:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TMDB_API_KEY")

    # ------------------------------------------------------------------
    # TMDB API Calls
    # ------------------------------------------------------------------
    def _fetch_movies_by_genres(
        self,
        genre_names: List[str],
        language: str = "fa-IR",
        page: int = 1,
    ) -> List[Dict]:
        """
        فراخوانی TMDB Discover API با cache.
        page به عنوان بخشی از cache key استفاده می‌شود تا
        صفحات مختلف جداگانه کش شوند و تنوع فراهم گردد.
        """
        if not self.api_key:
            return []

        genre_ids = [str(TMDB_GENRE_IDS[g]) for g in genre_names if g in TMDB_GENRE_IDS]
        if not genre_ids:
            return []

        cache_key = cache.build_cache_key("tmdb_discover_movie_v2", sorted(genre_ids), language, page)
        cached_results = cache.get_cached(cache_key)
        if cached_results is not None:
            return cached_results

        params = {
            "api_key": self.api_key,
            "language": language,
            "with_genres": ",".join(genre_ids),
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "page": page,
        }

        try:
            response = requests.get(f"{TMDB_BASE_URL}/discover/movie", params=params, timeout=5)
            response.raise_for_status()
            results = response.json().get("results", [])
            cache.set_cached(cache_key, results, ttl_hours=cache.CACHE_TTL_HOURS)
            return results
        except (requests.RequestException, ValueError):
            if language != "en-US":
                return self._fetch_movies_by_genres(genre_names, "en-US", page)
            return []

    def _normalize_tmdb_movie(self, movie: Dict) -> Dict:
        genre_ids = movie.get("genre_ids", [])
        genres = [TMDB_ID_TO_GENRE[gid] for gid in genre_ids if gid in TMDB_ID_TO_GENRE]
        poster_path = movie.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None
        return {
            "title": movie.get("title") or movie.get("original_title", "بدون عنوان"),
            "genres": genres,
            "rating": movie.get("vote_average", 0.0),
            "overview": movie.get("overview", ""),
            "poster_path": poster_url,
        }

    # ------------------------------------------------------------------
    # Reasoning
    # ------------------------------------------------------------------
    @staticmethod
    def _build_reasoning(
        movie: Dict,
        mood: str,
        energy: str,
        activity: str,
        time_period: str,
        target_genres: List[str],
        safety_active: bool,
    ) -> List[str]:
        reasons = []

        matched_genres = set(g.lower() for g in movie["genres"]) & set(g.lower() for g in target_genres)
        if matched_genres:
            reasons.append(
                f"احساس «{mood}» تشخیص داده شد و این فیلم با ژانر(های) "
                f"{', '.join(matched_genres)} با آن همخوانی دارد."
            )

        if energy == "low":
            reasons.append("سطح انرژی شما پایین است، پس محتوای سبک و آرام پیشنهاد شد.")
        elif energy == "high":
            reasons.append("سطح انرژی شما بالاست، پس محتوای پرانرژی پیشنهاد شد.")

        if time_period == "night":
            reasons.append("زمان فعلی شب است؛ این فیلم برای ساعات پایانی روز مناسب است.")
        elif time_period == "morning":
            reasons.append("زمان فعلی صبح است؛ این محتوا برای شروع روز مناسب است.")

        if activity and activity != "general":
            reasons.append(f"با توجه به فعالیت فعلی شما ({activity})، این پیشنهاد مناسب است.")

        if safety_active:
            reasons.append("با توجه به شدت احساس فعلی، یک محتوای امیدبخش پیشنهاد شده است.")

        if not reasons:
            reasons.append("این فیلم به‌عنوان یک گزینه‌ی عمومی و محبوب پیشنهاد شده است.")

        return reasons

    # ------------------------------------------------------------------
    # Main
    # ------------------------------------------------------------------
    def recommend(
        self,
        mood: str,
        energy: str,
        activity: str,
        time_period: str,
        safety_active: bool = False,
        top_n: int = TOP_N_MOVIES,
    ) -> List[Dict]:
        target_genres = MOOD_GENRE_MAPPING.get(mood, MOOD_GENRE_MAPPING["neutral"])

        if safety_active:
            target_genres = ["Comedy", "Family"]

        try:
            taste_profile = db.get_taste_profile()
        except Exception:
            taste_profile = {}

        # انتخاب تصادفی page از TMDB برای تنوع
        page = random.randint(1, TMDB_PAGE_POOL)
        raw_movies = self._fetch_movies_by_genres(target_genres, page=page)

        # اگر page انتخاب‌شده خالی بود، از page 1 fallback کن
        if not raw_movies and page > 1:
            raw_movies = self._fetch_movies_by_genres(target_genres, page=1)

        if raw_movies:
            movies = [self._normalize_tmdb_movie(m) for m in raw_movies]
            source = "tmdb"
        else:
            movies = list(MOCK_MOVIES)
            source = "mock"

        # امتیازدهی
        scored_movies = []
        for movie in movies:
            mood_score = genre_match_score(movie["genres"], target_genres)
            en_score = energy_match_score(
                "low" if "comedy" in [g.lower() for g in movie["genres"]] else energy,
                energy,
            )
            act_score = 1.0 if activity == "general" else 0.5

            final_score = calculate_final_score(mood_score, en_score, act_score)

            boost, boost_reason = personalization.movie_boost(movie["genres"], taste_profile)
            final_score = round(final_score * boost, 2)

            reasoning = self._build_reasoning(
                movie, mood, energy, activity, time_period, target_genres, safety_active
            )
            if boost_reason:
                reasoning.append(boost_reason)

            scored_movies.append({**movie, "final_score": final_score, "reasoning": reasoning})

        # نمونه‌برداری وزن‌دار → تنوع واقعی در هر بار پیشنهاد
        result = weighted_sample(scored_movies, score_key="final_score", n=top_n)

        for item in result:
            item["source"] = source

        return result


# ----------------------------------------------------------------------
# Singleton
# ----------------------------------------------------------------------
_default_recommender: Optional[MovieRecommender] = None


def recommend_movies(
    mood: str, energy: str, activity: str, time_period: str, safety_active: bool = False
) -> List[Dict]:
    global _default_recommender
    if _default_recommender is None:
        _default_recommender = MovieRecommender()
    return _default_recommender.recommend(mood, energy, activity, time_period, safety_active)
