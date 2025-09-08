from fastapi import APIRouter
from app.api import chat, generate, feedback, search

api_router = APIRouter()

# 채팅 API 라우터 등록
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

# 텍스트 생성 API 라우터 등록
api_router.include_router(generate.router, prefix="/generate", tags=["generate"])

# 피드백 API 라우터 등록
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])

# 검색 API 라우터 등록
api_router.include_router(search.router, prefix="/search", tags=["search"])