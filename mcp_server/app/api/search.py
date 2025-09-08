from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from loguru import logger
import uuid

# 인증 의존성 임포트
from app.core.auth import get_api_key, get_optional_api_key

# 서비스 임포트
from app.services.search import SearchService

# 모델 정의
class SearchRequest(BaseModel):
    query: str = Field(..., description="검색 쿼리")
    num_results: Optional[int] = Field(5, description="반환할 최대 결과 수")
    search_type: Optional[str] = Field("web", description="검색 유형 (web, image, news 등)")
    options: Optional[Dict[str, Any]] = Field(None, description="추가 검색 옵션")

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="검색 결과 목록")
    request_id: str = Field(..., description="요청 ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")

# 라우터 생성
router = APIRouter()

# 서비스 인스턴스 생성
search_service = SearchService()

@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest, 
    x_search_api_key: Optional[str] = Header(None, alias="X-Search-API-Key"),
    x_search_engine_id: Optional[str] = Header(None, alias="X-Search-Engine-ID"),
    api_key_info: Dict[str, Any] = Depends(get_api_key)
):
    """검색 API 엔드포인트
    
    쿼리를 받아 외부 검색 서비스를 통해 검색 결과를 반환합니다.
    클라이언트는 X-Search-API-Key와 X-Search-Engine-ID 헤더를 통해 검색 API 키와 검색 엔진 ID를 제공해야 합니다.
    """
    try:
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        
        logger.info(f"Search request received: {request_id}")
        
        # 검색 수행
        results = await search_service.search(
            query=request.query,
            num_results=request.num_results,
            search_type=request.search_type,
            options=request.options,
            api_key=x_search_api_key,
            search_engine_id=x_search_engine_id
        )
        
        # 응답 반환
        return SearchResponse(
            results=results,
            request_id=request_id,
            metadata={
                "query": request.query,
                "num_results": len(results),
                "search_type": request.search_type
            }
        )
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")