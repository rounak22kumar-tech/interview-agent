from typing import Optional
from pydantic import BaseModel


class FeedbackModel(BaseModel):
    summary: str
    strengths: list[str]
    gaps: list[str]
    next: list[str]


class InterviewRequest(BaseModel):
    sessionId: str
    candidate: Optional[dict] = None  # Required on first call only
    message: Optional[str] = None     # Required on subsequent calls


class InterviewResponse(BaseModel):
    reply: str
    done: bool
    feedback: Optional[FeedbackModel] = None
