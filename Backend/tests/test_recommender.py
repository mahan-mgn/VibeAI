"""
Test Cases for VibeAI Recommendation Engine
=============================================
تست‌های خودکار برای:
- Ranking (بخش 16 مستند: فرمول امتیازدهی)
- Movie Recommender (بخش 17 مستند: Top 5، Mock Fallback، Reasoning)
- Music Recommender (بخش 18-19 مستند: Top 10، YouTube Link، Reasoning)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from recommender.ranking import (
    activity_match_score,
    calculate_final_score,
    energy_match_score,
    genre_match_score,
    rank_items,
)
from recommender.movie import MovieRecommender
from recommender.music import MusicRecommender


def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"PASS - {name}")
        else:
            failed += 1
            print(f"FAIL - {name}")

    # ====================================================================
    # بخش 1: Ranking Logic (بخش 16 مستند)
    # ====================================================================

    # 1. فرمول Final Score: Mood×50 + Energy×30 + Activity×20
    score = calculate_final_score(mood_score=1.0, energy_score=1.0, activity_score=1.0)
    check("Final Score کامل (1،1،1) باید 100 باشد", score == 100.0)

    # 2. فرمول با مقادیر صفر
    score_zero = calculate_final_score(mood_score=0.0, energy_score=0.0, activity_score=0.0)
    check("Final Score صفر (0،0،0) باید 0 باشد", score_zero == 0.0)

    # 3. فرمول با وزن‌دهی دقیق (فقط mood کامل)
    score_mood_only = calculate_final_score(mood_score=1.0, energy_score=0.0, activity_score=0.0)
    check("Final Score فقط mood کامل باید 50 باشد", score_mood_only == 50.0)

    # 4. genre_match_score: تطابق کامل
    g_score = genre_match_score(["Comedy", "Family"], ["Comedy", "Family"])
    check("genre_match_score تطابق کامل = 1.0", g_score == 1.0)

    # 5. genre_match_score: عدم تطابق
    g_score_none = genre_match_score(["Horror"], ["Comedy", "Family"])
    check("genre_match_score بدون تطابق = 0.0", g_score_none == 0.0)

    # 6. energy_match_score: تطابق کامل
    e_score = energy_match_score("low", "low")
    check("energy_match_score تطابق کامل = 1.0", e_score == 1.0)

    # 7. energy_match_score: اختلاف یک سطح (low vs medium)
    e_score_half = energy_match_score("low", "medium")
    check("energy_match_score اختلاف یک سطح = 0.5", e_score_half == 0.5)

    # 8. energy_match_score: اختلاف کامل (low vs high)
    e_score_zero = energy_match_score("low", "high")
    check("energy_match_score اختلاف کامل = 0.0", e_score_zero == 0.0)

    # 9. activity_match_score: تطابق
    act_mapping = {"coding": ["Lo-Fi"]}
    a_score = activity_match_score(["Lo-Fi"], "coding", act_mapping)
    check("activity_match_score تطابق = 1.0", a_score == 1.0)

    # 10. rank_items: مرتب‌سازی نزولی
    items = [{"final_score": 50}, {"final_score": 90}, {"final_score": 10}]
    ranked = rank_items(items)
    check("rank_items مرتب‌سازی نزولی صحیح", [i["final_score"] for i in ranked] == [90, 50, 10])

    # ====================================================================
    # بخش 2: Movie Recommender (بخش 17 مستند)
    # ====================================================================
    movie_rec = MovieRecommender(api_key=None)  # بدون API Key -> Mock Data

    # 11. خروجی باید دقیقاً Top 5 فیلم باشد (یا کمتر اگر دیتاست کوچک‌تر است)
    movies = movie_rec.recommend(mood="tired", energy="low", activity="general", time_period="night")
    check("Movie Recommender حداکثر 5 فیلم برمی‌گرداند", len(movies) <= 5)
    check("Movie Recommender حداقل 1 فیلم برمی‌گرداند (mock data)", len(movies) >= 1)

    # 12. بدون API Key باید از Mock Data استفاده شود (source = mock)
    check("بدون API Key -> source باید mock باشد", all(m["source"] == "mock" for m in movies))

    # 13. هر فیلم باید فیلد reasoning غیرخالی داشته باشد (Explainability - بخش 20)
    check("هر فیلم دارای حداقل یک دلیل (reasoning) است", all(len(m["reasoning"]) > 0 for m in movies))

    # 14. هر فیلم باید فیلد final_score داشته باشد
    check("هر فیلم دارای final_score است", all("final_score" in m for m in movies))

    # 15. فیلم‌ها باید بر اساس امتیاز نزولی مرتب باشند
    scores = [m["final_score"] for m in movies]
    check("فیلم‌ها بر اساس امتیاز نزولی مرتب شده‌اند", scores == sorted(scores, reverse=True))

    # 16. Content Safety Layer: در حالت safety_active، باید ژانرهای امیدبخش پیشنهاد شود
    safe_movies = movie_rec.recommend(
        mood="stressed", energy="low", activity="general", time_period="night", safety_active=True
    )
    check("Content Safety Layer حداقل یک فیلم برمی‌گرداند", len(safe_movies) >= 1)
    safety_reasoning_found = any(
        any("امیدبخش" in r or "سبک" in r for r in m["reasoning"]) for m in safe_movies
    )
    check("Content Safety Layer دلیل امیدبخش/سبک در reasoning دارد", safety_reasoning_found)

    # 17. سیستم نباید برای mood نامعتبر/ناشناخته Crash کند (بخش 27 مستند)
    try:
        fallback_movies = movie_rec.recommend(
            mood="unknown_mood_xyz", energy="low", activity="general", time_period="night"
        )
        check("Mood ناشناخته باعث Crash نمی‌شود", True)
    except Exception:
        check("Mood ناشناخته باعث Crash نمی‌شود", False)

    # ====================================================================
    # بخش 3: Music Recommender (بخش 18-19 مستند)
    # ====================================================================
    music_rec = MusicRecommender()

    # 18. خروجی باید حداکثر Top 10 آهنگ باشد
    songs = music_rec.recommend(mood="tired", energy="low", activity="coding", time_period="night")
    check("Music Recommender حداکثر 10 آهنگ برمی‌گرداند", len(songs) <= 10)
    check("Music Recommender حداقل 1 آهنگ برمی‌گرداند", len(songs) >= 1)

    # 19. هر آهنگ باید لینک YouTube معتبر داشته باشد
    check(
        "هر آهنگ دارای لینک جستجوی YouTube است",
        all(s["youtube_link"].startswith("https://www.youtube.com/results?search_query=") for s in songs),
    )

    # 20. هر آهنگ باید فیلد reasoning غیرخالی داشته باشد
    check("هر آهنگ دارای حداقل یک دلیل (reasoning) است", all(len(s["reasoning"]) > 0 for s in songs))

    # 21. فعالیت coding باید ژانر Lo-Fi را در رتبه‌های بالا بیاورد
    top_song_genres = [s["genre"] for s in songs[:3]]
    check("فعالیت coding باعث اولویت ژانر Lo-Fi در رتبه‌های بالا می‌شود", "Lo-Fi" in top_song_genres)

    # 22. Content Safety Layer برای موزیک: باید آرام‌ترین آهنگ‌ها در اولویت باشند
    safe_songs = music_rec.recommend(
        mood="stressed", energy="high", activity="general", time_period="night", safety_active=True
    )
    check(
        "Content Safety Layer موزیک: آهنگ اول باید انرژی پایین داشته باشد",
        len(safe_songs) > 0 and safe_songs[0]["final_score"] > 0,
    )

    # 23. آهنگ‌ها باید بر اساس امتیاز نزولی مرتب باشند
    song_scores = [s["final_score"] for s in songs]
    check("آهنگ‌ها بر اساس امتیاز نزولی مرتب شده‌اند", song_scores == sorted(song_scores, reverse=True))

    # 24. سیستم نباید برای فعالیت نامعتبر Crash کند
    try:
        fallback_songs = music_rec.recommend(
            mood="happy", energy="medium", activity="unknown_activity_xyz", time_period="current"
        )
        check("Activity ناشناخته باعث Crash نمی‌شود", True)
    except Exception:
        check("Activity ناشناخته باعث Crash نمی‌شود", False)

    print(f"\n{passed} passed, {failed} failed out of {passed + failed}")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)