import json
from sqlalchemy.orm import Session
from . import models

class MeetingCRUD:
    def get(self, db: Session, meeting_id: int) -> models.Meeting | None:
        return db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> list[models.Meeting]:
        return db.query(models.Meeting).order_by(models.Meeting.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, db: Session, filename: str) -> models.Meeting:
        db_meeting = models.Meeting(filename=filename, status="processing")
        db.add(db_meeting)
        db.commit()
        db.refresh(db_meeting)
        return db_meeting

    def update_status(self, db: Session, meeting_id: int, status: str) -> models.Meeting | None:
        db_meeting = self.get(db, meeting_id)
        if db_meeting:
            db_meeting.status = status
            db.commit()
            db.refresh(db_meeting)
        return db_meeting

    def update_transcript(self, db: Session, meeting_id: int, transcript: str):
        db_meeting = self.get(db, meeting_id)
        if db_meeting:
            db_meeting.transcript = transcript
            db.commit()
        return db_meeting

    def update_insights(self, db: Session, meeting_id: int, insights: dict):
        db_meeting = self.get(db, meeting_id)
        if db_meeting:
            db_meeting.summary = insights.get("summary")
            db_meeting.action_items = json.dumps(insights.get("action_items", []))
            db_meeting.decisions = json.dumps(insights.get("decisions", []))
            db_meeting.keywords = json.dumps(insights.get("keywords", []))
            db_meeting.participants = json.dumps(insights.get("participants", []))
            db_meeting.sentiment = insights.get("sentiment")
            db.commit()
        return db_meeting

# --- Global Instance ---
meeting_crud = MeetingCRUD()
