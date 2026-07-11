"""
VibeAI - FastAPI Backend
==========================

اپلیکیشن اصلی FastAPI که Mood Analysis Engine و Recommendation Engine
را به صورت API ارائه می‌دهد.

مفهوم "چت" (Chat): هر چت یک Session مستقل است که شامل چند پیام/درخواست
(History Records) می‌شود. این امکان را می‌دهد که نتایج هر پیام در همان
صفحه‌ی چت نمایش داده شود.

Endpoints:
- POST /api/analyze       -> تحلیل متن فارسی و تشخیص mood/energy/activity/time
- POST /api/chats          -> ساخت چت جدید
- GET  /api/chats          -> لیست چت‌ها (با قابلیت جستجو)
- GET  /api/chats/{id}      -> دریافت یک چت همراه با تمام پیام‌های آن
- POST /api/recommend      -> تحلیل + پیشنهاد فیلم و موسیقی در قالب یک پیام از یک چت
- POST /api/feedback       -> ثبت لایک/دیسلایک
- GET  /api/history         -> تاریخچه کلی (مستقل از چت)
"""

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# بارگذاری متغیرهای محیطی از فایل .env (مثلا TMDB_API_KEY)
load_dotenv()

from mood.hybrid_analyzer import get_hybrid_analyzer
from recommender.movie import MovieRecommender, TOP_N_MOVIES
from recommender.music import MusicRecommender, TOP_N_SONGS
from database import db
from cache import cache


# ----------------------------------------------------------------------
# Rate Limiter (بخش 31 مستند: 30 Request/Minute)
# ----------------------------------------------------------------------
RATE_LIMIT = "30/minute"
limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT])


def _rate_limit_handler_fa(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """پیام خطای فارسی و کاربرپسند برای عبور از محدودیت نرخ درخواست."""
    return JSONResponse(
        status_code=429,
        content={"detail": "تعداد درخواست‌های شما بیش از حد مجاز است (حداکثر ۳۰ درخواست در دقیقه). لطفاً کمی صبر کنید و دوباره تلاش کنید."},
    )


# ----------------------------------------------------------------------
# App Initialization
# ----------------------------------------------------------------------
app = FastAPI(
    title="VibeAI API",
    description="AI-Powered Mood-Based Entertainment Assistant",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler_fa)

# CORS برای دسترسی Frontend (HTML/CSS/JS) به API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# نمونه‌ی واحد از Hybrid Analyzer (Gemini + Rule-Based Fallback)
analyzer = get_hybrid_analyzer()

# نمونه‌ی واحد از Movie و Music Recommender
movie_recommender = MovieRecommender()
music_recommender = MusicRecommender()

# ایجاد جداول دیتابیس (در صورت عدم وجود) - بخش 24 مستند
db.init_db()

# ایجاد جدول Cache (در صورت عدم وجود) - بخش 26 مستند
cache.init_cache_db()


# ----------------------------------------------------------------------
# Security Rules (بخش 31 مستند)
# ----------------------------------------------------------------------
MAX_INPUT_LENGTH = 500


# ----------------------------------------------------------------------
# Content-Type Intent Detection (فقط فیلم / فقط موزیک)
# ----------------------------------------------------------------------
# اگر کاربر صراحتاً فقط یکی از این دو نوع محتوا را بخواهد، فقط همان نوع
# پیشنهاد داده می‌شود و تعداد پیشنهادها در آن حالت بیشتر می‌شود.
MOVIE_ONLY_KEYWORDS = ["فیلم", "سینما", "سینمایی"]
MUSIC_ONLY_KEYWORDS = ["موزیک", "موسیقی", "آهنگ", "ترانه"]

MOVIE_FOCUSED_TOP_N = 10
MUSIC_FOCUSED_TOP_N = 15


def _detect_content_intent(text: str) -> str:
    """
    تشخیص می‌دهد کاربر فقط «فیلم» می‌خواهد، فقط «موزیک» می‌خواهد یا هیچ‌کدام
    را صراحتاً درخواست نکرده (در این صورت هر دو نوع مثل قبل پیشنهاد می‌شود).
    """
    wants_movie = any(kw in text for kw in MOVIE_ONLY_KEYWORDS)
    wants_music = any(kw in text for kw in MUSIC_ONLY_KEYWORDS)

    if wants_movie and not wants_music:
        return "movie"
    if wants_music and not wants_movie:
        return "music"
    return "both"


# ----------------------------------------------------------------------
# Request / Response Models
# ----------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=MAX_INPUT_LENGTH,
        description="متن فارسی کاربر برای تحلیل احساسات",
        examples=["امروز خیلی خسته‌ام و یه فیلم سبک می‌خوام"],
    )


