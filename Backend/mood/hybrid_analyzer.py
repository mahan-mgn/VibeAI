"""
VibeAI - Hybrid Mood Analyzer (V3)
=====================================

معماری Hybrid که اول Gemini AI را امتحان می‌کند؛
اگر Gemini در دسترس نبود یا خطا داد، به Rule-Based Engine برمی‌گردد.

Pipeline:
متن کاربر
    ↓
Gemini available? ─── نه ──→ Rule-Based Engine
    ↓ بله                           ↓
Gemini.analyze()           نتیجه‌ی پایه‌ای
    ↓                       (analyzer: "rule_based")
موفق؟ ─── نه ──→ Rule-Based Engine
    ↓ بله
نتیجه‌ی غنی‌تر
(analyzer: "gemini")
    ↓
خروجی یکسان (همان schema برای بقیه‌ی سیستم)
"""

import os
from typing import Dict

from mood.analyzer import MoodAnalyzer
from mood.gemini_analyzer import GeminiAnalyzer


class HybridAnalyzer:
    def __init__(self, gemini_api_key: str | None = None):
        """
        gemini_api_key: کلید API. اگه داده نشه از GEMINI_API_KEY خوانده می‌شه.
        """
        self._gemini = GeminiAnalyzer(api_key=gemini_api_key)
        self._rule_based = MoodAnalyzer()

    @property
    def gemini_active(self) -> bool:
        """آیا Gemini در دسترس است؟"""
        return self._gemini.is_available

    def analyze(self, text: str) -> Dict:
        """
        تحلیل متن با اولویت Gemini، با Fallback به Rule-Based.

        خروجی همان schema هر دو engine است:
        {
            "mood": str,
            "moods": dict,
            "energy": str,
            "activity": str,
            "time_period": str,
            "confidence": float,
            "negations_detected": list,
            "analyzer": "gemini" | "rule_based" | "fallback"
        }
        """
        # تلاش با Gemini (اگه در دسترس باشه)
        if self._gemini.is_available:
            gemini_result = self._gemini.analyze(text)
            if gemini_result is not None:
                return gemini_result
            print("[HybridAnalyzer] Gemini returned None -> switching to Rule-Based")
        else:
            print("[HybridAnalyzer] Gemini not available -> using Rule-Based")

        # Fallback به Rule-Based Engine
        rule_result = self._rule_based.analyze(text)
        rule_result["analyzer"] = "rule_based"
        return rule_result

    def requires_safety_layer(self, mood: str, moods: Dict) -> bool:
        """سازگاری با app.py — مستقیماً از Rule-Based می‌گیریم."""
        return self._rule_based.requires_safety_layer(mood, moods)


# ----------------------------------------------------------------------
# Singleton برای استفاده در app.py
# ----------------------------------------------------------------------
_default_hybrid: HybridAnalyzer | None = None


def get_hybrid_analyzer() -> HybridAnalyzer:
    global _default_hybrid
    if _default_hybrid is None:
        _default_hybrid = HybridAnalyzer(
            gemini_api_key=os.environ.get("GEMINI_API_KEY")
        )
    return _default_hybrid