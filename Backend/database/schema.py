from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Request ────────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    text: str


class FeedbackRequest(BaseModel):
    session_id:  int
    item_type:   str            # "movie" | "music"
    item_id:     str
    item_title:  str
    feedback:    str            # "like" | "dislike"
    mood_context: Optional[str] = None


# ── Response ───────────────────────────────────────────────────────────────────

class MoodAnalysis(BaseModel):
    mood:        str
    moods:       dict[str, int]
    energy:      str
    activity:    str
    time_period: str
    confidence:  float


class MovieRecommendation(BaseModel):
    id:             int
    title:          str
    original_title: str
    overview:       str
    poster_url:     Optional[str]
    genres:         list[str]
    vote_average:   float
    release_year:   Optional[str]
    reasoning:      str


class MusicRecommendation(BaseModel):
    title:       str
    artist:      str
    genre:       str
    mood_tags:   list[str]
    youtube_url: str
    reasoning:   str


class VibeResponse(BaseModel):
    session_id:  int
    analysis:    MoodAnalysis
    movies:      list[MovieRecommendation]
    music:       list[MusicRecommendation]
    safety_note: Optional[str] = None


class HistoryItem(BaseModel):
    id:                int
    user_input:        str
    detected_mood:     str
    detected_energy:   str
    detected_activity: str
    confidence:        float
    timestamp:         Optional[str]