import json
from pydantic import BaseModel, field_validator
from typing import List, Optional

# --- Schema for Keywords ---
class Keyword(BaseModel):
    keyword: str
    count: int

# --- Schemas for Search ---
class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    answer: str

# --- Schemas for Meeting Insights ---
class ActionItem(BaseModel):
    task: str
    assigned_to: str

class MeetingBase(BaseModel):
    id: int
    filename: str
    status: str

# For polling status
class MeetingStatus(MeetingBase):
    pass

# The main Meeting schema returned by the API
class Meeting(MeetingBase):
    transcript: Optional[str] = None
    summary: Optional[str] = None
    action_items: List[ActionItem] = []
    decisions: List[str] = []
    keywords: List[Keyword] = []
    participants: List[str] = []
    sentiment: Optional[str] = None

    # Pydantic v2 validator
    @field_validator('action_items', 'decisions', 'keywords', 'participants', mode='before')
    @classmethod
    def parse_json_strings(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v if v is not None else []

    class Config:
        from_attributes = True

