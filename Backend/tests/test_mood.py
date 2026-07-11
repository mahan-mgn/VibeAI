"""
Tests for the Mood Analysis Engine
Run: pytest tests/test_mood.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from mood.analyzer import analyze
from mood.negation import is_negated
from mood.time_detector import detect as detect_time


# ── analyzer tests ─────────────────────────────────────────────────────────────

class TestAnalyzer:
    def test_tired_detection(self):
        r = analyze("امروز خیلی خسته‌ام و یه فیلم سبک می‌خوام")
        assert r["mood"] == "tired"
        assert r["energy"] == "low"

    def test_stressed_detection(self):
        r = analyze("خیلی استرس داشتم امروز و ناراحتم")
        assert r["mood"] == "stressed"

    def test_happy_detection(self):
        r = analyze("خیلی شادم امروز یه فیلم خنده‌دار می‌خوام")
        assert r["mood"] == "happy"

    def test_coding_activity(self):
        r = analyze("دارم برنامه‌نویسی می‌کنم و یه موزیک تمرکزی می‌خوام")
        assert r["activity"] == "coding"

    def test_low_confidence_returns_default(self):
        r = analyze("سلام")
        assert r["mood"] == "neutral"
        assert r["confidence"] == 0.30

    def test_confidence_above_threshold(self):
        r = analyze("خیلی خسته‌ام و انرژی ندارم")
        assert r["confidence"] >= 0.40

    def test_safety_mood_in_moods_dict(self):
        r = analyze("خیلی استرس دارم و نگرانم")
        assert "stressed" in r["moods"]


# ── negation tests ─────────────────────────────────────────────────────────────

class TestNegation:
    def test_negation_detected(self):
        assert is_negated("خسته نیستم", "خسته") is True

    def test_no_negation(self):
        assert is_negated("خیلی خسته‌ام", "خسته") is False

    def test_nadaram_pattern(self):
        assert is_negated("استرس ندارم", "استرس") is True


# ── time detector tests ────────────────────────────────────────────────────────

class TestTimeDetector:
    def test_night_from_text(self):
        assert detect_time("الان ساعت ۱ شبه") == "night"

    def test_morning_from_text(self):
        assert detect_time("صبح زود بیدار شدم") == "morning"

    def test_fallback_to_clock(self):
        # Should return a valid period (clock-based)
        result = detect_time("یه چیزی می‌خوام")
        assert result in ("morning", "afternoon", "evening", "night")