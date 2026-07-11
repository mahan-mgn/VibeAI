"""
Test Cases for VibeAI Cache Layer (cache/cache.py)
تست Cache Strategy طبق بخش 26 مستند: TTL 24 ساعته، Cache Hit/Miss
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cache import cache

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_cache.db")


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

    # پاکسازی قبل از شروع تست‌ها (دیتابیس تستی مجزا از دیتابیس اصلی)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    cache.init_cache_db(db_path=TEST_DB_PATH)

    # 1. build_cache_key: کلیدهای یکسان برای ورودی‌های یکسان
    key1 = cache.build_cache_key("movies", ["Comedy", "Family"], "fa-IR")
    key2 = cache.build_cache_key("movies", ["Comedy", "Family"], "fa-IR")
    check("build_cache_key برای ورودی یکسان، کلید یکسان می‌سازد", key1 == key2)

    # 2. build_cache_key: کلیدهای متفاوت برای ورودی‌های متفاوت
    key3 = cache.build_cache_key("movies", ["Action"], "fa-IR")
    check("build_cache_key برای ورودی متفاوت، کلید متفاوت می‌سازد", key1 != key3)

    # 3. Cache Miss: مقدار نامعتبر/ناموجود -> None
    check(
        "Cache Miss برای کلید ناموجود -> None",
        cache.get_cached("nonexistent_key_xyz", db_path=TEST_DB_PATH) is None,
    )

    # 4. Set + Get: ذخیره و بازیابی مقدار
    test_key = cache.build_cache_key("test_set_get")
    saved = cache.set_cached(test_key, {"results": ["فیلم تستی"]}, db_path=TEST_DB_PATH)
    check("set_cached با موفقیت ذخیره می‌کند", saved is True)

    retrieved = cache.get_cached(test_key, db_path=TEST_DB_PATH)
    check("get_cached مقدار ذخیره‌شده را برمی‌گرداند", retrieved == {"results": ["فیلم تستی"]})

    # 5. TTL: مقدار با TTL منقضی‌شده باید None برگرداند
    short_ttl_key = cache.build_cache_key("test_short_ttl")
    cache.set_cached(short_ttl_key, {"x": 1}, ttl_hours=0.0002, db_path=TEST_DB_PATH)  # ~0.7 ثانیه
    time.sleep(1.2)
    check(
        "مقدار با TTL منقضی‌شده -> None برمی‌گرداند",
        cache.get_cached(short_ttl_key, db_path=TEST_DB_PATH) is None,
    )

    # 6. TTL پیش‌فرض باید 24 ساعت باشد (طبق بخش 26 مستند)
    check("CACHE_TTL_HOURS پیش‌فرض برابر 24 است", cache.CACHE_TTL_HOURS == 24)

    # 7. Overwrite: ذخیره دوباره با همان کلید باید مقدار را به‌روزرسانی کند
    overwrite_key = cache.build_cache_key("test_overwrite")
    cache.set_cached(overwrite_key, {"version": 1}, db_path=TEST_DB_PATH)
    cache.set_cached(overwrite_key, {"version": 2}, db_path=TEST_DB_PATH)
    check(
        "ذخیره دوباره با همان کلید، مقدار قبلی را به‌روزرسانی می‌کند",
        cache.get_cached(overwrite_key, db_path=TEST_DB_PATH) == {"version": 2},
    )

    # 8. clear_expired: فقط رکوردهای منقضی‌شده را حذف می‌کند
    cache.clear_all(db_path=TEST_DB_PATH)
    valid_key = cache.build_cache_key("valid_entry")
    expired_key = cache.build_cache_key("expired_entry")
    cache.set_cached(valid_key, {"ok": True}, ttl_hours=24, db_path=TEST_DB_PATH)
    cache.set_cached(expired_key, {"ok": False}, ttl_hours=0.0002, db_path=TEST_DB_PATH)
    time.sleep(1.2)

    removed_count = cache.clear_expired(db_path=TEST_DB_PATH)
    check("clear_expired حداقل یک رکورد منقضی‌شده را حذف می‌کند", removed_count >= 1)
    check(
        "بعد از clear_expired، رکورد معتبر همچنان باقی می‌ماند",
        cache.get_cached(valid_key, db_path=TEST_DB_PATH) == {"ok": True},
    )

    # 9. clear_all: پاکسازی کامل کش
    cache.clear_all(db_path=TEST_DB_PATH)
    check(
        "clear_all تمام رکوردها را پاک می‌کند",
        cache.get_cached(valid_key, db_path=TEST_DB_PATH) is None,
    )

    # 10. مدیریت خطا: مسیر دیتابیس نامعتبر نباید Crash کند (بخش 27 مستند)
    try:
        result = cache.get_cached("any_key", db_path="/nonexistent/dir/cache.db")
        check("مسیر دیتابیس نامعتبر باعث Crash نمی‌شود (get)", result is None)
    except Exception:
        check("مسیر دیتابیس نامعتبر باعث Crash نمی‌شود (get)", False)

    try:
        result = cache.set_cached("any_key", {"x": 1}, db_path="/nonexistent/dir/cache.db")
        check("مسیر دیتابیس نامعتبر باعث Crash نمی‌شود (set)", result is False)
    except Exception:
        check("مسیر دیتابیس نامعتبر باعث Crash نمی‌شود (set)", False)

    # پاکسازی نهایی
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    print(f"\n{passed} passed, {failed} failed out of {passed + failed}")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)