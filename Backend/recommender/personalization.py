"""
VibeAI - Personalization Layer
================================

تنظیم final_score پیشنهادها بر اساس پروفایل ذائقه‌ای که از لایک/دیسلایک‌های
قبلی کاربر یاد گرفته شده (database.db.get_taste_profile).

این لایه صرفاً final_score را کمی جابه‌جا می‌کند (حداکثر ±MAX_BOOST) تا
mood/energy/activity همچنان سیگنال اصلی رتبه‌بندی باقی بماند.
"""

from typing import Dict, List, Optional, Tuple

BOOST_PER_UNIT_SCORE = 0.05
MAX_BOOST = 0.35
MIN_SIGNAL_SCORE = 1.0


def _multiplier(item_genres: List[str], genre_scores: Dict[str, float]) -> Tuple[float, Optional[str]]:
    """
    محاسبه‌ی ضریب شخصی‌سازی برای یک آیتم بر اساس ژانرهایش.

    خروجی: (ضریب نهایی final_score, جمله‌ی دلیل به فارسی یا None)
    """
    if not item_genres or not genre_scores:
        return 1.0, None

    matched = [
        (genre, genre_scores[genre])
        for genre in item_genres
        if genre in genre_scores and abs(genre_scores[genre]) >= MIN_SIGNAL_SCORE
    ]
    if not matched:
        return 1.0, None

    avg_score = sum(score for _, score in matched) / len(matched)
    delta = max(-MAX_BOOST, min(MAX_BOOST, avg_score * BOOST_PER_UNIT_SCORE))

    reason = None
    if delta > 0.03:
        best_genre = max(matched, key=lambda t: t[1])[0]
        reason = f"چون قبلاً چند مورد با ژانر «{best_genre}» رو لایک کرده بودی، این گزینه رو بالاتر آوردیم."

    return 1.0 + delta, reason


def movie_boost(item_genres: List[str], profile: Dict[str, Dict[str, float]]) -> Tuple[float, Optional[str]]:
    return _multiplier(item_genres, profile.get("movie_genre", {}))


def music_boost(item_genre: str, profile: Dict[str, Dict[str, float]]) -> Tuple[float, Optional[str]]:
    return _multiplier([item_genre] if item_genre else [], profile.get("music_genre", {}))
