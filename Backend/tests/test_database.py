"""
Test Cases for VibeAI Database Layer
=======================================
تست‌های خودکار برای:
- Chats (ساخت چت، عنوان خودکار، جستجو)
- History (ذخیره و بازیابی تاریخچه - بخش 22-24 مستند)
- Feedback (ثبت و بازیابی بازخورد - بخش 22 مستند)
- Cache (بخش 26 مستند)
"""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import db
from cache import cache


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

    # استفاده از فایل دیتابیس موقت و جداگانه برای جلوگیری از تأثیر روی داده واقعی
    tmp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(tmp_dir, "test_vibeai.db")
    test_cache_path = os.path.join(tmp_dir, "test_cache.db")

    db.init_db(test_db_path)
    cache.init_cache_db(test_cache_path)

    # ====================================================================
    # بخش 1: Chats
    # ====================================================================

    # 1. ساخت چت بدون عنوان -> باید عنوان پیش‌فرض "چت جدید" بگیرد
    chat_id_1 = db.create_chat(title="", db_path=test_db_path)
    chat_1 = db.get_chat_by_id(chat_id_1, db_path=test_db_path)
    check("چت بدون عنوان -> عنوان پیش‌فرض 'چت جدید'", chat_1["title"] == "چت جدید")

    # 2. chat_exists برای چت موجود
    check("chat_exists برای چت موجود -> True", db.chat_exists(chat_id_1, db_path=test_db_path) is True)

    # 3. chat_exists برای چت ناموجود
    check("chat_exists برای چت ناموجود -> False", db.chat_exists(99999, db_path=test_db_path) is False)

    # 4. ذخیره اولین پیام -> باید عنوان چت را خودکار به‌روزرسانی کند
    db.save_history(
        chat_id=chat_id_1,
        user_input="امروز خیلی خسته‌ام",
        detected_mood="tired",
        detected_energy="low",
        detected_activity="general",
        detected_time_period="night",
        confidence=0.75,
        recommendations={"movies": [], "music": []},
        db_path=test_db_path,
    )
    chat_1_after = db.get_chat_by_id(chat_id_1, db_path=test_db_path)
    check("اولین پیام -> عنوان چت از روی متن پیام به‌روزرسانی می‌شود", chat_1_after["title"] == "امروز خیلی خسته‌ام")

    # 5. پیام دوم نباید عنوان را دوباره تغییر دهد
    db.save_history(
        chat_id=chat_id_1,
        user_input="دارم برنامه‌نویسی می‌کنم",
        detected_mood="neutral",
        detected_energy="medium",
        detected_activity="coding",
        detected_time_period="night",
        confidence=0.3,
        recommendations={"movies": [], "music": []},
        db_path=test_db_path,
    )
    chat_1_final = db.get_chat_by_id(chat_id_1, db_path=test_db_path)
    check("پیام دوم -> عنوان چت تغییر نمی‌کند", chat_1_final["title"] == "امروز خیلی خسته‌ام")

    # 6. تعداد پیام‌های یک چت باید درست باشد (از طریق get_history_for_chat)
    chat_1_messages = db.get_history_for_chat(chat_id_1, db_path=test_db_path)
    check("چت دارای دقیقاً 2 پیام است", len(chat_1_messages) == 2)

    # 7. ساخت یک چت دوم با عنوان دستی
    chat_id_2 = db.create_chat(title="استرس دارم خیلی", db_path=test_db_path)
    db.save_history(
        chat_id=chat_id_2,
        user_input="استرس دارم خیلی",
        detected_mood="stressed",
        detected_energy="low",
        detected_activity="general",
        detected_time_period="night",
        confidence=0.85,
        recommendations={"movies": [], "music": []},
        db_path=test_db_path,
    )

    # 8. لیست چت‌ها باید هر دو چت را برگرداند
    all_chats = db.get_chats(db_path=test_db_path)
    check("لیست چت‌ها شامل هر دو چت است", len(all_chats) == 2)

    # 9. جستجو در عنوان چت
    search_result_title = db.get_chats(search="برنامه", db_path=test_db_path)
    check("جستجو بر اساس محتوای پیام (برنامه) چت درست را پیدا می‌کند", len(search_result_title) == 1 and search_result_title[0]["id"] == chat_id_1)

    # 10. جستجو بدون نتیجه
    search_no_result = db.get_chats(search="کلمه‌ی نامرتبط xyz", db_path=test_db_path)
    check("جستجوی بدون تطابق -> نتیجه خالی", len(search_no_result) == 0)

    # ====================================================================
    # بخش 2: History (بخش 22-24 مستند)
    # ====================================================================

    # 11. get_history باید جدیدترین رکوردها را اول برگرداند
    history_list = db.get_history(limit=10, db_path=test_db_path)
    check("get_history حداقل 3 رکورد دارد (2 از چت 1 + 1 از چت 2)", len(history_list) == 3)
    check("get_history جدیدترین رکورد را اول برمی‌گرداند", history_list[0]["user_input"] == "استرس دارم خیلی")

    # 12. recommendations باید به‌صورت dict (نه رشته JSON) برگردد
    check("recommendations به‌صورت dict بازگردانده می‌شود (نه str)", isinstance(history_list[0]["recommendations"], dict))

    # 13. get_history_by_id برای رکورد موجود
    first_history_id = history_list[-1]["id"]
    single_record = db.get_history_by_id(first_history_id, db_path=test_db_path)
    check("get_history_by_id رکورد صحیح را برمی‌گرداند", single_record is not None and single_record["id"] == first_history_id)

    # 14. get_history_by_id برای رکورد ناموجود
    missing_record = db.get_history_by_id(999999, db_path=test_db_path)
    check("get_history_by_id برای id ناموجود -> None", missing_record is None)

    # ====================================================================
    # بخش 3: Feedback (بخش 22 مستند)
    # ====================================================================

    # 15. ثبت بازخورد معتبر (like)
    feedback_id = db.save_feedback(
        history_id=first_history_id, item_type="movie", item_name="فیلم تست", reaction="like", db_path=test_db_path
    )
    check("ثبت بازخورد معتبر (like) موفق است", feedback_id is not None)

    # 16. ثبت بازخورد دوم (dislike) برای آیتم دیگر
    db.save_feedback(
        history_id=first_history_id, item_type="music", item_name="آهنگ تست", reaction="dislike", db_path=test_db_path
    )

    # 17. دریافت بازخوردهای یک رکورد History
    feedbacks = db.get_feedback_for_history(first_history_id, db_path=test_db_path)
    check("دریافت بازخوردها -> دقیقاً 2 رکورد", len(feedbacks) == 2)

    # 18. item_type نامعتبر باید با ValueError رد شود
    try:
        db.save_feedback(
            history_id=first_history_id, item_type="book", item_name="x", reaction="like", db_path=test_db_path
        )
        check("item_type نامعتبر -> ValueError پرتاب می‌شود", False)
    except ValueError:
        check("item_type نامعتبر -> ValueError پرتاب می‌شود", True)

    # 19. reaction نامعتبر باید با ValueError رد شود
    try:
        db.save_feedback(
            history_id=first_history_id, item_type="movie", item_name="x", reaction="neutral", db_path=test_db_path
        )
        check("reaction نامعتبر -> ValueError پرتاب می‌شود", False)
    except ValueError:
        check("reaction نامعتبر -> ValueError پرتاب می‌شود", True)

    # 19b. history_id ناموجود باید با ValueError رد شود
    try:
        db.save_feedback(
            history_id=999999, item_type="movie", item_name="x", reaction="like", db_path=test_db_path
        )
        check("history_id ناموجود -> ValueError پرتاب می‌شود", False)
    except ValueError:
        check("history_id ناموجود -> ValueError پرتاب می‌شود", True)

    # 20. خلاصه‌ی feedback باید در رکورد History به‌روزرسانی شده باشد
    updated_history = db.get_history_by_id(first_history_id, db_path=test_db_path)
    check("فیلد feedback در History به‌روزرسانی شده است", updated_history["feedback"] is not None)

    # ====================================================================
    # بخش 4: Cache (بخش 26 مستند)
    # ====================================================================

    # 21. کش خالی در ابتدا
    cache_key = cache.build_cache_key("test", ["a", "b"])
    check("کش خالی قبل از set -> None", cache.get_cached(cache_key, db_path=test_cache_path) is None)

    # 22. ذخیره و بازیابی از کش
    cache.set_cached(cache_key, {"data": "value"}, ttl_hours=1, db_path=test_cache_path)
    cached_value = cache.get_cached(cache_key, db_path=test_cache_path)
    check("بازیابی مقدار کش‌شده صحیح است", cached_value == {"data": "value"})

    # 23. انقضای کش بعد از گذشت TTL
    short_key = cache.build_cache_key("expiring_test")
    cache.set_cached(short_key, {"x": 1}, ttl_hours=0.0001, db_path=test_cache_path)
    time.sleep(1)
    expired_value = cache.get_cached(short_key, db_path=test_cache_path)
    check("کش بعد از انقضای TTL -> None", expired_value is None)

    # 24. کلیدهای متفاوت برای پارامترهای متفاوت
    key_a = cache.build_cache_key("movies", ["Comedy"], "fa-IR")
    key_b = cache.build_cache_key("movies", ["Drama"], "fa-IR")
    check("کلیدهای کش برای پارامترهای متفاوت یکتا هستند", key_a != key_b)

    print(f"\n{passed} passed, {failed} failed out of {passed + failed}")

    # پاکسازی فایل‌های موقت
    try:
        os.remove(test_db_path)
        os.remove(test_cache_path)
        os.rmdir(tmp_dir)
    except OSError:
        pass

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)