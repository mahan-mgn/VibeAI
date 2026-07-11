from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class SessionHistory(Base):
    __tablename__ = "session_history"

    id                  = Column(Integer, primary_key=True, index=True)
    user_input          = Column(Text, nullable=False)
    detected_mood       = Column(String(50))
    detected_energy     = Column(String(20))
    detected_activity   = Column(String(50))
    detected_time_period= Column(String(20))
    confidence          = Column(Float)
    recommended_movies  = Column(Text)   # JSON: list of movie IDs
    recommended_music   = Column(Text)   # JSON: list of track titles
    timestamp           = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id          = Column(Integer, primary_key=True, index=True)
    session_id  = Column(Integer, nullable=False)
    item_type   = Column(String(10))     # "movie" | "music"
    item_id     = Column(String(50))
    item_title  = Column(String(200))
    feedback    = Column(String(10))     # "like" | "dislike"
    mood_context= Column(String(50))
    timestamp   = Column(DateTime, default=datetime.utcnow)