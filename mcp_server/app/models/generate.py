from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class GenerationRequest(BaseModel):
    """텍스트 생성 요청 모델"""
    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    model: Optional[str] = None
    stream: Optional[bool] = False
    protocols: Optional[List[str]] = Field(default_factory=list)
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)

class GenerationResponse(BaseModel):
    """텍스트 생성 응답 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class GenerationStreamResponse(BaseModel):
    """텍스트 생성 스트림 응답 모델"""
    id: str
    delta: str
    finish_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GenerationHistory(BaseModel):
    """텍스트 생성 기록 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    response: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)