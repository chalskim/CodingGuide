from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class FeedbackRequest(BaseModel):
    """피드백 요청 모델"""
    request_id: str
    rating: int = Field(ge=1, le=5)
    feedback_text: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class FeedbackResponse(BaseModel):
    """피드백 응답 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "received"

class FeedbackItem(BaseModel):
    """피드백 항목 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    rating: int
    feedback_text: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class FeedbackSummary(BaseModel):
    """피드백 요약 모델"""
    request_id: str
    average_rating: float
    feedback_count: int
    categories: Dict[str, int] = Field(default_factory=dict)
    recent_feedback: List[FeedbackItem] = Field(default_factory=list)