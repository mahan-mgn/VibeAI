"""
VibeAI - Database Layer (SQLite)
==================================

مدیریت دیتابیس SQLite شامل سه جدول اصلی:

1. Chats Table (مفهوم "چت" - هر چت شامل چند درخواست/پیام است):
   - id, title, created_at, updated_at

2. History Table (بخش 24 مستند):
   - id, chat_id, user_input, detected_mood, detected_energy, detected_activity,
     detected_time_period, confidence, recommendations, feedback, timestamp

3. Feedback Table:
   - id, history_id, item_type, item_name, reaction, timestamp
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, List, Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "vibeai.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_input TEXT NOT NULL,
    detected_mood TEXT NOT NULL,
    detected_energy TEXT NOT NULL,
    detected_activity TEXT NOT NULL,
    detected_time_period TEXT NOT NULL,
    confidence REAL NOT NULL,
    recommendations TEXT NOT NULL,
    feedback TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (chat_id) REFERENCES chats (id)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    history_id INTEGER NOT NULL,
    item_type TEXT NOT NULL,
    item_name TEXT NOT NULL,
    reaction TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (history_id) REFERENCES history (id)
);

CREATE TABLE IF NOT EXISTS taste_stats (
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (category, key)
);

CREATE INDEX IF NOT EXISTS idx_feedback_history_id ON feedback (history_id);
CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history (timestamp);
CREATE INDEX IF NOT EXISTS idx_history_chat_id ON history (chat_id);
CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON chats (updated_at);
"""


# ----------------------------------------------------------------------
# Connection Management
# ----------------------------------------------------------------------
@contextmanager
def get_connection(db_path: str = DB_PATH):
    """
    Context manager برای اتصال به دیتابیس SQLite.
    اتصال را پس از استفاده می‌بندد و در صورت خطا rollback می‌کند.
    """
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