class AnalyzeResponse(BaseModel):
    mood: str
    moods: dict
    energy: str
    activity: str
    time_period: str
    confidence: float
    negations_detected: list[str]
    safety_layer_active: bool
    analyzer: str = "rule_based"   # "gemini" | "rule_based" | "fallback"


class RecommendRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=MAX_INPUT_LENGTH,
        description="متن فارسی کاربر برای تحلیل احساسات و پیشنهاد محتوا",
        examples=["امروز خیلی خسته‌ام و یه فیلم سبک می‌خوام"],
    )
    chat_id: int | None = Field(
        default=None,
        description="شناسه‌ی چت موجود. در صورت ارسال نشدن، یک چت جدید ساخته می‌شود.",
    )


class MovieItem(BaseModel):
    title: str
    genres: list[str]
    rating: float
    overview: str
    poster_path: str | None
    final_score: float
    reasoning: list[str]
    source: str


class MusicItem(BaseModel):
    title: str
    artist: str
    genre: str
    youtube_link: str
    final_score: float
    reasoning: list[str]
    spotify_url: str | None = None
    spotify_preview_url: str | None = None
    album_image: str | None = None


class RecommendResponse(BaseModel):
    chat_id: int
    history_id: int
    analysis: AnalyzeResponse
    movies: list[MovieItem]
    music: list[MusicItem]


class FeedbackRequest(BaseModel):
    history_id: int = Field(..., description="شناسه‌ی رکورد History مرتبط")
    item_type: str = Field(..., description="نوع آیتم: movie یا music")
    item_name: str = Field(..., description="نام آیتم (عنوان فیلم/آهنگ)")
    reaction: str = Field(..., description="واکنش کاربر: like یا dislike")


class FeedbackResponse(BaseModel):
    id: int
    history_id: int
    item_type: str
    item_name: str
    reaction: str
    timestamp: str


class FeedbackEntry(BaseModel):
    item_type: str
    item_name: str
    reaction: str
    timestamp: str


class HistoryItem(BaseModel):
    id: int
    chat_id: int
    user_input: str
    detected_mood: str
    detected_energy: str
    detected_activity: str
    detected_time_period: str
    confidence: float
    recommendations: dict
    feedback: list[FeedbackEntry]
    timestamp: str


class ChatSummary(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str


class ChatDetail(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str
    messages: list[HistoryItem]


class GenreScore(BaseModel):
    genre: str
    score: float


class TasteProfileResponse(BaseModel):
    movie_genres: list[GenreScore]
    music_genres: list[GenreScore]
    total_feedback: int


class CreateChatRequest(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=MAX_INPUT_LENGTH,
        description="عنوان دلخواه برای چت جدید (اختیاری)",
    )


# ----------------------------------------------------------------------
# Shared Helper
# ----------------------------------------------------------------------
def _run_analysis(text: str) -> dict:
    """
    اجرای Mood Analysis Engine روی متن ورودی به همراه اعتبارسنجی
    (Security Rules - بخش 31 مستند) و مدیریت خطا (بخش 27 مستند).
    """
    text = text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="متن ورودی نمی‌تواند خالی باشد.")

    if len(text) > MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"متن ورودی نباید بیشتر از {MAX_INPUT_LENGTH} کاراکتر باشد.",
        )

    try:
        result = analyzer.analyze(text)
    except Exception as exc:
        # سیستم نباید Crash کند (بخش 27 مستند)
        raise HTTPException(status_code=500, detail="خطا در پردازش متن. لطفا دوباره تلاش کنید.") from exc

    result["safety_layer_active"] = analyzer.requires_safety_layer(result["mood"], result["moods"])
    return result


# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "VibeAI API is running", "docs": "/docs"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
@limiter.limit(RATE_LIMIT)
def analyze(payload: AnalyzeRequest, request: Request):
    """
    تحلیل متن فارسی کاربر و تشخیص:
    - mood (احساس غالب)
    - moods (تمام احساسات تشخیص داده‌شده با امتیاز)
    - energy (سطح انرژی)
    - activity (فعالیت فعلی)
    - time_period (بازه زمانی)
    - confidence (میزان اطمینان)
    - negations_detected (کلمات نفی شناسایی‌شده)
    - safety_layer_active (آیا Content Safety Layer باید فعال شود)
    """
    result = _run_analysis(payload.text)

    return AnalyzeResponse(
        mood=result["mood"],
        moods=result["moods"],
        energy=result["energy"],
        activity=result["activity"],
        time_period=result["time_period"],
        confidence=result["confidence"],
        negations_detected=result["negations_detected"],
        safety_layer_active=result["safety_layer_active"],
        analyzer=result.get("analyzer", "rule_based"),
    )


