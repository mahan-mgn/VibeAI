"""
VibeAI - Test Runner
======================

اجرای یکجای تمام تست‌های خودکار پروژه و نمایش خلاصه نهایی.

استفاده:
    cd backend
    python3 tests/run_all_tests.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests import test_analyzer, test_cache, test_database, test_recommender, test_api


def main():
    suites = [
        ("Mood Analyzer", test_analyzer.run_tests),
        ("Cache Layer", test_cache.run_tests),
        ("Database Layer", test_database.run_tests),
        ("Recommendation Engine", test_recommender.run_tests),
        ("API Endpoints", test_api.run_tests),
    ]

    results = {}

    for name, run_fn in suites:
        print(f"\n{'=' * 60}")
        print(f"  {name}")
        print(f"{'=' * 60}")
        results[name] = run_fn()

    print(f"\n{'=' * 60}")
    print("  خلاصه نهایی")
    print(f"{'=' * 60}")

    all_passed = True
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if not success:
            all_passed = False

    print()
    if all_passed:
        print("🎉 تمام مجموعه‌های تست با موفقیت پاس شدند.")
    else:
        print("⚠️  برخی مجموعه‌های تست با خطا مواجه شدند.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)