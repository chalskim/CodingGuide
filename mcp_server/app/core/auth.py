from fastapi import Depends, HTTPException, status, Header
from fastapi.security import APIKeyHeader
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

from app.api.auth import verify_api_key

# API 키 헤더 정의
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Depends(api_key_header)) -> Dict[str, Any]:
    """
    API 키 검증 의존성
    
    Args:
        api_key: 요청 헤더에서 추출한 API 키
        
    Returns:
        API 키 정보
        
    Raises:
        HTTPException: API 키가 유효하지 않은 경우
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API 키가 필요합니다",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    key_info = verify_api_key(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 API 키",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return key_info

async def get_optional_api_key(api_key: str = Depends(api_key_header)) -> Optional[Dict[str, Any]]:
    """
    선택적 API 키 검증 의존성
    
    Args:
        api_key: 요청 헤더에서 추출한 API 키
        
    Returns:
        API 키 정보 또는 None
    """
    if not api_key:
        return None
    
    return verify_api_key(api_key)