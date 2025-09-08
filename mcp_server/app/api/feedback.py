from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from loguru import logger
import uuid
from datetime import datetime

# 인증 의존성 임포트
from app.core.auth import get_api_key, get_optional_api_key

# 프로토콜 임포트
from app.protocols.learning import AdaptiveLearningProtocol

# 모델 정의
class FeedbackRequest(BaseModel):
    request_id: str = Field(..., description="피드백 대상 요청 ID")
    session_id: Optional[str] = Field(None, description="대화 세션 ID")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    rating: int = Field(..., description="평점 (1-5)")
    feedback_type: str = Field(..., description="피드백 유형 (accuracy, relevance, clarity, completeness, etc.)")
    comment: Optional[str] = Field(None, description="추가 코멘트")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")

class FeedbackResponse(BaseModel):
    feedback_id: str = Field(..., description="피드백 ID")
    status: str = Field("success", description="처리 상태")
    timestamp: datetime = Field(default_factory=datetime.now)

# 라우터 생성
router = APIRouter()

# 프로토콜 인스턴스 생성
learning_protocol = AdaptiveLearningProtocol()

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest, api_key_info: Dict[str, Any] = Depends(get_api_key)):
    """피드백 수집 API 엔드포인트
    
    사용자의 피드백을 수집하여 저장합니다.
    """
    try:
        # 피드백 ID 생성
        feedback_id = str(uuid.uuid4())
        
        logger.info(f"Feedback received: {feedback_id} for request: {request.request_id}")
        
        # 피드백 유효성 검사
        if request.rating < 1 or request.rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        # 피드백 저장
        await learning_protocol.store_feedback(
            feedback_id=feedback_id,
            request_id=request.request_id,
            session_id=request.session_id,
            user_id=request.user_id,
            rating=request.rating,
            feedback_type=request.feedback_type,
            comment=request.comment,
            metadata=request.metadata
        )
        
        # 응답 반환
        return FeedbackResponse(
            feedback_id=feedback_id,
            status="success",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback/{feedback_id}", response_model=Dict[str, Any])
async def get_feedback(feedback_id: str):
    """피드백 조회 API 엔드포인트
    
    특정 피드백의 상세 정보를 조회합니다.
    """
    try:
        # 피드백 조회
        feedback = await learning_protocol.get_feedback(feedback_id)
        
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        return feedback
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback/request/{request_id}", response_model=List[Dict[str, Any]])
async def get_feedback_by_request(request_id: str):
    """요청별 피드백 조회 API 엔드포인트
    
    특정 요청에 대한 모든 피드백을 조회합니다.
    """
    try:
        # 요청별 피드백 조회
        feedbacks = await learning_protocol.get_feedback_by_request(request_id)
        
        return feedbacks
        
    except Exception as e:
        logger.error(f"Error retrieving feedback by request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))