"""
Content Safety Layer
When heavy emotional states are detected, override to uplifting content.
"""
from config.constants import SAFETY_MOODS, MOOD_TO_MOVIE_GENRES


SAFE_MOVIE_GENRES = ["comedy", "animation", "family", "adventure"]
SAFE_MUSIC_TAGS   = ["آرام‌بخش", "امیدبخش", "آرام", "شاد"]

SAFETY_MESSAGE = (
    "به دلیل تشخیص وضعیت احساسی شما، پیشنهادهای آرام‌تر و امیدبخش‌تر "
    "انتخاب شدند. امیدواریم حالتون بهتر بشه 💙"
)


def is_triggered(mood: str) -> bool:
    return mood in SAFETY_MOODS


def safe_genres(mood: str) -> list[str]:
    """Return safe genre list — overrides to uplifting genres for heavy moods."""
    if is_triggered(mood):
        return SAFE_MOVIE_GENRES
    return MOOD_TO_MOVIE_GENRES.get(mood, ["comedy", "drama"])


def safety_note(mood: str) -> str | None:
    return SAFETY_MESSAGE if is_triggered(mood) else None