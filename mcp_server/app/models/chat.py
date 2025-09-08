from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class Message(BaseModel):
    """채팅 메시지 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    messages: List[Message]
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    model: Optional[str] = None
    stream: Optional[bool] = False
    protocols: Optional[List[str]] = Field(default_factory=list)
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: Message
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatStreamResponse(BaseModel):
    """채팅 스트림 응답 모델"""
    id: str
    delta: str
    finish_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatHistory(BaseModel):
    """채팅 기록 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)