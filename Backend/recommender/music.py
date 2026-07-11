"""
VibeAI - Music Recommendation Engine
======================================

پیشنهاد موسیقی بر اساس Mood/Energy/Activity کاربر، با استفاده از
دیتاست محلی (Local Dataset) و لینک جستجوی YouTube (بخش 18 و 19 مستند).

تعداد خروجی: Top 10 Songs
"""

import json
import os
import urllib.parse
from typing import Dict, List, Optional

from database import db
from recommender import personalization
from recommender.ranking import (
    activity_match_score,
    calculate_final_score,
    energy_match_score,
    weighted_sample,
)
from services import spotify_service


DATASET_PATH = os.path.join(os.path.dirname(__file__), "music_dataset.json")

TOP_N_SONGS = 10

YOUTUBE_SEARCH_BASE_URL = "https://www.youtube.com/results?search_query="

# نگاشت activity به ژانرهای موزیک مناسب (بخش 15 مستند)
ACTIVITY_MUSIC_MAPPING = {
    "coding": ["Lo-Fi"],
    "studying": ["Classical"],
    "resting": ["Ambient"],
    "exercise": ["EDM", "Rock", "Hip-Hop", "Pop"],
    "general": ["Pop", "Indie", "Electronic", "R&B", "Alternative", "Ambient", "Classical", "Lo-Fi", "Hip-Hop", "Rock", "EDM"],
}


class MusicRecommender:
    def __init__(self, dataset_path: str = DATASET_PATH):
        self.dataset_path = dataset_path
        self._songs = self._load_dataset()

    def _load_dataset(self) -> List[Dict]:
        """
        بارگذاری دیتاست موزیک از فایل JSON.
        در صورت بروز خطا (فایل خراب/موجود نبود)، لیست خالی برمی‌گرداند
        تا سیستم Crash نکند (بخش 27 مستند).
        """
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @staticmethod
    def _build_youtube_link(title: str, artist: str) -> str:
        """ساخت لینک جستجوی YouTube برای یک آهنگ."""
        query = f"{artist} {title}"
        encoded_query = urllib.parse.quote_plus(query)
        return f"{YOUTUBE_SEARCH_BASE_URL}{encoded_query}"

    # ------------------------------------------------------------------
    # Reasoning (بخش 20 مستند)
    # ------------------------------------------------------------------
    @staticmethod
    def _build_reasoning(
        song: Dict,
        mood: str,
        energy: str,
        activity: str,
        safety_active: bool,
    ) -> List[str]:
        reasons = []

        if song.get("mood") == mood:
            reasons.append(f"احساس «{mood}» تشخیص داده شد و این آهنگ با این حال‌وهوا همخوانی دارد.")

        if song.get("energy") == energy:
            energy_fa = {"low": "پایین", "medium": "متوسط", "high": "بالا"}.get(energy, energy)
            reasons.append(f"سطح انرژی این آهنگ با سطح انرژی فعلی شما ({energy_fa}) مطابقت دارد.")

        if activity != "general" and activity in song.get("activity_tags", []):
            reasons.append(f"این آهنگ برای فعالیت «{activity}» مناسب است.")

        if safety_active:
            reasons.append("با توجه به شدت بالای احساس فعلی، یک موسیقی آرام‌بخش پیشنهاد شده است.")

        if not reasons:
            reasons.append("این آهنگ به‌عنوان یک گزینه‌ی عمومی و محبوب پیشنهاد شده است.")

        return reasons

    # ------------------------------------------------------------------
    # Main Recommendation Method
    # ------------------------------------------------------------------
    def recommend(
        self,
        mood: str,
        energy: str,
        activity: str,
        time_period: str = "current",
        safety_active: bool = False,
        top_n: int = TOP_N_SONGS,
    ) -> List[Dict]:
        """
        پیشنهاد موسیقی بر اساس mood/energy/activity.

        خروجی: لیستی از آهنگ‌ها به همراه:
        - title, artist, genre, youtube_link
        - final_score
        - reasoning (لیست دلایل پیشنهاد)
        """
        if not self._songs:
            return []

        # در صورت فعال بودن Content Safety Layer، اولویت با موسیقی آرام
        target_mood = "calm" if safety_active else mood
        target_energy = "low" if safety_active else energy

        try:
            taste_profile = db.get_taste_profile()
        except Exception:
            taste_profile = {}

        scored_songs = []
        for song in self._songs:
            # Mood Match: تطابق mood آهنگ با mood هدف
            mood_score = 1.0 if song.get("mood") == target_mood else 0.0

            # Energy Match
            en_score = energy_match_score(song.get("energy", "medium"), target_energy)

            # Activity Match: تطابق ژانر آهنگ با ژانرهای مناسب فعالیت
            act_score = activity_match_score([song.get("genre", "")], activity, ACTIVITY_MUSIC_MAPPING)

            final_score = calculate_final_score(mood_score, en_score, act_score)

            boost, boost_reason = personalization.music_boost(song.get("genre", ""), taste_profile)
            final_score = round(final_score * boost, 2)

            reasoning = self._build_reasoning(song, mood, energy, activity, safety_active)
            if boost_reason:
                reasoning.append(boost_reason)

            scored_songs.append(
                {
                    "title": song["title"],
                    "artist": song["artist"],
                    "genre": song["genre"],
                    "youtube_link": self._build_youtube_link(song["title"], song["artist"]),
                    "final_score": final_score,
                    "reasoning": reasoning,
                }
            )

        top_songs = weighted_sample(scored_songs, score_key="final_score", n=top_n)

        for song in top_songs:
            song["spotify_url"] = None
            song["spotify_preview_url"] = None
            song["album_image"] = None
            try:
                spotify_data = spotify_service.search_track(song["title"], song["artist"])
            except Exception:
                spotify_data = None
            if spotify_data:
                song["spotify_url"] = spotify_data.get("spotify_url")
                song["spotify_preview_url"] = spotify_data.get("preview_url")
                song["album_image"] = spotify_data.get("album_image")

        return top_songs


# ----------------------------------------------------------------------
# Convenience function
# ----------------------------------------------------------------------
_default_recommender: Optional[MusicRecommender] = None


def recommend_music(mood: str, energy: str, activity: str, time_period: str = "current", safety_active: bool = False) -> List[Dict]:
    global _default_recommender
    if _default_recommender is None:
        _default_recommender = MusicRecommender()
    return _default_recommender.recommend(mood, energy, activity, time_period, safety_active)


if __name__ == "__main__":
    recommender = MusicRecommender()

    result = recommender.recommend(
        mood="tired",
        energy="low",
        activity="coding",
        time_period="night",
        safety_active=False,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))