@app.post("/api/chats", response_model=ChatSummary)
@limiter.limit(RATE_LIMIT)
def create_chat(payload: CreateChatRequest, request: Request):
    """
    ساخت یک چت جدید (دکمه «چت جدید»).
    در صورت ندادن عنوان، عنوان موقت «چت جدید» قرار می‌گیرد و با اولین پیام
    به‌صورت خودکار به‌روزرسانی نمی‌شود (عنوان نهایی از روی اولین پیام در recommend ساخته می‌شود
    اگر عنوان داده نشده باشد).
    """
    try:
        chat_id = db.create_chat(title=payload.title or "")
        chat = db.get_chat_by_id(chat_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="خطا در ساخت چت جدید.") from exc

    return ChatSummary(**chat)


@app.get("/api/chats", response_model=list[ChatSummary])
@limiter.limit(RATE_LIMIT)
def list_chats(request: Request, limit: int = 50, offset: int = 0, search: str | None = None):
    """
    دریافت لیست چت‌ها (جدیدترین بر اساس آخرین فعالیت در ابتدا).
    با پارامتر search می‌توان در عنوان چت‌ها و متن پیام‌ها جستجو کرد.
    """
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit باید بین 1 و 200 باشد.")

    if offset < 0:
        raise HTTPException(status_code=400, detail="offset نمی‌تواند منفی باشد.")

    try:
        chats = db.get_chats(limit=limit, offset=offset, search=search)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="خطا در دریافت لیست چت‌ها.") from exc

    return [ChatSummary(**c) for c in chats]


@app.get("/api/chats/{chat_id}", response_model=ChatDetail)
@limiter.limit(RATE_LIMIT)
def get_chat(chat_id: int, request: Request):
    """دریافت یک چت همراه با تمام پیام‌ها/درخواست‌های آن (برای بازسازی صفحه چت)."""
    chat = db.get_chat_by_id(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"چت با id={chat_id} یافت نشد.")

    try:
        messages = db.get_history_for_chat(chat_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="خطا در دریافت پیام‌های چت.") from exc

    return ChatDetail(
        id=chat["id"],
        title=chat["title"],
        created_at=chat["created_at"],
        updated_at=chat["updated_at"],
        messages=[HistoryItem(**m) for m in messages],
    )


@app.post("/api/recommend", response_model=RecommendResponse)
@limiter.limit(RATE_LIMIT)
def recommend(req_body: RecommendRequest, request: Request):
    """
    تحلیل متن کاربر و سپس پیشنهاد:
    - Top 5 فیلم (از TMDB یا Mock Data در صورت نبود API Key/خطا)
    - Top 10 موسیقی (از دیتاست محلی)

    این درخواست به‌عنوان یک پیام در یک چت ذخیره می‌شود:
    - اگر chat_id ارسال شود، پیام به همان چت اضافه می‌شود.
    - اگر chat_id ارسال نشود، یک چت جدید ساخته می‌شود و عنوان آن از روی
      همین متن تعیین می‌شود.

    هر پیشنهاد همراه با دلیل (Explainable Recommendation - بخش 20 مستند) است.
    """
    result = _run_analysis(req_body.text)

    mood = result["mood"]
    energy = result["energy"]
    activity = result["activity"]
    time_period = result["time_period"]
    safety_active = result["safety_layer_active"]

    # تعیین چت مقصد: چت موجود یا ساخت چت جدید
    if req_body.chat_id is not None:
        if not db.chat_exists(req_body.chat_id):
            raise HTTPException(status_code=404, detail=f"چت با id={req_body.chat_id} یافت نشد.")
        chat_id = req_body.chat_id
    else:
        try:
            chat_id = db.create_chat(title=req_body.text.strip())
        except Exception as exc:
            raise HTTPException(status_code=500, detail="خطا در ساخت چت جدید.") from exc

    content_intent = _detect_content_intent(req_body.text)

    try:
        if content_intent == "music":
            movies = []
        else:
            movies = movie_recommender.recommend(
                mood=mood,
                energy=energy,
                activity=activity,
                time_period=time_period,
                safety_active=safety_active,
                top_n=MOVIE_FOCUSED_TOP_N if content_intent == "movie" else TOP_N_MOVIES,
            )
    except Exception:
        # سیستم نباید در صورت خطای TMDB یا قطع اینترنت Crash کند (بخش 27 مستند)
        movies = []

    try:
        if content_intent == "movie":
            music = []
        else:
            music = music_recommender.recommend(
                mood=mood,
                energy=energy,
                activity=activity,
                time_period=time_period,
                safety_active=safety_active,
                top_n=MUSIC_FOCUSED_TOP_N if content_intent == "music" else TOP_N_SONGS,
            )
    except Exception:
        music = []

    analysis_response = AnalyzeResponse(
        mood=mood,
        moods=result["moods"],
        energy=energy,
        activity=activity,
        time_period=time_period,
        confidence=result["confidence"],
        negations_detected=result["negations_detected"],
        safety_layer_active=safety_active,
        analyzer=result.get("analyzer", "rule_based"),
    )

    recommendations_payload = {
        "movies": [m if isinstance(m, dict) else m.dict() for m in movies],
        "music": [m if isinstance(m, dict) else m.dict() for m in music],
    }

    # ذخیره در History (بخش 23-24 مستند). در صورت خطا، سیستم Crash نکند.
    try:
        history_id = db.save_history(
            chat_id=chat_id,
            user_input=req_body.text.strip(),
            detected_mood=mood,
            detected_energy=energy,
            detected_activity=activity,
            detected_time_period=time_period,
            confidence=result["confidence"],
            recommendations=recommendations_payload,
        )
    except Exception:
        history_id = -1

    return RecommendResponse(
        chat_id=chat_id,
        history_id=history_id,
        analysis=analysis_response,
        movies=movies,
        music=music,
    )


