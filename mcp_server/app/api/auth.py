from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import uuid
import secrets
from datetime import datetime, timedelta
from loguru import logger

from app.core.config import settings
from app.utils.helpers import generate_id, generate_timestamp

# 라우터 생성
router = APIRouter(tags=["auth"])

# API 키 헤더 정의
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# 메모리 내 API 키 저장소 (실제 구현에서는 데이터베이스 사용 권장)
api_keys = {}

# 모델 정의
class APIKeyRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    description: Optional[str] = Field(None, description="API 키 설명")
    expires_in_days: Optional[int] = Field(30, description="만료 기간(일)")

class APIKeyResponse(BaseModel):
    key_id: str = Field(..., description="API 키 ID")
    api_key: str = Field(..., description="생성된 API 키")
    user_id: str = Field(..., description="사용자 ID")
    description: Optional[str] = Field(None, description="API 키 설명")
    created_at: str = Field(..., description="생성 시간")
    expires_at: str = Field(..., description="만료 시간")

class APIKeyInfo(BaseModel):
    key_id: str = Field(..., description="API 키 ID")
    user_id: str = Field(..., description="사용자 ID")
    description: Optional[str] = Field(None, description="API 키 설명")
    created_at: str = Field(..., description="생성 시간")
    expires_at: str = Field(..., description="만료 시간")
    is_active: bool = Field(..., description="활성화 여부")

class APIKeyList(BaseModel):
    keys: List[APIKeyInfo] = Field(..., description="API 키 목록")

# API 키 생성 함수
def create_api_key(user_id: str, description: Optional[str] = None, expires_in_days: int = 30) -> Dict[str, Any]:
    """
    새로운 API 키 생성
    
    Args:
        user_id: 사용자 ID
        description: API 키 설명
        expires_in_days: 만료 기간(일)
        
    Returns:
        생성된 API 키 정보
    """
    key_id = generate_id()
    api_key = f"mcp_{secrets.token_urlsafe(32)}"
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=expires_in_days)
    
    # API 키 정보 저장
    api_keys[key_id] = {
        "key_id": key_id,
        "api_key": api_key,
        "user_id": user_id,
        "description": description,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "is_active": True
    }
    
    return api_keys[key_id]

# API 키 검증 함수
def verify_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """
    API 키 검증
    
    Args:
        api_key: 검증할 API 키
        
    Returns:
        유효한 경우 API 키 정보, 아니면 None
    """
    for key_id, key_info in api_keys.items():
        if key_info["api_key"] == api_key and key_info["is_active"]:
            # 만료 확인
            expires_at = datetime.fromisoformat(key_info["expires_at"])
            if expires_at > datetime.utcnow():
                return key_info
    return None

# API 키 생성 엔드포인트
@router.post("/keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_key(request: APIKeyRequest):
    """
    새로운 API 키 생성 엔드포인트
    """
    try:
        key_info = create_api_key(
            user_id=request.user_id,
            description=request.description,
            expires_in_days=request.expires_in_days or 30
        )
        
        logger.info(f"API 키 생성: {key_info['key_id']} (사용자: {request.user_id})")
        
        return APIKeyResponse(
            key_id=key_info["key_id"],
            api_key=key_info["api_key"],
            user_id=key_info["user_id"],
            description=key_info["description"],
            created_at=key_info["created_at"],
            expires_at=key_info["expires_at"]
        )
    except Exception as e:
        logger.error(f"API 키 생성 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API 키 생성 중 오류가 발생했습니다."
        )

# API 키 정보 조회 엔드포인트
@router.get("/keys/{key_id}", response_model=APIKeyInfo)
async def get_key_info(key_id: str, api_key: str = Depends(api_key_header)):
    """
    API 키 정보 조회 엔드포인트
    """
    # API 키 검증
    key_info = verify_api_key(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 API 키",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 요청된 키 ID 확인
    if key_id not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 키를 찾을 수 없습니다."
        )
    
    return APIKeyInfo(
        key_id=api_keys[key_id]["key_id"],
        user_id=api_keys[key_id]["user_id"],
        description=api_keys[key_id]["description"],
        created_at=api_keys[key_id]["created_at"],
        expires_at=api_keys[key_id]["expires_at"],
        is_active=api_keys[key_id]["is_active"]
    )

# API 키 비활성화 엔드포인트
@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(key_id: str, api_key: str = Depends(api_key_header)):
    """
    API 키 비활성화 엔드포인트
    """
    # API 키 검증
    key_info = verify_api_key(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 API 키",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 요청된 키 ID 확인
    if key_id not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 키를 찾을 수 없습니다."
        )
    
    # API 키 비활성화
    api_keys[key_id]["is_active"] = False
    
    logger.info(f"API 키 비활성화: {key_id}")
    
    return None