"""
VibeAI - Gemini Mood Analyzer (V3)
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, Optional

from google import genai
from google.genai import types

MODEL_NAME = "gemini-2.5-flash"

VALID_MOODS = {"tired", "stressed", "happy", "excited", "calm", "anxious", "sad", "bored", "neutral"}
VALID_ENERGIES = {"low", "medium", "high"}
VALID_ACTIVITIES = {"coding", "studying", "resting", "exercise", "general"}
VALID_TIME_PERIODS = {"morning", "afternoon", "evening", "night", "current"}

JSON_EXAMPLE = '{"mood": "tired", "moods": {"tired": 8}, "energy": "low", "activity": "general", "time_period": "night", "confidence": 0.9, "negations_detected": []}'


def _remove_zws(text: str) -> str:
    """حذف نیم فاصله و کاراکترهای zero-width که Gemini را گیج می کنند."""
    text = text.replace("\u200c", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\u200d", "")
    return text.strip()


class GeminiAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._client = None

        if self.api_key:
            self._client = genai.Client(api_key=self.api_key)

    @property
    def is_available(self) -> bool:
        return self._client is not None

    @staticmethod
    def _build_prompt(text: str) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_hint = "morning"
        elif 12 <= hour < 17:
            time_hint = "afternoon"
        elif 17 <= hour < 21:
            time_hint = "evening"
        else:
            time_hint = "night"

        prompt = _remove_zws(text) + "\n\n"
        prompt += "زمان فعلی: " + time_hint + "\n\n"
        prompt += "بر اساس متن بالا، احساس کاربر را تحلیل کن و فقط یک JSON برگردان.\n"
        prompt += "mood باید یکی از این ها باشه: tired, stressed, happy, excited, calm, anxious, sad, bored, neutral\n"
        prompt += "energy باید یکی از این ها باشه: low, medium, high\n"
        prompt += "activity باید یکی از این ها باشه: coding, studying, resting, exercise, general\n\n"
        prompt += "نمونه خروجی:\n"
        prompt += JSON_EXAMPLE
        return prompt

    @staticmethod
    def _validate_and_clean(raw: Dict) -> Dict:
        mood = raw.get("mood", "neutral")
        if mood not in VALID_MOODS:
            mood = "neutral"

        moods_raw = raw.get("moods", {})
        moods = {}
        if isinstance(moods_raw, dict):
            for k, v in moods_raw.items():
                if k in VALID_MOODS and isinstance(v, (int, float)):
                    moods[k] = int(v)

        if mood != "neutral" and mood not in moods:
            moods[mood] = 5

        energy = raw.get("energy", "medium")
        if energy not in VALID_ENERGIES:
            energy = "medium"

        activity = raw.get("activity", "general")
        if activity not in VALID_ACTIVITIES:
            activity = "general"

        time_period = raw.get("time_period", "current")
        if time_period not in VALID_TIME_PERIODS:
            time_period = "current"

        confidence = raw.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        confidence = round(float(max(0.0, min(1.0, confidence))), 2)

        return {
            "mood": mood,
            "moods": moods,
            "energy": energy,
            "activity": activity,
            "time_period": time_period,
            "confidence": confidence,
            "negations_detected": raw.get("negations_detected", []),
            "analyzer": "gemini",
        }

    def analyze(self, text: str) -> Optional[Dict]:
        if not self.is_available:
            return None

        if not text or not text.strip():
            return None

        try:
            prompt = self._build_prompt(text)

            response = self._client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1000,
                    response_mime_type="application/json",
                ),
            )

            if not response.text:
                return None

            cleaned = response.text.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

            raw = json.loads(cleaned)
            return self._validate_and_clean(raw)

        except json.JSONDecodeError as e:
            print(f"[GeminiAnalyzer] JSONDecodeError: {e}")
            print(f"[GeminiAnalyzer] Raw response was: {repr(cleaned[:300])}")
            return None
        except Exception as e:
            print(f"[GeminiAnalyzer] Error: {type(e).__name__}: {e}")
            return None


_default_gemini: Optional[GeminiAnalyzer] = None


def analyze_with_gemini(text: str) -> Optional[Dict]:
    global _default_gemini
    if _default_gemini is None:
        _default_gemini = GeminiAnalyzer()
    return _default_gemini.analyze(text)