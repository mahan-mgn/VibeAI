import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import SessionHistory
from database.schema import AnalyzeRequest, VibeResponse
from mood.analyzer import analyze
from recommender import movie, music
from recommender.safety import safety_note
from config.settings import settings

router = APIRouter()


@router.post("/recommend", response_model=VibeResponse)
async def recommend(req: AnalyzeRequest, db: Session = Depends(get_db)):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="متن خالی است.")

    # 1 — Mood analysis
    analysis = analyze(req.text)

    # 2 — Recommendations
    movies = []
    if settings.TMDB_API_KEY:
        movies = await movie.recommend(
            mood=analysis["mood"],
            energy=analysis["energy"],
            time_period=analysis["time_period"],
        )

    tracks = music.recommend(
        mood=analysis["mood"],
        energy=analysis["energy"],
        activity=analysis["activity"],
    )

    # 3 — Safety note
    note = safety_note(analysis["mood"])

    # 4 — Persist
    record = SessionHistory(
        user_input=req.text,
        detected_mood=analysis["mood"],
        detected_energy=analysis["energy"],
        detected_activity=analysis["activity"],
        detected_time_period=analysis["time_period"],
        confidence=analysis["confidence"],
        recommended_movies=json.dumps([m["id"] for m in movies], ensure_ascii=False),
        recommended_music=json.dumps([t["title"] for t in tracks], ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return VibeResponse(
        session_id=record.id,
        analysis=analysis,
        movies=movies,
        music=tracks,
        safety_note=note,
    )