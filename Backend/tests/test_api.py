"""
Test Cases for VibeAI API Endpoints (app.py)
تست‌های end-to-end برای:
- POST /api/analyze
- POST /api/chats, GET /api/chats, GET /api/chats/{id}
- POST /api/recommend (شامل مدل چت/پیام)
- POST /api/feedback
- GET  /api/history
- Rate Limiting (بخش 31 مستند)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


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

    # دیتابیس و کش را به فایل‌های موقت/تستی هدایت می‌کنیم تا با داده واقعی تداخل نکند
    import tempfile

    tmp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(tmp_dir, "test_vibeai.db")
    test_cache_path = os.path.join(tmp_dir, "test_cache.db")

    from database import db
    from cache import cache

    # Monkey-patch مسیرهای پیش‌فرض قبل از import شدن app (تا app از همین مسیرها استفاده کند)
    db.DB_PATH = test_db_path
    cache.CACHE_DB_PATH = test_cache_path

    from fastapi.testclient import TestClient
    from app import app

    client = TestClient(app)

    # ====================================================================
    # بخش 1: /api/analyze
    # ====================================================================

    resp = client.post("/api/analyze", json={"text": "امروز خیلی خسته‌ام"})
    check("POST /api/analyze -> status 200", resp.status_code == 200)
    data = resp.json()
    check("analyze -> mood صحیح تشخیص داده شود", data.get("mood") == "tired")
    check(
        "analyze -> تمام فیلدهای مورد انتظار موجود است",
        all(k in data for k in ["mood", "moods", "energy", "activity", "time_period", "confidence", "negations_detected", "safety_layer_active"]),
    )

    # ورودی خالی -> خطای 422 (validation)
    resp_empty = client.post("/api/analyze", json={"text": ""})
    check("analyze با متن خالی -> خطای 422", resp_empty.status_code == 422)

    # ورودی بیش از حد طولانی -> خطای 422
    resp_long = client.post("/api/analyze", json={"text": "ا" * 600})
    check("analyze با متن طولانی‌تر از 500 کاراکتر -> خطای 422", resp_long.status_code == 422)

    # ====================================================================
    # بخش 2: /api/chats
    # ====================================================================

    resp_new_chat = client.post("/api/chats", json={})
    check("POST /api/chats بدون عنوان -> status 200", resp_new_chat.status_code == 200)
    manual_chat = resp_new_chat.json()
    check("چت دستی -> عنوان پیش‌فرض 'چت جدید'", manual_chat["title"] == "چت جدید")

    resp_list_chats = client.get("/api/chats")
    check("GET /api/chats -> status 200", resp_list_chats.status_code == 200)
    check("لیست چت‌ها شامل چت ساخته‌شده است", any(c["id"] == manual_chat["id"] for c in resp_list_chats.json()))

    # ====================================================================
    # بخش 3: /api/recommend (مدل چت + پیام)
    # ====================================================================

    resp_rec1 = client.post("/api/recommend", json={"text": "امروز خیلی خسته‌ام و یه فیلم سبک می‌خوام"})
    check("POST /api/recommend (چت جدید) -> status 200", resp_rec1.status_code == 200)
    rec1_data = resp_rec1.json()
    chat_id = rec1_data["chat_id"]
    history_id = rec1_data["history_id"]

    check("recommend -> history_id معتبر برمی‌گرداند", history_id is not None and history_id > 0)
    check("recommend -> حداکثر 5 فیلم برمی‌گرداند", len(rec1_data["movies"]) <= 5)
    check("recommend -> حداکثر 10 موزیک برمی‌گرداند", len(rec1_data["music"]) <= 10)
    check(
        "recommend -> هر فیلم دارای reasoning است",
        all(len(m["reasoning"]) > 0 for m in rec1_data["movies"]),
    )

    # پیام دوم در همان چت
    resp_rec2 = client.post("/api/recommend", json={"text": "دارم برنامه‌نویسی می‌کنم", "chat_id": chat_id})
    check("POST /api/recommend (پیام دوم، همان چت) -> status 200", resp_rec2.status_code == 200)
    check("پیام دوم در همان chat_id ذخیره می‌شود", resp_rec2.json()["chat_id"] == chat_id)

    # چت با chat_id ناموجود -> خطای 404
    resp_rec_bad_chat = client.post("/api/recommend", json={"text": "سلام", "chat_id": 999999})
    check("recommend با chat_id ناموجود -> خطای 404", resp_rec_bad_chat.status_code == 404)

    # دریافت کامل چت با هر دو پیام
    resp_chat_detail = client.get(f"/api/chats/{chat_id}")
    check("GET /api/chats/{id} -> status 200", resp_chat_detail.status_code == 200)
    chat_detail = resp_chat_detail.json()
    check("چت دارای دقیقاً 2 پیام است", len(chat_detail["messages"]) == 2)

    # چت ناموجود -> 404
    resp_chat_missing = client.get("/api/chats/999999")
    check("GET /api/chats/{id} برای چت ناموجود -> خطای 404", resp_chat_missing.status_code == 404)

    # ====================================================================
    # بخش 4: /api/feedback
    # ====================================================================

    movie_name = rec1_data["movies"][0]["title"] if rec1_data["movies"] else None
    if movie_name:
        resp_feedback = client.post(
            "/api/feedback",
            json={"history_id": history_id, "item_type": "movie", "item_name": movie_name, "reaction": "like"},
        )
        check("POST /api/feedback (like) -> status 200", resp_feedback.status_code == 200)

    # item_type نامعتبر -> خطای 400
    resp_bad_feedback = client.post(
        "/api/feedback",
        json={"history_id": history_id, "item_type": "book", "item_name": "x", "reaction": "like"},
    )
    check("feedback با item_type نامعتبر -> خطای 400", resp_bad_feedback.status_code == 400)

    # reaction نامعتبر -> خطای 400
    resp_bad_reaction = client.post(
        "/api/feedback",
        json={"history_id": history_id, "item_type": "movie", "item_name": "x", "reaction": "neutral"},
    )
    check("feedback با reaction نامعتبر -> خطای 400", resp_bad_reaction.status_code == 400)

    # history_id ناموجود -> خطای 404
    resp_missing_history = client.post(
        "/api/feedback",
        json={"history_id": 999999, "item_type": "movie", "item_name": "x", "reaction": "like"},
    )
    check("feedback با history_id ناموجود -> خطای 404", resp_missing_history.status_code == 404)

    # ====================================================================
    # بخش 5: /api/history
    # ====================================================================

    resp_history = client.get("/api/history")
    check("GET /api/history -> status 200", resp_history.status_code == 200)
    check("history شامل حداقل 2 رکورد است", len(resp_history.json()) >= 2)

    # ====================================================================
    # بخش 6: جستجوی چت‌ها (search)
    # ====================================================================

    resp_search = client.get("/api/chats?search=برنامه")
    check("جستجوی چت با کلمه‌ی موجود -> نتیجه پیدا می‌شود", resp_search.status_code == 200 and len(resp_search.json()) >= 1)

    resp_search_none = client.get("/api/chats?search=کلمه‌ی‌نامرتبط‌xyz")
    check("جستجوی چت با کلمه‌ی نامرتبط -> نتیجه خالی", len(resp_search_none.json()) == 0)

    # ====================================================================
    # بخش 7: Rate Limiting (بخش 31 مستند: 30 Request/Minute)
    # ====================================================================

    success_count = 0
    rate_limited_count = 0
    for _ in range(35):
        r = client.get("/api/history")
        if r.status_code == 200:
            success_count += 1
        elif r.status_code == 429:
            rate_limited_count += 1

    check("Rate Limiting: حداکثر 30 درخواست موفق در دقیقه", success_count <= 30)
    check("Rate Limiting: درخواست‌های بیش از حد با 429 رد می‌شوند", rate_limited_count > 0)

    print(f"\n{passed} passed, {failed} failed out of {passed + failed}")

    # پاکسازی
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