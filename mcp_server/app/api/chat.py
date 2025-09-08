from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from loguru import logger
import uuid
from datetime import datetime

# 인증 의존성 임포트
from app.core.auth import get_api_key, get_optional_api_key

# 프로토콜 임포트
from app.protocols.knowledge import KnowledgeAccessProtocol
from app.protocols.reasoning import AnalyticalReasoningProtocol
from app.protocols.generation import ContentGenerationProtocol
from app.protocols.learning import AdaptiveLearningProtocol
from app.protocols.communication import CommunicationProtocol

# 서비스 임포트
from app.services.llm import LLMService

# 모델 정의
class ChatMessage(BaseModel):
    role: str = Field(..., description="메시지 역할 (user, assistant, system)")
    content: str = Field(..., description="메시지 내용")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="대화 메시지 목록")
    session_id: Optional[str] = Field(None, description="대화 세션 ID")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    stream: bool = Field(False, description="스트리밍 응답 여부")
    options: Optional[Dict[str, Any]] = Field(None, description="추가 옵션")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="LLM 설정 (클라이언트에서 전달)")
    api_key: Optional[str] = Field(None, description="클라이언트에서 전달한 API 키")

class ChatResponse(BaseModel):
    message: ChatMessage = Field(..., description="응답 메시지")
    session_id: str = Field(..., description="대화 세션 ID")
    request_id: str = Field(..., description="요청 ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")

# 라우터 생성
router = APIRouter()

# 프로토콜 및 서비스 인스턴스 생성
knowledge_protocol = KnowledgeAccessProtocol()
reasoning_protocol = AnalyticalReasoningProtocol()
generation_protocol = ContentGenerationProtocol()
learning_protocol = AdaptiveLearningProtocol()
communication_protocol = CommunicationProtocol()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks, api_key_info: Dict[str, Any] = Depends(get_api_key)):
    """대화형 API 엔드포인트
    
    사용자의 메시지를 받아 MCP 프로토콜을 적용하여 응답을 생성합니다.
    """
    try:
        # 요청 ID 및 세션 ID 생성
        request_id = str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"Chat request received: {request_id}, session: {session_id}")
        
        # 사용자 메시지 추출
        user_message = next((m for m in request.messages if m.role == "user"), None)
        if not user_message:
            raise HTTPException(status_code=400, detail="User message not found")
        
        # 대화 맥락 관리 (적응형 학습 프로토콜)
        context = await learning_protocol.manage_context(request.messages, session_id)
        
        # 지식 접근 프로토콜 적용
        knowledge_context = await knowledge_protocol.retrieve_knowledge(user_message.content, context)
        
        # 분석 추론 프로토콜 적용
        reasoning_result = await reasoning_protocol.analyze(user_message.content, knowledge_context, context, api_key=api_key)
        
        # 클라이언트에서 전달받은 LLM 설정 및 API 키 처리
        llm_config = request.llm_config
        api_key = request.api_key
        
        # 콘텐츠 생성 프로토콜 적용 (LLM 설정 및 API 키 전달)
        generated_content = await generation_protocol.generate(
            user_message.content,
            reasoning_result,
            knowledge_context,
            context,
            llm_config=llm_config,
            api_key=api_key
        )
        
        # 커뮤니케이션 프로토콜 적용
        final_response = await communication_protocol.format_response(
            generated_content,
            user_message.content,
            context,
            api_key=api_key
        )
        
        # 응답 메시지 생성
        response_message = ChatMessage(
            role="assistant",
            content=final_response
        )
        
        # 대화 기록 저장 (백그라운드 작업)
        background_tasks.add_task(
            learning_protocol.store_interaction,
            session_id,
            request.messages + [response_message]
        )
        
        # 응답 반환
        return ChatResponse(
            message=response_message,
            session_id=session_id,
            request_id=request_id,
            metadata={
                "used_knowledge": knowledge_protocol.get_sources(),
                "reasoning_steps": reasoning_protocol.get_steps()
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))