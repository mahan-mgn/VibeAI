from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Feedback
from database.schema import FeedbackRequest

router = APIRouter()


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    fb = Feedback(
        session_id=req.session_id,
        item_type=req.item_type,
        item_id=str(req.item_id),
        item_title=req.item_title,
        feedback=req.feedback,
        mood_context=req.mood_context,
    )
    db.add(fb)
    db.commit()
    return {"status": "ok", "message": "بازخورد ثبت شد."}