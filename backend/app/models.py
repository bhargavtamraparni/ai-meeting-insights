from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .database import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    status = Column(String, default="processing")  # processing, completed, failed

    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    action_items = Column(Text, nullable=True)  # JSON string of a list of objects
    decisions = Column(Text, nullable=True)  # JSON string of a list of strings

    keywords = Column(Text, nullable=True) # JSON string of [{"keyword": "str", "count": int}]  # JSON string of a list of strings
    sentiment = Column(String, nullable=True)  # e.g., "Positive", "Neutral", "Negative"
    participants = Column(Text, nullable=True)  # JSON string of a list of strings

    created_at = Column(DateTime(timezone=True), server_default=func.now())
