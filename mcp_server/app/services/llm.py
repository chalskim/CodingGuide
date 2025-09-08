from typing import Dict, Any, List, Optional
from loguru import logger
import httpx
import json
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

class LLMService:
    """LLM 서비스
    
    다양한 LLM API를 통합하여 텍스트 생성 기능을 제공합니다.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # 기본값 설정 (설정에 없는 경우)
        # 클라이언트에서 API 키를 받아 처리하는 방식으로 변경
        self.api_key = api_key or getattr(settings, "LLM_API_KEY", "sk-test")
        self.default_model = getattr(settings, "LLM_DEFAULT_MODEL", "gpt-3.5-turbo")
        self.api_base_url = getattr(settings, "LLM_API_BASE_URL", "https://api.openai.com/v1")
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.client = httpx.AsyncClient(timeout=self.timeout)
        
        # 테스트 모드 설정 (API 키가 'sk-dummy' 또는 'sk-test'로 시작하면 테스트 모드 활성화)
        self.test_mode = self.api_key.startswith("sk-dummy") or self.api_key.startswith("sk-test")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_text(self, 
                          prompt: str, 
                          max_tokens: int = 1000, 
                          temperature: float = 0.7,
                          model: Optional[str] = None,
                          options: Optional[Dict[str, Any]] = None) -> str:
        """텍스트 생성
        
        Args:
            prompt: 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 (0.0 ~ 1.0)
            model: 모델 이름 (기본값: settings.LLM_DEFAULT_MODEL)
            options: 추가 옵션
            
        Returns:
            생성된 텍스트
        """
        try:
            # 모델 설정
            model = model or self.default_model
            
            # 테스트 모드인 경우 모의 응답 반환
            if self.test_mode:
                logger.info(f"LLM API in test mode: Returning mock response for prompt: {prompt[:50]}...")
                return self._generate_mock_response(prompt, model)
            
            # API 요청 준비
            payload = self._prepare_payload(prompt, max_tokens, temperature, model, options)
            headers = self._prepare_headers()
            
            # API 요청 로깅
            logger.debug(f"LLM API request: model={model}, max_tokens={max_tokens}, temperature={temperature}")
            
            # API 요청 전송
            endpoint = f"{self.api_base_url}/chat/completions"
            response = await self.client.post(
                endpoint,
                json=payload,
                headers=headers
            )
            
            # 응답 처리
            if response.status_code == 200:
                result = response.json()
                generated_text = self._extract_generated_text(result, model)
                return generated_text
            else:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                raise Exception(f"LLM API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}")
            raise
    
    def _prepare_payload(self, 
                        prompt: str, 
                        max_tokens: int, 
                        temperature: float, 
                        model: str,
                        options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """API 요청 페이로드 준비"""
        # 기본 페이로드
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # 추가 옵션 적용
        if options:
            # 시스템 프롬프트 커스터마이징
            if options.get("system_prompt"):
                payload["messages"][0]["content"] = options["system_prompt"]
            
            # 출력 형식 지정
            if options.get("format") == "json":
                payload["response_format"] = {"type": "json_object"}
            
            # 기타 옵션 적용
            for key, value in options.items():
                if key not in ["system_prompt", "format"] and key not in payload:
                    payload[key] = value
        
        return payload
    
    def _prepare_headers(self) -> Dict[str, str]:
        """API 요청 헤더 준비"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _extract_generated_text(self, result: Dict[str, Any], model: str) -> str:
        """생성된 텍스트 추출"""
        # 모델별 응답 형식에 따라 텍스트 추출
        if "openai" in model.lower() or "gpt" in model.lower():
            # OpenAI API 응답 형식
            if "choices" in result and len(result["choices"]) > 0:
                if "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                    return result["choices"][0]["message"]["content"]
                elif "text" in result["choices"][0]:
                    return result["choices"][0]["text"]
        elif "anthropic" in model.lower() or "claude" in model.lower():
            # Anthropic API 응답 형식
            if "completion" in result:
                return result["completion"]
        
        # 기본 응답 처리
        if "text" in result:
            return result["text"]
        elif "generated_text" in result:
            return result["generated_text"]
        elif "output" in result:
            return result["output"]
        
        # JSON 문자열로 변환하여 반환
        return json.dumps(result)
        
    def _generate_mock_response(self, prompt: str, model: str) -> str:
        """테스트 모드에서 사용할 모의 응답 생성"""
        # 간단한 모의 응답 생성
        return f"이것은 '{model}' 모델의 테스트 응답입니다. 프롬프트: {prompt[:30]}..."
        
        # 실제 구현에서는 더 정교한 모의 응답을 생성할 수 있습니다.
        # 예: 특정 키워드에 따라 다른 응답 반환, 미리 정의된 응답 목록에서 선택 등
    
    async def generate_embeddings(self, text: str, model: Optional[str] = None) -> List[float]:
        """텍스트 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
            model: 임베딩 모델 (기본값: settings.EMBEDDING_MODEL)
            
        Returns:
            임베딩 벡터
        """
        try:
            # 모델 설정
            model = model or settings.EMBEDDING_MODEL
            
            # API 요청 준비
            payload = {
                "model": model,
                "input": text
            }
            headers = self._prepare_headers()
            
            # API 요청 전송
            response = await self.client.post(
                f"{settings.EMBEDDING_API_BASE_URL}",
                json=payload,
                headers=headers
            )
            
            # 응답 처리
            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0 and "embedding" in result["data"][0]:
                    return result["data"][0]["embedding"]
                else:
                    logger.error(f"Unexpected embedding response format: {result}")
                    raise Exception("Unexpected embedding response format")
            else:
                logger.error(f"Embedding API error: {response.status_code} - {response.text}")
                raise Exception(f"Embedding API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise
    
    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()