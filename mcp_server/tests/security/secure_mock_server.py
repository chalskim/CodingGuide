#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
import re
import time
import uuid
import html
import json
import asyncio
import uvicorn
import os
import sys
from json.decoder import JSONDecodeError
from typing import List, Dict, Optional, Set
from pydantic import BaseModel, Field, validator, ValidationError
from fastapi import FastAPI, Request, Response, Depends, Header, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# 보안 설정
API_KEY = "test_api_key_12345"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# 모의 서버 애플리케이션 생성
app = FastAPI(title="MCP Secure Mock Server", description="보안이 강화된 모의 MCP 서버")

# CORS 설정 - 허용된 출처만 명시적으로 지정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # 필요한 메서드만 허용
    allow_headers=["Authorization", "Content-Type"],  # 필요한 헤더만 허용
)

# 세션 저장소
sessions = {}

# 데이터 저장소
feedbacks = {}
requests_data = {}

# 락 메커니즘
request_locks = {}

# 모델 정의
class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None
    
    @validator('content')
    def validate_content(cls, v):
        # XSS 방지를 위한 검증
        if re.search(r'<script|<img|<svg|javascript:|onerror=|onload=', v, re.IGNORECASE):
            raise ValueError("잠재적인 XSS 공격이 감지되었습니다")
        return html.escape(v)  # 추가 보호를 위한 이스케이프 적용

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = Field(0.7, ge=0, le=1)
    max_tokens: Optional[int] = Field(1000, gt=0, le=4000)
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: ChatMessage
    session_id: str

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = Field(1000, gt=0, le=4000)
    temperature: Optional[float] = Field(0.7, ge=0, le=1)
    model: Optional[str] = "gpt-3.5-turbo"
    
    @validator('prompt')
    def validate_prompt(cls, v):
        # XSS 방지를 위한 검증
        if re.search(r'<script|<img|<svg|javascript:|onerror=|onload=', v, re.IGNORECASE):
            raise ValueError("잠재적인 XSS 공격이 감지되었습니다")
        return html.escape(v)  # 추가 보호를 위한 이스케이프 적용

class GenerateResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str

class FeedbackRequest(BaseModel):
    request_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    session_id: Optional[str] = None
    
    @validator('comment')
    def validate_comment(cls, v):
        if v is not None:
            # XSS 방지를 위한 검증
            if re.search(r'<script|<img|<svg|javascript:|onerror=|onload=', v, re.IGNORECASE):
                raise ValueError("잠재적인 XSS 공격이 감지되었습니다")
            return html.escape(v)  # 추가 보호를 위한 이스케이프 적용
        return v

class FeedbackResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "success"
    message: str = "피드백이 성공적으로 저장되었습니다."

# 미들웨어
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limit_per_minute=60):
        super().__init__(app)
        self.rate_limit = rate_limit_per_minute
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # 이전 요청 정리
        self.requests = {ip: times for ip, times in self.requests.items() 
                        if current_time - times[-1] < 60}
        
        # 현재 IP의 요청 확인
        if client_ip in self.requests:
            times = self.requests[client_ip]
            # 1분 내 요청만 유지
            times = [t for t in times if current_time - t < 60]
            
            # 속도 제한 확인
            if len(times) >= self.rate_limit:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "너무 많은 요청이 발생했습니다. 잠시 후 다시 시도하세요."}
                )
            
            times.append(current_time)
            self.requests[client_ip] = times
        else:
            self.requests[client_ip] = [current_time]
        
        return await call_next(request)

# 미들웨어 추가
app.add_middleware(RateLimitMiddleware, rate_limit_per_minute=60)

# 예외 처리 핸들러
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

# 유틸리티 함수
def generate_id() -> str:
    return str(uuid.uuid4())

def sanitize_input(input_str: str) -> str:
    # HTML 이스케이프 적용
    return html.escape(input_str)

async def verify_api_key(api_key: str = Header(None, alias="Authorization")):
    if not api_key or api_key != f"Bearer {API_KEY}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 API 키",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return api_key

async def get_request_lock(request_id: str):
    if request_id not in request_locks:
        request_locks[request_id] = asyncio.Lock()
    return request_locks[request_id]

# 예외 핸들러
@app.exception_handler(JSONDecodeError)
async def json_decode_exception_handler(request: Request, exc: JSONDecodeError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "잘못된 JSON 형식", "detail": str(exc)}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "유효성 검증 오류",
            "detail": exc.errors()
        }
    )

@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "입력값 오류",
            "detail": str(exc)
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 프로덕션 환경에서는 최소한의 정보만 반환
    if ENVIRONMENT == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "내부 서버 오류"}
        )
    # 개발 환경에서는 제한된 정보 제공
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": str(exc), "type": type(exc).__name__}
    )

# 엔드포인트 정의
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# 유틸리티 함수
def sanitize_input(text):
    """입력 텍스트를 안전하게 처리합니다."""
    if not text:
        return ""
    # HTML 이스케이프 적용
    return html.escape(text)

