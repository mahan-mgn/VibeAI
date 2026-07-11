"""
Time Period Detector
Priority: explicit mention in text → system clock fallback
"""
import json
import os
from datetime import datetime

_kw_path = os.path.join(os.path.dirname(__file__), "keywords.json")
with open(_kw_path, encoding="utf-8") as f:
    _TIME_KW: dict[str, list[str]] = json.load(f)["time"]


def _normalize(text: str) -> str:
    return text.replace("\u200c", "").replace("\u200f", "").replace("\u200e", "")


def from_text(text: str) -> str | None:
    """
    Try to extract time period from text.
    Returns one of: 'morning' | 'afternoon' | 'evening' | 'night' | None
    """
    normalized = _normalize(text)
    for period, keywords in _TIME_KW.items():
        for kw in keywords:
            if _normalize(kw) in normalized:
                return period
    return None


def from_clock() -> str:
    """Determine time period from current system time."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


def detect(text: str) -> str:
    """
    Main entry point.
    Text mention wins; falls back to system clock.
    """
    return from_text(text) or from_clock()