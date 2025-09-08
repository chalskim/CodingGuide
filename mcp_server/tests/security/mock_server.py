#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
import json
import uvicorn
import os
import sys

# 모의 서버 애플리케이션 생성
app = FastAPI(title="MCP Mock Server", description="취약성 테스트를 위한 모의 MCP 서버")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모델 정의
class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: ChatMessage
    session_id: str

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    model: Optional[str] = "gpt-3.5-turbo"

class GenerateResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str

class FeedbackRequest(BaseModel):
    request_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    session_id: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "success"
    message: str = "피드백이 성공적으로 저장되었습니다."

# 유틸리티 함수
def generate_id() -> str:
    return str(uuid.uuid4())

def sanitize_input(input_str: str) -> str:
    # 입력 검증 취약점 테스트를 위한 함수
    # 실제로는 적절한 검증이 필요함
    return input_str

# 엔드포인트 정의
@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    # 요청 ID 생성
    request_id = generate_id()
    
    # 세션 ID 생성 또는 사용
    session_id = request.session_id or generate_id()
    
    # 사용자 메시지 추출
    user_message = next((msg for msg in request.messages if msg.role == "user"), None)
    if not user_message:
        raise HTTPException(status_code=400, detail="사용자 메시지가 필요합니다.")
    
    # 입력 검증 취약점 테스트를 위해 의도적으로 검증 생략
    user_content = sanitize_input(user_message.content)
    
    # 응답 생성
    response_message = ChatMessage(
        role="assistant",
        content=f"이것은 '{user_content}'에 대한 모의 응답입니다."
    )
    
    # 응답 반환
    return ChatResponse(
        id=request_id,
        message=response_message,
        session_id=session_id
    )

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    # 요청 ID 생성
    request_id = generate_id()
    
    # 입력 검증 취약점 테스트를 위해 의도적으로 검증 생략
    prompt = sanitize_input(request.prompt)
    
    # 응답 생성
    content = f"이것은 '{prompt}'에 대한 모의 생성 응답입니다."
    
    # 응답 반환
    return GenerateResponse(
        id=request_id,
        content=content
    )

@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    # 피드백 ID 생성
    feedback_id = generate_id()
    
    # 입력 검증 취약점 테스트를 위해 의도적으로 검증 생략
    request_id = sanitize_input(request.request_id)
    
    # 응답 반환
    return FeedbackResponse(
        id=feedback_id
    )

@app.get("/feedback/{feedback_id}")
async def get_feedback(feedback_id: str):
    # 입력 검증 취약점 테스트를 위해 의도적으로 검증 생략
    feedback_id = sanitize_input(feedback_id)
    
    # 응답 반환
    return {
        "id": feedback_id,
        "rating": 5,
        "comment": "이것은 모의 피드백입니다.",
        "created_at": "2023-01-01T00:00:00Z"
    }

@app.get("/feedback/request/{request_id}")
async def get_feedback_by_request(request_id: str):
    # 입력 검증 취약점 테스트를 위해 의도적으로 검증 생략
    request_id = sanitize_input(request_id)
    
    # 응답 반환
    return [
        {
            "id": generate_id(),
            "rating": 5,
            "comment": "이것은 모의 피드백입니다.",
            "created_at": "2023-01-01T00:00:00Z"
        }
    ]

# 오류 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 오류 정보 유출 취약점 테스트를 위해 의도적으로 상세 정보 노출
    return {
        "error": str(exc),
        "type": type(exc).__name__,
        "path": request.url.path,
        "method": request.method,
        "headers": dict(request.headers),
        "traceback": str(sys.exc_info())
    }

# 메인 함수
def main():
    # 서버 실행
    uvicorn.run("mock_server:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()