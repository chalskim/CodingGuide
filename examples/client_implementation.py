#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 클라이언트 구현 예제 (Python)

이 파일은 MCP 서버와 통신하기 위한 클라이언트 라이브러리의 구현 예제입니다.
실제 프로젝트에서는 공식 클라이언트 라이브러리를 사용하는 것을 권장합니다.
"""

import json
import os
import requests
from typing import Dict, List, Optional, Union, Any
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class CustomLLMConfig:
    """
    커스텀 LLM 설정 클래스
    자체 LLM 모델을 MCP 서버와 연결하기 위한 설정
    """
    def __init__(self, model: str, api_key: Optional[str] = None, 
                 temperature: Optional[float] = None, max_tokens: Optional[int] = None,
                 model_endpoint: Optional[str] = None, options: Optional[Dict[str, Any]] = None):
        """
        커스텀 LLM 설정 생성자
        
        Args:
            model: LLM 모델 이름
            api_key: LLM API 키 (선택 사항)
            temperature: 생성 온도 (0.0 ~ 1.0)
            max_tokens: 최대 토큰 수
            model_endpoint: LLM API 엔드포인트 URL (선택 사항)
            options: 추가 옵션 (system_prompt 등)
        """
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model_endpoint = model_endpoint
        self.options = options or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        config = {"model": self.model}
        
        if self.temperature is not None:
            config["temperature"] = self.temperature
        if self.max_tokens is not None:
            config["max_tokens"] = self.max_tokens
        if self.model_endpoint:
            config["model_endpoint"] = self.model_endpoint
        if self.options:
            config["options"] = self.options
            
        return config


class MCPError(Exception):
    """
    MCP 클라이언트 오류 클래스
    """
    def __init__(self, message: str, status_code: int = 0, data: Dict = None):
        """
        MCP 오류 생성자
        
        Args:
            message: 오류 메시지
            status_code: HTTP 상태 코드
            data: 추가 오류 데이터
        """
        super().__init__(message)
        self.status_code = status_code
        self.data = data or {}


class ChatSession:
    """
    채팅 세션 클래스
    연속적인 대화를 위한 세션 관리
    """
    def __init__(self, client: 'MCPClient'):
        """
        채팅 세션 생성자
        
        Args:
            client: MCP 클라이언트 인스턴스
        """
        self.client = client
        self.session_id = None
        self.messages = []

    async def send_message(self, content: str, request_llm_config: Optional[CustomLLMConfig] = None) -> Dict:
        """
        메시지 전송
        
        Args:
            content: 사용자 메시지 내용
            request_llm_config: 이 요청에만 적용할 커스텀 LLM 설정 (선택 사항)
            
        Returns:
            채팅 응답
        """
        response = await self.client.chat(content, self.session_id, request_llm_config)
        
        # 세션 ID 저장
        self.session_id = response.get('session_id')
        
        # 메시지 기록 저장
        self.messages.append({
            'role': 'user',
            'content': content
        })
        
        self.messages.append({
            'role': 'assistant',
            'content': response.get('message', {}).get('content', '')
        })
        
        return response.get('message', {})

    def get_history(self) -> List[Dict]:
        """
        세션 기록 가져오기
        
        Returns:
            세션 메시지 기록
        """
        return self.messages.copy()

    def reset(self) -> None:
        """
        세션 초기화
        """
        self.session_id = None
        self.messages = []


class MCPClient:
    """
    MCP 클라이언트 클래스
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, 
                 llm_config: Optional[CustomLLMConfig] = None, search_api_key: Optional[str] = None,
                 search_engine_id: Optional[str] = None):
        """
        MCP 클라이언트 생성자
        
        Args:
            api_key: MCP 서버 인증을 위한 API 키 (기본값: 환경 변수 MCP_API_KEY)
            base_url: MCP 서버 기본 URL (기본값: 환경 변수 MCP_BASE_URL 또는 http://localhost:9000)
            llm_config: 커스텀 LLM 설정 (선택 사항)
            search_api_key: 검색 API 키 (기본값: 환경 변수 MCP_SEARCH_API_KEY)
            search_engine_id: 검색 엔진 ID (기본값: 환경 변수 MCP_SEARCH_ENGINE_ID)
        """
        # 환경 변수에서 설정 로드
        self.api_key = api_key or os.getenv('MCP_API_KEY')
        self.base_url = base_url or os.getenv('MCP_BASE_URL', 'http://localhost:9000')
        self.search_api_key = search_api_key or os.getenv('MCP_SEARCH_API_KEY')
        self.search_engine_id = search_engine_id or os.getenv('MCP_SEARCH_ENGINE_ID')
        
        # API 키가 없으면 오류 발생
        if not self.api_key:
            raise ValueError("API 키가 필요합니다. 매개변수로 전달하거나 MCP_API_KEY 환경 변수를 설정하세요.")
            
        self.session_id = None
        self.session = requests.Session()
        self.llm_config = llm_config

    async def request(self, endpoint: str, method: str = 'GET', data: Dict = None, params: Dict = None) -> Dict:
        """
        HTTP 요청을 보내는 유틸리티 메서드
        
        Args:
            endpoint: API 엔드포인트
            method: HTTP 메서드 (GET, POST 등)
            data: 요청 본문 데이터
            params: 쿼리 파라미터
            
        Returns:
            응답 데이터
        
        Raises:
            MCPError: API 요청 중 오류 발생 시
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        
        # 검색 API 키와 검색 엔진 ID가 있고 검색 관련 엔드포인트인 경우 헤더에 추가
        if endpoint.startswith('/search'):
            if self.search_api_key:
                headers['X-Search-API-Key'] = self.search_api_key
            if self.search_engine_id:
                headers['X-Search-Engine-ID'] = self.search_engine_id

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=headers, json=data, params=params)
            elif method.upper() == 'PUT':
                response = self.session.put(url, headers=headers, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers, params=params)
            else:
                raise MCPError(f"지원하지 않는 HTTP 메서드: {method}")

            response.raise_for_status()
            # 204 No Content 응답은 본문이 없으므로 빈 딕셔너리 반환
            if response.status_code == 204:
                return {}
            return response.json()

        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
            except ValueError:
                error_data = {'error': e.response.text}

            raise MCPError(
                f"API 오류: {error_data.get('error', {}).get('message', '알 수 없는 오류')}",
                e.response.status_code,
                error_data
            )
        except requests.exceptions.RequestException as e:
            raise MCPError(f"네트워크 오류: {str(e)}", data={'original_error': str(e)})

    async def check_health(self) -> Dict:
        """
        서버 상태 확인
        
        Returns:
            서버 상태 정보
        """
        return await self.request('/health')

    async def chat(self, message: str, session_id: Optional[str] = None, request_llm_config: Optional[CustomLLMConfig] = None) -> Dict:
        """
        채팅 메시지 전송
        
        Args:
            message: 사용자 메시지 내용
            session_id: 세션 ID (없으면 새 세션 생성)
            request_llm_config: 이 요청에만 적용할 커스텀 LLM 설정 (선택 사항)
            
        Returns:
            채팅 응답
        """
        data = {
            'session_id': session_id or self.session_id,
            'messages': [
                {
                    'content': message,
                    'role': 'user'
                }
            ]
        }
        
        # 요청별 커스텀 LLM 설정이 있는 경우 우선 적용
        llm_config_to_use = request_llm_config or self.llm_config
        
        # 커스텀 LLM 설정이 있는 경우 추가
        if llm_config_to_use:
            # to_dict 메서드를 사용하여 LLM 설정을 딕셔너리로 변환
            llm_config_dict = llm_config_to_use.to_dict()
            
            # API 키는 별도로 전달
            api_key = None
            if llm_config_to_use.api_key:
                api_key = llm_config_to_use.api_key
                
            # 데이터에 LLM 설정 추가
            data['llm_config'] = llm_config_dict
            if api_key:
                data['api_key'] = api_key
                
            # response_mapping은 더 이상 사용하지 않음

        response = await self.request('/api/v1/chat', 'POST', data)
        
        # 세션 ID 저장
        self.session_id = response.get('session_id')
        
        return response

    async def generate(self, prompt: str, max_tokens: int = 100, temperature: float = 0.7, request_llm_config: Optional[CustomLLMConfig] = None) -> Dict:
        """
        콘텐츠 생성
        
        Args:
            prompt: 생성 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 생성 온도 (창의성 조절)
            request_llm_config: 이 요청에만 적용할 커스텀 LLM 설정 (선택 사항)
            
        Returns:
            생성된 콘텐츠
        """
        data = {
            'prompt': prompt,
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        # 요청별 커스텀 LLM 설정이 있는 경우 우선 적용
        llm_config_to_use = request_llm_config or self.llm_config
        
        # 커스텀 LLM 설정이 있는 경우 추가
        if llm_config_to_use:
            # to_dict 메서드를 사용하여 LLM 설정을 딕셔너리로 변환
            llm_config_dict = llm_config_to_use.to_dict()
            
            # API 키는 별도로 전달
            api_key = None
            if llm_config_to_use.api_key:
                api_key = llm_config_to_use.api_key
                
            # 데이터에 LLM 설정 추가
            data['llm_config'] = llm_config_dict
            if api_key:
                data['api_key'] = api_key
                
            # response_mapping은 더 이상 사용하지 않음

        return await self.request('/api/v1/generate', 'POST', data)

    async def provide_feedback(self, request_id: str, rating: int, comment: str = '', feedback_type: str = 'general', request_llm_config: Optional[CustomLLMConfig] = None) -> Dict:
        """
        피드백 제공
        
        Args:
            request_id: 피드백을 제공할 요청 ID
            rating: 평점 (1-5)
            comment: 피드백 코멘트
            feedback_type: 피드백 유형 (예: 'general', 'accuracy', 'helpfulness' 등)
            request_llm_config: 이 요청에만 적용할 커스텀 LLM 설정 (선택 사항)
            
        Returns:
            피드백 응답
        """
        data = {
            'request_id': request_id,
            'rating': rating,
            'comment': comment,
            'feedback_type': feedback_type
        }
        
        # 요청별 커스텀 LLM 설정이 있는 경우 우선 적용
        llm_config_to_use = request_llm_config or self.llm_config
        
        # 커스텀 LLM 설정이 있는 경우 추가
        if llm_config_to_use:
            llm_data = {
                'model_name': llm_config_to_use.model_name,
                'model_endpoint': llm_config_to_use.model_endpoint
            }
            
            if llm_config_to_use.api_key:
                llm_data['api_key'] = llm_config_to_use.api_key
                
            if llm_config_to_use.parameters:
                llm_data['parameters'] = llm_config_to_use.parameters
                
            if llm_config_to_use.response_mapping:
                llm_data['response_mapping'] = llm_config_to_use.response_mapping
                
            data['llm_config'] = llm_data

        return await self.request('/api/v1/feedback', 'POST', data)

    async def get_feedback(self, request_id: str, request_llm_config: Optional[CustomLLMConfig] = None) -> Dict:
        """
        특정 요청에 대한 피드백 조회
        
        Args:
            request_id: 조회할 요청 ID
            request_llm_config: 이 요청에만 적용할 커스텀 LLM 설정 (선택 사항)
            
        Returns:
            피드백 정보
        """
        # 요청별 커스텀 LLM 설정이 있는 경우 우선 적용
        llm_config_to_use = request_llm_config or self.llm_config
        
        # 커스텀 LLM 설정이 있는 경우 추가
        params = {}
        if llm_config_to_use:
            llm_data = {
                'model_name': llm_config_to_use.model_name,
                'model_endpoint': llm_config_to_use.model_endpoint
            }
            
            if llm_config_to_use.api_key:
                llm_data['api_key'] = llm_config_to_use.api_key
                
            if llm_config_to_use.parameters:
                llm_data['parameters'] = llm_config_to_use.parameters
                
            if llm_config_to_use.response_mapping:
                llm_data['response_mapping'] = llm_config_to_use.response_mapping
                
            params['llm_config'] = llm_data
            
        return await self.request(f'/api/v1/feedback/request/{request_id}', 'GET', None, params)

    def create_chat_session(self) -> ChatSession:
        """
        새로운 채팅 세션 생성
        
        Returns:
            채팅 세션 객체
        """
        return ChatSession(self)


# 사용 예시
async def example():
    """
    MCP 클라이언트 사용 예시
    """
    try:
        # 기본 클라이언트 초기화
        client = MCPClient('***REMOVED***proj-uwz93kF9PT66Q2iBg1LebSe3L6pLgG87ttRFky7s2_vfBbiv-Wp6EiACzdp-ba5q_1TtOaJC6hT3BlbkFJL9ZQaEgkDB8cyXxurq8VNOJD-efqHEoSLXDhfGcvGmlUcacheJEDpp8u3oTLSGJv2fDqfRdpUA', 'http://localhost:9000')
        
        # 서버 상태 확인
        health_status = await client.check_health()
        print('서버 상태:', health_status)
        
        # 채팅 세션 생성
        session = client.create_chat_session()
        
        # 첫 번째 메시지 전송
        response1 = await session.send_message('안녕하세요, MCP!')
        print('AI 응답 1:', response1.get('content'))
        
        # 후속 메시지 전송 (세션 유지)
        response2 = await session.send_message('MCP 서버의 주요 기능은 무엇인가요?')
        print('AI 응답 2:', response2.get('content'))
        
        # 세션 기록 확인
        history = session.get_history()
        print('대화 기록:', history)
        
        # 콘텐츠 생성
        generated_content = await client.generate(
            '인공지능의 미래 발전 방향에 대해 설명해주세요',
            200,
            0.8
        )
        print('생성된 콘텐츠:', generated_content.get('content'))
        
        # 피드백 제공
        feedback_response = await client.provide_feedback(
            generated_content.get('request_id'),
            5,
            '매우 유용한 정보를 제공해주셔서 감사합니다!',
            'accuracy'  # 피드백 유형 추가
        )
        print('피드백 제출 완료:', feedback_response)
        
        print('\n=== 커스텀 LLM 사용 예시 ===')
        
        # 커스텀 LLM 설정 생성
        custom_llm_config = CustomLLMConfig(
            model='gpt-4',
            model_endpoint='https://api.openai.com/v1/chat/completions',
            api_key='***REMOVED***proj-uwz93kF9PT66Q2iBg1LebSe3L6pLgG87ttRFky7s2_vfBbiv-Wp6EiACzdp-ba5q_1TtOaJC6hT3BlbkFJL9ZQaEgkDB8cyXxurq8VNOJD-efqHEoSLXDhfGcvGmlUcacheJEDpp8u3oTLSGJv2fDqfRdpUA',
            temperature=0.8,
            max_tokens=500,
            options={
                'top_p': 0.95
            }
        )
        
        # 커스텀 LLM을 사용하는 클라이언트 생성
        custom_client = MCPClient('your-api-key', 'http://localhost:9000', custom_llm_config)
        
        # 커스텀 LLM으로 채팅
        custom_response = await custom_client.chat('커스텀 LLM을 사용한 질문입니다.')
        print('커스텀 LLM 응답:', custom_response.get('message', {}).get('content'))
        
        # 요청별 커스텀 LLM 설정 사용
        request_specific_config = CustomLLMConfig(
            model='claude-3-opus',
            model_endpoint='https://api.anthropic.com/v1/messages',
            api_key='***REMOVED***proj-uwz93kF9PT66Q2iBg1LebSe3L6pLgG87ttRFky7s2_vfBbiv-Wp6EiACzdp-ba5q_1TtOaJC6hT3BlbkFJL9ZQaEgkDB8cyXxurq8VNOJD-efqHEoSLXDhfGcvGmlUcacheJEDpp8u3oTLSGJv2fDqfRdpUA',
            temperature=0.5,
            max_tokens=1000
        )
        
        # 기본 클라이언트에서 요청별 커스텀 LLM 사용
        request_specific_response = await client.chat(
            '이 질문은 요청별 커스텀 LLM 설정을 사용합니다.',
            None,  # 세션 ID
            request_specific_config
        )
        print('요청별 커스텀 LLM 응답:', request_specific_response.get('message', {}).get('content'))
        
        # 커스텀 LLM으로 콘텐츠 생성
        custom_generated_content = await custom_client.generate(
            '커스텀 LLM을 사용한 콘텐츠 생성 예시입니다.',
            300,
            0.7
        )
        print('커스텀 LLM 생성 콘텐츠:', custom_generated_content.get('content'))
        
    except MCPError as e:
        print('오류 발생:', str(e))
        print('상태 코드:', e.status_code)
        print('오류 데이터:', e.data)
    except Exception as e:
        print('예상치 못한 오류:', str(e))


# 비동기 실행 예시 (asyncio 사용)
if __name__ == "__main__":
    import asyncio
    
    # 비동기 함수 실행
    asyncio.run(example())