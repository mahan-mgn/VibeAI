from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import SessionHistory

router = APIRouter()


@router.get("/history")
async def get_history(
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
):
    records = (
        db.query(SessionHistory)
        .order_by(SessionHistory.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id":                record.id,
            "user_input":        record.user_input,
            "detected_mood":     record.detected_mood,
            "detected_energy":   record.detected_energy,
            "detected_activity": record.detected_activity,
            "confidence":        record.confidence,
            "timestamp":         record.timestamp.isoformat() if record.timestamp else None,
        }
        for record in records
    ]