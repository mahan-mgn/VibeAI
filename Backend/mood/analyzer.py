"""
VibeAI - Mood Analysis Engine
Rule-Based Engine برای تحلیل متن فارسی و تشخیص:
- Mood (با امکان تشخیص چند Mood)
- Energy Level
- Activity
- Time Context
- Confidence Score

Pipeline:
Text -> Normalization -> Negation Detection -> Mood Scoring
-> Dominant Mood -> Confidence -> Final Result
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), "keywords.json")

CONFIDENCE_LEVELS = {
    "very_high": (0.80, 1.00),
    "high": (0.60, 0.79),
    "medium": (0.40, 0.59),
    "fallback": (0.0, 0.39),
}

FALLBACK_RESULT_TEMPLATE = {
    "mood": "neutral",
    "moods": {},
    "energy": "medium",
    "activity": "general",
    "time_period": "current",
    "confidence": 0.30,
    "negations_detected": [],
}


class MoodAnalyzer:
    def __init__(self, keywords_path: str = KEYWORDS_PATH):
        with open(keywords_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.moods = self.data.get("moods", {})
        self.negation_patterns = self.data.get("negation_patterns", [])
        self.energy_map = self.data.get("energy", {})
        self.activity_map = self.data.get("activity", {})
        self.time_map = self.data.get("time_context", {})
        self.content_safety_moods = set(self.data.get("content_safety_moods", []))

    # ------------------------------------------------------------------
    # Step 1: Normalization
    # ------------------------------------------------------------------
    def normalize(self, text: str) -> str:
        """نرمال‌سازی متن فارسی: حذف فاصله‌های اضافه، یکسان‌سازی کاراکترها."""
        if not text:
            return ""

        text = text.strip()

        # یکسان‌سازی کاراکترهای عربی/فارسی رایج
        replacements = {
            "ي": "ی",
            "ك": "ک",
            "ة": "ه",
            "ۀ": "ه",
            "‌": " ",  # نیم‌فاصله -> فاصله (برای راحتی matching، اما کلیدواژه‌ها هم با نیم‌فاصله موجودند)
            # تبدیل ارقام فارسی/عربی به انگلیسی
            "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
            "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
            "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
            "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
        }
        for src, dst in replacements.items():
            text = text.replace(src, dst)

        # حذف فاصله‌های تکراری
        text = re.sub(r"\s+", " ", text)

        return text.lower().strip()

    # ------------------------------------------------------------------
    # Step 2: Negation Detection
    # ------------------------------------------------------------------
    @staticmethod
    def _build_boundary_pattern(phrase: str) -> "re.Pattern":
        """
        ساخت regex با مرز کلمه برای جلوگیری از match شدن substring داخل کلمات دیگر
        (مثلا 'ترس' داخل 'استرس' نباید match شود).
        مرز: شروع/پایان رشته یا فاصله یا علائم نگارشی.
        """
        escaped = re.escape(phrase)
        return re.compile(r"(?:(?<=^)|(?<=[\s\.\،\,\!\؟\?]))" + escaped + r"(?:(?=$)|(?=[\s\.\،\,\!\؟\?]))")

    def detect_negations(self, text: str) -> List[Tuple[str, int]]:
        """
        پیدا کردن موقعیت کلمات نفی در متن.
        خروجی: لیستی از (negation_word, position_index)
        """
        found = []
        for pattern in self.negation_patterns:
            normalized_pattern = self.normalize(pattern)
            regex = self._build_boundary_pattern(normalized_pattern)
            for match in regex.finditer(text):
                found.append((pattern, match.start()))
        return found

    def _is_negated(self, keyword_pos: int, keyword_len: int, negations: List[Tuple[str, int]], text: str) -> bool:
        """
        بررسی می‌کند آیا یک کلیدواژه توسط یک کلمه نفی نزدیک (قبل یا بعد) منفی شده.
        پنجره بررسی: حدود 15 کاراکتر اطراف کلیدواژه.
        """
        window = 15
        kw_start = keyword_pos
        kw_end = keyword_pos + keyword_len

        for _, neg_pos in negations:
            # نفی قبل از کلیدواژه (مثل "خسته نیستم" -> نه برعکس "نیستم خسته")
            if kw_end <= neg_pos <= kw_end + window:
                return True
            # نفی قبل از کلمه به صورت پیشوندی ("نه اینکه خسته باشم")
            if neg_pos < kw_start and kw_start - neg_pos <= window:
                return True

        return False

    # ------------------------------------------------------------------
    # Step 3: Mood Scoring
    # ------------------------------------------------------------------
    def score_moods(self, text: str, negations: List[Tuple[str, int]]) -> Dict[str, int]:
        """
        برای هر mood، امتیاز را بر اساس تعداد کلیدواژه‌های یافت‌شده (با در نظر گرفتن نفی) حساب می‌کند.
        """
        scores: Dict[str, int] = {}

        for mood_name, mood_data in self.moods.items():
            weight = mood_data.get("weight", 1)
            keywords = mood_data.get("keywords", [])
            score = 0

            for kw in keywords:
                normalized_kw = self.normalize(kw)
                regex = self._build_boundary_pattern(normalized_kw)
                for match in regex.finditer(text):
                    if self._is_negated(match.start(), len(normalized_kw), negations, text):
                        continue  # نادیده گرفتن کلیدواژه‌ی منفی‌شده
                    score += weight

            if score > 0:
                scores[mood_name] = score

        return scores

    # ------------------------------------------------------------------
    # Step 4: Dominant Mood
    # ------------------------------------------------------------------
    def get_dominant_mood(self, scores: Dict[str, int]) -> str:
        """
        انتخاب mood غالب با max(scores).
        در صورت تساوی، اولویت با moodهایی است که Content Safety Layer را فعال می‌کنند.
        """
        if not scores:
            return "neutral"

        max_score = max(scores.values())
        candidates = [m for m, s in scores.items() if s == max_score]

        if len(candidates) == 1:
            return candidates[0]

        # تساوی -> اولویت با content safety moods
        safety_candidates = [m for m in candidates if m in self.content_safety_moods]
        if safety_candidates:
            return safety_candidates[0]

        return candidates[0]

    # ------------------------------------------------------------------
    # Step 5: Confidence Scoring
    # ------------------------------------------------------------------
    def calculate_confidence(self, scores: Dict[str, int], text: str) -> float:
        """
        محاسبه‌ی Confidence بر اساس قدرت سیگنال (مجموع امتیازها نسبت به طول متن
        و میزان غلبه‌ی mood غالب).
        """
        if not scores:
            return 0.30

        total_score = sum(scores.values())
        max_score = max(scores.values())

        # نسبت غلبه mood غالب نسبت به کل امتیازها
        dominance_ratio = max_score / total_score if total_score > 0 else 0

        # پایه‌ی confidence بر اساس تعداد کلیدواژه‌های یافت‌شده
        base = min(0.5 + (max_score * 0.12), 0.95)

        # ترکیب با dominance_ratio
        confidence = base * (0.6 + 0.4 * dominance_ratio)

        return round(min(max(confidence, 0.0), 1.0), 2)

    @staticmethod
    def get_confidence_level(confidence: float) -> str:
        for level, (low, high) in CONFIDENCE_LEVELS.items():
            if low <= confidence <= high:
                return level
        return "fallback"

    # ------------------------------------------------------------------
    # Step 6: Energy Detection
    # ------------------------------------------------------------------
    def detect_energy(self, text: str, negations: List[Tuple[str, int]]) -> str:
        energy_scores = {"low": 0, "medium": 0, "high": 0}

        for level, level_data in self.energy_map.items():
            for kw in level_data.get("keywords", []):
                normalized_kw = self.normalize(kw)
                regex = self._build_boundary_pattern(normalized_kw)
                for match in regex.finditer(text):
                    if self._is_negated(match.start(), len(normalized_kw), negations, text):
                        continue
                    energy_scores[level] += 1

        if all(v == 0 for v in energy_scores.values()):
            return "medium"

        return max(energy_scores, key=energy_scores.get)

    # ------------------------------------------------------------------
    # Step 7: Activity Detection
    # ------------------------------------------------------------------
    def detect_activity(self, text: str) -> str:
        for activity_name, activity_data in self.activity_map.items():
            for kw in activity_data.get("keywords", []):
                normalized_kw = self.normalize(kw)
                if not normalized_kw:
                    continue
                if self._build_boundary_pattern(normalized_kw).search(text):
                    return activity_name
        return "general"

    # ------------------------------------------------------------------
    # Step 8: Time Detection
    # ------------------------------------------------------------------
    def detect_time_context(self, text: str) -> str:
        """
        اولویت ۱: زمان ذکر شده در متن کاربر
        اولویت ۲: زمان سیستم (datetime.now())
        """
        # اولویت ۱: بررسی کلیدواژه‌های زمانی در متن
        for period_name, period_data in self.time_map.items():
            for kw in period_data.get("keywords", []):
                normalized_kw = self.normalize(kw)
                if not normalized_kw:
                    continue
                if self._build_boundary_pattern(normalized_kw).search(text):
                    return period_name

        # اولویت ۲: زمان سیستم
        return self._time_period_from_system_clock()

    def _time_period_from_system_clock(self) -> str:
        hour = datetime.now().hour

        for period_name, period_data in self.time_map.items():
            hour_range = period_data.get("hour_range")
            if not hour_range:
                continue
            start, end = hour_range
            if start <= end:
                if start <= hour <= end:
                    return period_name
            else:
                # بازه‌ای که از نیمه‌شب رد می‌شود (مثل night: 21 -> 4)
                if hour >= start or hour <= end:
                    return period_name

        return "current"

    # ------------------------------------------------------------------
    # Main Pipeline
    # ------------------------------------------------------------------
    def analyze(self, text: str) -> Dict:
        """
        اجرای کامل pipeline تحلیل احساسات.

        خروجی نمونه:
        {
            "mood": "stressed",
            "moods": {"stressed": 8, "tired": 7},
            "energy": "low",
            "activity": "coding",
            "time_period": "night",
            "confidence": 0.82,
            "negations_detected": []
        }
        """
        if not text or not text.strip():
            return dict(FALLBACK_RESULT_TEMPLATE)

        # 1. Normalization
        normalized_text = self.normalize(text)

        # 2. Negation Detection
        negations = self.detect_negations(normalized_text)

        # 3. Mood Scoring
        mood_scores = self.score_moods(normalized_text, negations)

        # 4. Dominant Mood
        dominant_mood = self.get_dominant_mood(mood_scores)

        # 5. Confidence
        confidence = self.calculate_confidence(mood_scores, normalized_text)

        # 6. Energy
        energy = self.detect_energy(normalized_text, negations)

        # 7. Activity
        activity = self.detect_activity(normalized_text)

        # 8. Time Context
        time_period = self.detect_time_context(normalized_text)

        result = {
            "mood": dominant_mood,
            "moods": mood_scores,
            "energy": energy,
            "activity": activity,
            "time_period": time_period,
            "confidence": confidence,
            "negations_detected": [neg[0] for neg in negations],
        }

        # Fallback در صورت پایین بودن confidence
        if confidence < 0.40:
            fallback = dict(FALLBACK_RESULT_TEMPLATE)
            fallback["moods"] = mood_scores
            fallback["confidence"] = confidence if confidence > 0 else 0.30
            fallback["negations_detected"] = result["negations_detected"]
            # حفظ energy/activity/time در صورت تشخیص معتبر بودنشان
            fallback["energy"] = energy
            fallback["activity"] = activity
            fallback["time_period"] = time_period
            return fallback

        return result

    # ------------------------------------------------------------------
    # Helper: Content Safety Check
    # ------------------------------------------------------------------
    def requires_safety_layer(self, mood: str, moods: Dict[str, int]) -> bool:
        """
        بررسی اینکه آیا نتیجه باید Content Safety Layer را فعال کند.
        شرط: mood غالب جزو content_safety_moods باشد و امتیاز بالایی داشته باشد (شدید).
        """
        if mood not in self.content_safety_moods:
            return False

        score = moods.get(mood, 0)
        # امتیاز بالا (>= 4، یعنی حداقل ۲ کلیدواژه با وزن ۲) به معنی شدت بالا
        return score >= 4


# ----------------------------------------------------------------------
# Convenience function for direct use
# ----------------------------------------------------------------------
_default_analyzer: Optional[MoodAnalyzer] = None


def analyze_text(text: str) -> Dict:
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = MoodAnalyzer()
    return _default_analyzer.analyze(text)


if __name__ == "__main__":
    analyzer = MoodAnalyzer()

    samples = [
        "امروز خیلی خسته‌ام و یه فیلم سبک می‌خوام",
        "دارم برنامه‌نویسی می‌کنم و یه پلی‌لیست تمرکزی لازم دارم",
        "امروز استرس زیادی داشتم و یه موزیک آروم می‌خوام",
        "خسته نیستم اصلا",
        "استرس دارم و خسته‌ام",
        "الان ساعت ۱ شبه و حوصلم سر رفته",
        "سلام چطوری",
    ]

    for s in samples:
        print(s)
        print(json.dumps(analyzer.analyze(s), ensure_ascii=False, indent=2))
        print("-" * 40)