@app.post("/api/feedback", response_model=FeedbackResponse)
@limiter.limit(RATE_LIMIT)
def feedback(payload: FeedbackRequest, request: Request):
    """
    ثبت بازخورد کاربر (لایک/دیسلایک) برای یک پیشنهاد (بخش 22 مستند).
    """
    item_type = payload.item_type.strip().lower()
    reaction = payload.reaction.strip().lower()

    if item_type not in db.VALID_ITEM_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"item_type باید یکی از {sorted(db.VALID_ITEM_TYPES)} باشد.",
        )

    if reaction not in db.VALID_REACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"reaction باید یکی از {sorted(db.VALID_REACTIONS)} باشد.",
        )

    try:
        feedback_id = db.save_feedback(
            history_id=payload.history_id,
            item_type=item_type,
            item_name=payload.item_name,
            reaction=reaction,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="خطا در ذخیره بازخورد. لطفا دوباره تلاش کنید.") from exc

    saved = db.get_feedback_for_history(payload.history_id)
    last = next((f for f in reversed(saved) if f["id"] == feedback_id), saved[-1])

    return FeedbackResponse(**last)


@app.get("/api/history", response_model=list[HistoryItem])
@limiter.limit(RATE_LIMIT)
def history(request: Request, limit: int = 50, offset: int = 0):
    """
    دریافت تاریخچه‌ی درخواست‌های کاربر (جدیدترین در ابتدا) - بخش 23 مستند.
    """
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit باید بین 1 و 200 باشد.")

    if offset < 0:
        raise HTTPException(status_code=400, detail="offset نمی‌تواند منفی باشد.")

    try:
        records = db.get_history(limit=limit, offset=offset)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="خطا در دریافت تاریخچه.") from exc

    return [HistoryItem(**r) for r in records]


@app.get("/api/taste-profile", response_model=TasteProfileResponse)
@limiter.limit(RATE_LIMIT)
def taste_profile(request: Request):
    """
    دریافت پروفایل ذائقه‌ی یادگرفته‌شده از لایک/دیسلایک‌های قبلی کاربر
    (ژانرهای محبوب فیلم و موسیقی) - بخش شخصی‌سازی یادگیرنده.
    """
    try:
        profile = db.get_taste_profile()
        total_feedback = db.count_feedback()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="خطا در دریافت پروفایل ذائقه.") from exc

    def top_genres(category: str) -> list[GenreScore]:
        items = profile.get(category, {})
        ranked = sorted(items.items(), key=lambda kv: kv[1], reverse=True)
        return [GenreScore(genre=genre, score=score) for genre, score in ranked if score > 0][:5]

    return TasteProfileResponse(
        movie_genres=top_genres("movie_genre"),
        music_genres=top_genres("music_genre"),
        total_feedback=total_feedback,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)