from typing import Dict, Any, List, Optional
from loguru import logger

from app.protocols.base import BaseProtocol
from app.services.llm import LLMService

class ContentGenerationProtocol(BaseProtocol):
    """콘텐츠 생성 프로토콜 (FR-201)
    
    사용자 요청에 따라 다양한 형식과 스타일의 콘텐츠를 생성합니다.
    """
    
    def __init__(self):
        super().__init__()
        self.llm_service = LLMService()
        self.generation_history = []
    
    async def execute(self, prompt: str, context: Dict[str, Any]) -> str:
        """프로토콜 실행 메서드
        
        Args:
            prompt: 사용자 프롬프트
            context: 생성 컨텍스트
            
        Returns:
            생성된 콘텐츠
        """
        return await self.generate(prompt, {}, {}, context)
    
    async def generate(self, 
                      prompt: str, 
                      reasoning_result: Dict[str, Any], 
                      knowledge_context: Dict[str, Any],
                      context: Dict[str, Any],
                      llm_config: Optional[Dict[str, Any]] = None,
                      api_key: Optional[str] = None) -> str:
        """콘텐츠 생성 메서드
        
        Args:
            prompt: 사용자 프롬프트
            reasoning_result: 분석 추론 결과
            knowledge_context: 지식 컨텍스트
            context: 생성 컨텍스트
            llm_config: 클라이언트에서 전달받은 LLM 설정 (선택 사항)
            api_key: 클라이언트에서 전달받은 API 키 (선택 사항)
            
        Returns:
            생성된 콘텐츠
        """
        try:
            # 생성 파라미터 설정
            generation_params = self._prepare_generation_params(prompt, reasoning_result, knowledge_context, context)
            
            # 생성 전 로그 기록
            self.log_execution("generation_start", {
                "prompt": prompt,
                "params": generation_params
            })
            
            # 클라이언트에서 전달받은 LLM 설정 처리
            model = None
            max_tokens = context.get("max_tokens", 1000)
            temperature = context.get("temperature", 0.7)
            options = generation_params
            
            if llm_config:
                model = llm_config.get("model")
                if llm_config.get("max_tokens"):
                    max_tokens = llm_config.get("max_tokens")
                if llm_config.get("temperature") is not None:
                    temperature = llm_config.get("temperature")
                # 기타 옵션 병합
                if llm_config.get("options"):
                    options.update(llm_config.get("options"))
            
            # 클라이언트에서 전달받은 API 키 처리
            original_api_key = None
            if api_key:
                # 기존 API 키 백업
                original_api_key = self.llm_service.api_key
                # 클라이언트 API 키로 임시 교체
                self.llm_service.api_key = api_key
            
            try:
                # API 키가 제공된 경우 새 LLM 서비스 인스턴스 생성
                llm_service = LLMService(api_key=api_key) if api_key else self.llm_service
                
                # LLM 서비스를 통한 콘텐츠 생성
                content = await llm_service.generate_text(
                    prompt=self._build_enhanced_prompt(prompt, reasoning_result, knowledge_context),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=model,
                    options=options
                )
            finally:
                # API 키 복원 (클라이언트 키를 사용한 경우)
                if original_api_key:
                    self.llm_service.api_key = original_api_key
            
            # 생성 후 로그 기록
            self.log_execution("generation_complete", {
                "content_length": len(content),
                "content_preview": content[:100] + "..." if len(content) > 100 else content
            })
            
            # 생성 이력 저장
            self._store_generation_history(prompt, content, context)
            
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            self.log_execution("generation_error", {"error": str(e)})
            raise
    
    def _prepare_generation_params(self, 
                                 prompt: str, 
                                 reasoning_result: Dict[str, Any], 
                                 knowledge_context: Dict[str, Any],
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """생성 파라미터 준비"""
        params = {}
        
        # 기본 파라미터 설정
        params["format"] = context.get("format", "text")
        params["domain"] = context.get("domain")
        
        # 추론 결과에서 파라미터 추출
        if reasoning_result.get("suggested_format"):
            params["format"] = reasoning_result["suggested_format"]
        
        if reasoning_result.get("tone"):
            params["tone"] = reasoning_result["tone"]
        
        # 지식 컨텍스트에서 파라미터 추출
        if knowledge_context.get("sources"):
            params["sources"] = knowledge_context["sources"]
        
        # 사용자 지정 옵션 추가
        if context.get("options"):
            params.update(context["options"])
        
        return params
    
    def _build_enhanced_prompt(self, 
                             prompt: str, 
                             reasoning_result: Dict[str, Any], 
                             knowledge_context: Dict[str, Any]) -> str:
        """향상된 프롬프트 구성"""
        enhanced_prompt = f"원본 요청: {prompt}\n\n"
        
        # 지식 컨텍스트 추가
        if knowledge_context.get("relevant_info"):
            enhanced_prompt += "참고 정보:\n"
            for info in knowledge_context["relevant_info"]:
                enhanced_prompt += f"- {info}\n"
            enhanced_prompt += "\n"
        
        # 추론 결과 추가
        if reasoning_result.get("key_points"):
            enhanced_prompt += "핵심 포인트:\n"
            for point in reasoning_result["key_points"]:
                enhanced_prompt += f"- {point}\n"
            enhanced_prompt += "\n"
        
        # 최종 지시사항 추가
        enhanced_prompt += "위 정보를 바탕으로 다음 요청에 응답하세요:\n"
        enhanced_prompt += prompt
        
        return enhanced_prompt
    
    def _store_generation_history(self, prompt: str, content: str, context: Dict[str, Any]) -> None:
        """생성 이력 저장"""
        history_entry = {
            "prompt": prompt,
            "content": content,
            "timestamp": self._get_timestamp(),
            "params": {
                "max_tokens": context.get("max_tokens"),
                "temperature": context.get("temperature"),
                "format": context.get("format"),
                "domain": context.get("domain")
            }
        }
        self.generation_history.append(history_entry)
        
        # 메타데이터 업데이트
        self.set_metadata("last_generation", {
            "timestamp": self._get_timestamp(),
            "prompt_length": len(prompt),
            "content_length": len(content)
        })
    
    def get_generation_history(self) -> List[Dict[str, Any]]:
        """생성 이력 반환"""
        return self.generation_history