def init_db(db_path: str = DB_PATH) -> None:
    """ایجاد جداول دیتابیس در صورت عدم وجود."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------------
# Chat Operations
# ----------------------------------------------------------------------
MAX_TITLE_LENGTH = 60


def _derive_title(text: str) -> str:
    """ساخت عنوان چت از روی اولین پیام کاربر (کوتاه‌شده)."""
    text = " ".join(text.strip().split())
    if len(text) <= MAX_TITLE_LENGTH:
        return text
    return text[:MAX_TITLE_LENGTH].rstrip() + "…"


def create_chat(title: str, db_path: str = DB_PATH) -> int:
    """ساخت یک چت جدید و بازگرداندن id آن."""
    now = _now_iso()
    title = _derive_title(title) if title else "چت جدید"

    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO chats (title, created_at, updated_at) VALUES (?, ?, ?)",
            (title, now, now),
        )
        return cursor.lastrowid


def get_chats(limit: int = 50, offset: int = 0, search: Optional[str] = None, db_path: str = DB_PATH) -> List[Dict]:
    """
    دریافت لیست چت‌ها (جدیدترین بر اساس آخرین فعالیت در ابتدا).

    search: در صورت ارسال، عنوان چت یا متن پیام‌های آن باید شامل این عبارت باشد
    (برای قابلیت "جستجوی چت").
    """
    with get_connection(db_path) as conn:
        if search:
            pattern = f"%{search.strip()}%"
            rows = conn.execute(
                """
                SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at
                FROM chats c
                LEFT JOIN history h ON h.chat_id = c.id
                WHERE c.title LIKE ? OR h.user_input LIKE ?
                ORDER BY c.updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (pattern, pattern, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM chats
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

    return [dict(row) for row in rows]


def get_chat_by_id(chat_id: int, db_path: str = DB_PATH) -> Optional[Dict]:
    """دریافت اطلاعات یک چت بر اساس id."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM chats WHERE id = ?",
            (chat_id,),
        ).fetchone()

    return dict(row) if row else None


def chat_exists(chat_id: int, db_path: str = DB_PATH) -> bool:
    """بررسی وجود یک چت."""
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT id FROM chats WHERE id = ?", (chat_id,)).fetchone()
    return row is not None


def _touch_chat(conn: sqlite3.Connection, chat_id: int) -> None:
    """به‌روزرسانی updated_at یک چت (برای مرتب‌سازی بر اساس آخرین فعالیت)."""
    conn.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (_now_iso(), chat_id))


def _maybe_update_title_from_first_message(conn: sqlite3.Connection, chat_id: int, user_input: str) -> None:
    """
    اگر این اولین پیام یک چت با عنوان پیش‌فرض («چت جدید») باشد،
    عنوان چت را از روی متن همین پیام به‌روزرسانی می‌کند.
    """
    row = conn.execute("SELECT title FROM chats WHERE id = ?", (chat_id,)).fetchone()
    if row is None:
        return

    if row["title"] != "چت جدید":
        return

    message_count = conn.execute(
        "SELECT COUNT(*) as c FROM history WHERE chat_id = ?", (chat_id,)
    ).fetchone()["c"]

    # اگر این رکورد، اولین پیام چت است (قبل از insert فعلی تعداد صفر بوده)
    if message_count == 0:
        conn.execute(
            "UPDATE chats SET title = ? WHERE id = ?",
            (_derive_title(user_input), chat_id),
        )


# ----------------------------------------------------------------------
# History Operations
# ----------------------------------------------------------------------
def save_history(
    chat_id: int,
    user_input: str,
    detected_mood: str,
    detected_energy: str,
    detected_activity: str,
    detected_time_period: str,
    confidence: float,
    recommendations: Dict,
    db_path: str = DB_PATH,
) -> int:
    """
    ذخیره یک رکورد History برای یک چت مشخص و بازگرداندن id آن.

    recommendations: دیکشنری شامل لیست فیلم‌ها و موزیک‌های پیشنهادی
    (به صورت JSON serialize می‌شود).
    """
    recommendations_json = json.dumps(recommendations, ensure_ascii=False)

    with get_connection(db_path) as conn:
        _maybe_update_title_from_first_message(conn, chat_id, user_input)

        cursor = conn.execute(
            """
            INSERT INTO history (
                chat_id, user_input, detected_mood, detected_energy, detected_activity,
                detected_time_period, confidence, recommendations, feedback, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
            """,
            (
                chat_id,
                user_input,
                detected_mood,
                detected_energy,
                detected_activity,
                detected_time_period,
                confidence,
                recommendations_json,
                _now_iso(),
            ),
        )

        _touch_chat(conn, chat_id)

        return cursor.lastrowid


def get_history_for_chat(chat_id: int, db_path: str = DB_PATH) -> List[Dict]:
    """
    دریافت تمام پیام‌ها/درخواست‌های یک چت به ترتیب زمانی (قدیمی -> جدید)،
    برای بازسازی کامل صفحه‌ی چت.
    """
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, chat_id, user_input, detected_mood, detected_energy, detected_activity,
                   detected_time_period, confidence, recommendations, feedback, timestamp
            FROM history
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (chat_id,),
        ).fetchall()

    return [_deserialize_history_row(row) for row in rows]


def _deserialize_history_row(row: sqlite3.Row) -> Dict:
    item = dict(row)
    try:
        item["recommendations"] = json.loads(item["recommendations"])
    except (json.JSONDecodeError, TypeError):
        item["recommendations"] = {}

    try:
        item["feedback"] = json.loads(item["feedback"]) if item["feedback"] else []
    except (json.JSONDecodeError, TypeError):
        item["feedback"] = []

    return item


def get_history(limit: int = 50, offset: int = 0, db_path: str = DB_PATH) -> List[Dict]:
    """
    دریافت تاریخچه‌ی درخواست‌ها در کل سیستم (جدیدترین در ابتدا).
    (برای مصارف عمومی/گزارش‌گیری - مستقل از چت)
    """
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, chat_id, user_input, detected_mood, detected_energy, detected_activity,
                   detected_time_period, confidence, recommendations, feedback, timestamp
            FROM history
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    return [_deserialize_history_row(row) for row in rows]


def get_history_by_id(history_id: int, db_path: str = DB_PATH) -> Optional[Dict]:
    """دریافت یک رکورد History بر اساس id."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, chat_id, user_input, detected_mood, detected_energy, detected_activity,
                   detected_time_period, confidence, recommendations, feedback, timestamp
            FROM history
            WHERE id = ?
            """,
            (history_id,),
        ).fetchone()

    if row is None:
        return None

    return _deserialize_history_row(row)


# ----------------------------------------------------------------------
# Feedback Operations
# ----------------------------------------------------------------------
VALID_REACTIONS = {"like", "dislike"}
VALID_ITEM_TYPES = {"movie", "music"}


def save_feedback(
    history_id: int,
    item_type: str,
    item_name: str,
    reaction: str,
    db_path: str = DB_PATH,
) -> int:
    """
    ذخیره یک بازخورد (لایک/دیسلایک) برای یک آیتم پیشنهادی.

    item_type: "movie" یا "music"
    reaction: "like" یا "dislike"

    همچنین فیلد feedback در جدول history به‌روزرسانی می‌شود (آخرین بازخورد).
    """
    if item_type not in VALID_ITEM_TYPES:
        raise ValueError(f"item_type باید یکی از {VALID_ITEM_TYPES} باشد.")

    if reaction not in VALID_REACTIONS:
        raise ValueError(f"reaction باید یکی از {VALID_REACTIONS} باشد.")

    with get_connection(db_path) as conn:
        # بررسی وجود history_id
        history_row = conn.execute("SELECT id FROM history WHERE id = ?", (history_id,)).fetchone()
        if history_row is None:
            raise ValueError(f"رکورد History با id={history_id} یافت نشد.")

        cursor = conn.execute(
            """
            INSERT INTO feedback (history_id, item_type, item_name, reaction, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (history_id, item_type, item_name, reaction, _now_iso()),
        )

        # به‌روزرسانی فیلد feedback در جدول history (لیست کامل بازخوردهای این رکورد)
        all_feedback_rows = conn.execute(
            "SELECT item_type, item_name, reaction, timestamp FROM feedback WHERE history_id = ? ORDER BY id ASC",
            (history_id,),
        ).fetchall()
        feedback_summary = json.dumps([dict(f) for f in all_feedback_rows], ensure_ascii=False)
        conn.execute("UPDATE history SET feedback = ? WHERE id = ?", (feedback_summary, history_id))

        feedback_id = cursor.lastrowid

    # به‌روزرسانی پروفایل ذائقه (بخش شخصی‌سازی) - نباید در صورت خطا ثبت بازخورد را خراب کند
    try:
        _update_taste_profile(history_id, item_type, item_name, reaction, db_path)
    except Exception:
        pass

    return feedback_id


def _update_taste_profile(history_id: int, item_type: str, item_name: str, reaction: str, db_path: str) -> None:
    """
    استخراج ژانر آیتم لایک/دیسلایک‌شده از history.recommendations و ثبت سیگنال سلیقه.
    """
    history = get_history_by_id(history_id, db_path)
    if history is None:
        return

    delta = 1.0 if reaction == "like" else -1.0
    recommendations = history.get("recommendations", {})

    if item_type == "movie":
        movie = next((m for m in recommendations.get("movies", []) if m.get("title") == item_name), None)
        if movie:
            for genre in movie.get("genres", []):
                record_taste_signal("movie_genre", genre, delta, db_path)
    elif item_type == "music":
        song = next((s for s in recommendations.get("music", []) if s.get("title") == item_name), None)
        if song and song.get("genre"):
            record_taste_signal("music_genre", song["genre"], delta, db_path)


def get_feedback_for_history(history_id: int, db_path: str = DB_PATH) -> List[Dict]:
    """دریافت تمام بازخوردهای ثبت‌شده برای یک رکورد History."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, history_id, item_type, item_name, reaction, timestamp
            FROM feedback
            WHERE history_id = ?
            ORDER BY id ASC
            """,
            (history_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def count_feedback(db_path: str = DB_PATH) -> int:
    """تعداد کل بازخوردهای ثبت‌شده در کل سیستم."""
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM feedback").fetchone()
    return row["c"]


# ----------------------------------------------------------------------
# Taste Profile Operations (شخصی‌سازی یادگیرنده بر اساس بازخورد)
# ----------------------------------------------------------------------
def record_taste_signal(category: str, key: str, delta: float, db_path: str = DB_PATH) -> None:
    """
    ثبت/به‌روزرسانی امتیاز سلیقه برای یک ژانر (category: "movie_genre" یا "music_genre").

    هر لایک امتیاز را افزایش و هر دیسلایک آن را کاهش می‌دهد؛ امتیاز به‌صورت
    تجمعی نگه‌داری می‌شود تا با گذر زمان سلیقه‌ی کاربر یاد گرفته شود.
    """
    now = _now_iso()
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO taste_stats (category, key, score, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(category, key) DO UPDATE SET
                score = score + excluded.score,
                updated_at = excluded.updated_at
            """,
            (category, key, delta, now),
        )


def get_taste_profile(db_path: str = DB_PATH) -> Dict[str, Dict[str, float]]:
    """دریافت پروفایل ذائقه‌ی یادگرفته‌شده، گروه‌بندی‌شده بر اساس category."""
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT category, key, score FROM taste_stats").fetchall()

    profile: Dict[str, Dict[str, float]] = {}
    for row in rows:
        profile.setdefault(row["category"], {})[row["key"]] = row["score"]
    return profile


if __name__ == "__main__":
    # تست سریع
    init_db()

    chat_id = create_chat("امروز خیلی خسته‌ام و یه فیلم سبک می‌خوام")
    print(f"Chat created with id={chat_id}")

    history_id = save_history(
        chat_id=chat_id,
        user_input="امروز خیلی خسته‌ام و یه فیلم سبک می‌خوام",
        detected_mood="tired",
        detected_energy="low",
        detected_activity="general",
        detected_time_period="night",
        confidence=0.74,
        recommendations={"movies": [{"title": "زندگی زیباست"}], "music": [{"title": "Night Owl"}]},
    )
    print(f"History saved with id={history_id}")

    feedback_id = save_feedback(history_id, "movie", "زندگی زیباست", "like")
    print(f"Feedback saved with id={feedback_id}")

    print(json.dumps(get_history(limit=5), ensure_ascii=False, indent=2))
    print(json.dumps(get_feedback_for_history(history_id), ensure_ascii=False, indent=2))