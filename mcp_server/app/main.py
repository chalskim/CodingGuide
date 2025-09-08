from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import os

# API 라우터 임포트
from app.api import chat, generate, feedback, search, auth

# 설정 임포트
from app.core.config import settings

# 애플리케이션 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(generate.router, prefix="/api/v1", tags=["generate"])
app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# 시작 이벤트 핸들러
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    # 여기에 시작 시 필요한 초기화 코드 추가

# 종료 이벤트 핸들러
@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.PROJECT_NAME}")
    # 여기에 종료 시 필요한 정리 코드 추가

# 상태 확인 엔드포인트
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": settings.VERSION}

# 오류 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# 애플리케이션 실행 (직접 실행 시)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=9000, reload=True)