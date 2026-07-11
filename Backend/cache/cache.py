"""
VibeAI - Cache Layer (SQLite)
================================

پیاده‌سازی Cache Strategy طبق بخش 26 مستند:

مدت اعتبار: 24 ساعت

مراحل:
Check Cache -> If Found -> Return Cache
            -> Else -> TMDB -> Save Cache

این لایه برای جلوگیری از فراخوانی‌های تکراری به TMDB API استفاده می‌شود
(صرفه‌جویی در Rate Limit و افزایش سرعت پاسخ‌دهی - بخش 30 مستند:
Response Time < 3 Seconds).
"""

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), "cache.db")

CACHE_TTL_HOURS = 24


SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    cache_key TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache (expires_at);
"""


@contextmanager
def get_connection(db_path: str = CACHE_DB_PATH):
    """Context manager برای اتصال به دیتابیس کش."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_cache_db(db_path: str = CACHE_DB_PATH) -> None:
    """ساخت جدول کش در صورت عدم وجود."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_cache_key(*parts: Any) -> str:
    """
    ساخت یک کلید یکتا برای کش بر اساس پارامترهای ورودی
    (مثلا نوع درخواست + لیست ژانرها + زبان).
    """
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached(cache_key: str, db_path: str = CACHE_DB_PATH) -> Optional[Any]:
    """
    دریافت مقدار کش‌شده در صورت معتبر بودن (هنوز منقضی نشده).

    خروجی: مقدار deserialize شده، یا None در صورت نبود/انقضا/خطا.
    سیستم نباید Crash کند (بخش 27 مستند) -> هرگونه خطای دیتابیس
    باعث Fallback به None (یعنی رفتن به سراغ منبع اصلی) می‌شود.
    """
    try:
        with get_connection(db_path) as conn:
            row = conn.execute(
                "SELECT payload, expires_at FROM cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
    except sqlite3.Error:
        return None

    if row is None:
        return None

    expires_at = datetime.fromisoformat(row["expires_at"])
    if _now() >= expires_at:
        # منقضی شده - حذف رکورد قدیمی (best-effort)
        _delete_cache_entry(cache_key, db_path)
        return None

    try:
        return json.loads(row["payload"])
    except (json.JSONDecodeError, TypeError):
        return None


def set_cached(cache_key: str, value: Any, ttl_hours: int = CACHE_TTL_HOURS, db_path: str = CACHE_DB_PATH) -> bool:
    """
    ذخیره مقدار در کش با مدت اعتبار مشخص (پیش‌فرض 24 ساعت).

    خروجی: True در صورت موفقیت، False در صورت خطا (بدون Crash کردن سیستم).
    """
    now = _now()
    expires_at = now + timedelta(hours=ttl_hours)
    payload = json.dumps(value, ensure_ascii=False)

    try:
        with get_connection(db_path) as conn:
            conn.execute(
                """
                INSERT INTO cache (cache_key, payload, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    payload = excluded.payload,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
                """,
                (cache_key, payload, now.isoformat(), expires_at.isoformat()),
            )
        return True
    except sqlite3.Error:
        return False


def _delete_cache_entry(cache_key: str, db_path: str = CACHE_DB_PATH) -> None:
    try:
        with get_connection(db_path) as conn:
            conn.execute("DELETE FROM cache WHERE cache_key = ?", (cache_key,))
    except sqlite3.Error:
        pass


def clear_expired(db_path: str = CACHE_DB_PATH) -> int:
    """
    حذف تمام رکوردهای منقضی‌شده از کش (برای پاکسازی دوره‌ای).
    خروجی: تعداد رکوردهای حذف‌شده.
    """
    try:
        with get_connection(db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at <= ?",
                (_now().isoformat(),),
            )
            return cursor.rowcount
    except sqlite3.Error:
        return 0


def clear_all(db_path: str = CACHE_DB_PATH) -> bool:
    """پاکسازی کامل کش (برای تست یا دستورات مدیریتی)."""
    try:
        with get_connection(db_path) as conn:
            conn.execute("DELETE FROM cache")
        return True
    except sqlite3.Error:
        return False


if __name__ == "__main__":
    import time

    init_cache_db()
    clear_all()

    key = build_cache_key("movies", ["Comedy", "Family"], "fa-IR")

    print("Before set:", get_cached(key))

    set_cached(key, {"results": ["فیلم تستی"]}, ttl_hours=1)
    print("After set:", get_cached(key))

    # تست انقضا با TTL خیلی کوتاه
    short_key = build_cache_key("test_expiry")
    set_cached(short_key, {"x": 1}, ttl_hours=0.0001)  # چند میلی‌ثانیه
    time.sleep(1)
    print("After expiry:", get_cached(short_key))