async def get_request_lock(request_id):
    """요청별 락을 반환합니다."""
    if request_id not in request_locks:
        request_locks[request_id] = asyncio.Lock()
    return request_locks[request_id]

@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    # 원시 요청 데이터 검증
    try:
        body = await request.json()
        if "messages" in body:
            for message in body["messages"]:
                if "content" in message and isinstance(message["content"], str):
                    content = message["content"]
                    if re.search(r'<script|<img|<svg|javascript:|onerror=|onload=', content, re.IGNORECASE):
                        raise HTTPException(status_code=400, detail="잠재적인 XSS 공격이 감지되었습니다")
        # 유효성 검증 통과 후 Pydantic 모델로 변환
        request_data = ChatRequest(**body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="유효하지 않은 JSON 형식입니다")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 요청 ID 생성
    request_id = generate_id()
    
    # 세션 관리
    if request_data.session_id and request_data.session_id in sessions:
        # 세션 유효성 검사
        session = sessions[request_data.session_id]
        if time.time() - session["created_at"] > 3600:  # 1시간 후 만료
            del sessions[request_data.session_id]
            session_id = generate_id()
            sessions[session_id] = {"created_at": time.time(), "user_id": session["user_id"]}
        else:
            session_id = request_data.session_id
    else:
        # 새 세션 생성
        session_id = generate_id()
        sessions[session_id] = {"created_at": time.time(), "user_id": generate_id()}
    
    # 사용자 메시지 추출
    user_message = next((msg for msg in request_data.messages if msg.role == "user"), None)
    if not user_message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="사용자 메시지가 필요합니다.")
    
    # 입력 검증 및 이스케이프 적용
    user_content = user_message.content  # 이미 ChatMessage 모델에서 검증 및 이스케이프 처리됨
    
    # 데이터 저장 (경쟁 조건 방지)
    lock = await get_request_lock(request_id)
    async with lock:
        requests_data[request_id] = {
            "session_id": session_id,
            "messages": request_data.messages,
            "created_at": time.time()
        }
    
    # 응답 생성
    response_message = ChatMessage(
        role="assistant",
        content=f"이것은 '{user_content}'에 대한 안전한 모의 응답입니다."
    )
    
    # 응답 반환
    return ChatResponse(
        id=request_id,
        message=response_message,
        session_id=session_id
    )

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, api_key: str = Depends(verify_api_key)):
    # 요청 ID 생성
    request_id = generate_id()
    
    # 입력 검증 및 이스케이프 적용
    prompt = sanitize_input(request.prompt)
    
    # 응답 생성
    content = f"이것은 '{prompt}'에 대한 안전한 모의 생성 응답입니다."
    
    # 응답 반환
    return GenerateResponse(
        id=request_id,
        content=content
    )

@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest, api_key: str = Depends(verify_api_key)):
    # 피드백 ID 생성
    feedback_id = generate_id()
    
    # 요청 ID 검증
    if request.request_id not in requests_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="요청 ID를 찾을 수 없습니다.")
    
    # 입력 검증 및 이스케이프 적용
    request_id = sanitize_input(request.request_id)
    comment = sanitize_input(request.comment) if request.comment else None
    
    # 데이터 저장 (경쟁 조건 방지)
    lock = await get_request_lock(request_id)
    async with lock:
        feedbacks[feedback_id] = {
            "request_id": request_id,
            "rating": request.rating,
            "comment": comment,
            "created_at": time.time()
        }
    
    # 응답 반환
    return FeedbackResponse(
        id=feedback_id
    )

@app.get("/feedback/{feedback_id}")
async def get_feedback(feedback_id: str, api_key: str = Depends(verify_api_key)):
    # 피드백 ID 검증
    if feedback_id not in feedbacks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="피드백 ID를 찾을 수 없습니다.")
    
    # 피드백 데이터 가져오기
    feedback = feedbacks[feedback_id]
    
    # 응답 반환
    return {
        "id": feedback_id,
        "rating": feedback["rating"],
        "comment": feedback["comment"],
        "created_at": feedback["created_at"]
    }

@app.get("/feedback/request/{request_id}")
async def get_feedback_by_request(request_id: str, api_key: str = Depends(verify_api_key)):
    # 요청 ID 검증
    if request_id not in requests_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="요청 ID를 찾을 수 없습니다.")
    
    # 해당 요청 ID에 대한 피드백 찾기
    request_feedbacks = []
    for fb_id, fb in feedbacks.items():
        if fb["request_id"] == request_id:
            request_feedbacks.append({
                "id": fb_id,
                "rating": fb["rating"],
                "comment": fb["comment"],
                "created_at": fb["created_at"]
            })
    
    # 응답 반환
    return request_feedbacks

# 메인 함수
def main():
    # 서버 실행
    uvicorn.run("secure_mock_server:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()