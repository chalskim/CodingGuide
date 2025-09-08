from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from loguru import logger
import uuid

# 인증 의존성 임포트
from app.core.auth import get_api_key, get_optional_api_key

# 프로토콜 임포트
from app.protocols.knowledge import KnowledgeAccessProtocol
from app.protocols.reasoning import AnalyticalReasoningProtocol
from app.protocols.generation import ContentGenerationProtocol
from app.protocols.communication import CommunicationProtocol

# 서비스 임포트
from app.services.llm import LLMService

# 모델 정의
class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="생성할 텍스트의 프롬프트")
    max_tokens: Optional[int] = Field(1000, description="생성할 최대 토큰 수")
    temperature: Optional[float] = Field(0.7, description="생성 다양성 (0.0 ~ 1.0)")
    domain: Optional[str] = Field(None, description="텍스트 도메인 (예: technical, business, creative)")
    format: Optional[str] = Field(None, description="출력 형식 (예: text, json, markdown)")
    options: Optional[Dict[str, Any]] = Field(None, description="추가 옵션")

class GenerateResponse(BaseModel):
    text: str = Field(..., description="생성된 텍스트")
    request_id: str = Field(..., description="요청 ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")

# 라우터 생성
router = APIRouter()

# 프로토콜 및 서비스 인스턴스 생성
knowledge_protocol = KnowledgeAccessProtocol()
reasoning_protocol = AnalyticalReasoningProtocol()
generation_protocol = ContentGenerationProtocol()
communication_protocol = CommunicationProtocol()
llm_service = LLMService()

@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, background_tasks: BackgroundTasks, api_key_info: Dict[str, Any] = Depends(get_api_key)):
    """텍스트 생성 API 엔드포인트
    
    프롬프트를 받아 MCP 프로토콜을 적용하여 텍스트를 생성합니다.
    """
    try:
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        
        logger.info(f"Generate request received: {request_id}")
        
        # 컨텍스트 초기화
        context = {
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "domain": request.domain,
            "format": request.format,
            "options": request.options or {}
        }
        
        # 지식 접근 프로토콜 적용
        knowledge_context = await knowledge_protocol.retrieve_knowledge(request.prompt, context)
        
        # 분석 추론 프로토콜 적용
        reasoning_result = await reasoning_protocol.analyze(request.prompt, knowledge_context, context)
        
        # 콘텐츠 생성 프로토콜 적용
        generated_content = await generation_protocol.generate(
            request.prompt,
            reasoning_result,
            knowledge_context,
            context
        )
        
        # 커뮤니케이션 프로토콜 적용
        final_response = await communication_protocol.format_response(
            generated_content,
            request.prompt,
            context
        )
        
        # 응답 반환
        return GenerateResponse(
            text=final_response,
            request_id=request_id,
            metadata={
                "used_knowledge": knowledge_protocol.get_sources(),
                "reasoning_steps": reasoning_protocol.get_steps(),
                "tokens_used": len(final_response.split()) // 3  # 대략적인 토큰 수 추정
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing generate request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))