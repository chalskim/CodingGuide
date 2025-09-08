#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP Python 클라이언트 사용 예제

이 예제는 .env 파일에서 설정을 로드하여 MCP 클라이언트를 사용하는 방법을 보여줍니다.
"""

import asyncio
from client_implementation import MCPClient, CustomLLMConfig

async def main():
    # .env 파일에서 설정을 로드하여 클라이언트 생성
    # 환경 변수: MCP_API_KEY, MCP_BASE_URL, MCP_SEARCH_API_KEY
    client = MCPClient()
    
    # 서버 상태 확인
    health = await client.check_health()
    print(f"서버 상태: {health}")
    
    # 채팅 메시지 전송
    response = await client.chat("안녕하세요, MCP!")
    print(f"AI 응답: {response['message']['content']}")
    
    # 커스텀 LLM 설정 사용
    custom_llm_config = CustomLLMConfig(
        model="gpt-4",
        model_endpoint="/v1/chat/completions",
        api_key=None,  # 환경 변수 ***REMOVED*** 사용
        temperature=0.7,
        max_tokens=1000
    )
    
    # 커스텀 LLM 설정으로 새 클라이언트 생성
    custom_client = MCPClient(llm_config=custom_llm_config)
    
    # 커스텀 LLM으로 채팅
    custom_response = await custom_client.chat("커스텀 LLM 설정으로 대화합니다.")
    print(f"커스텀 LLM 응답: {custom_response['message']['content']}")
    
    # 검색 기능은 현재 구현되어 있지 않아 주석 처리
    # search_response = await client.search("인공지능 최신 동향")
    # print(f"검색 결과: {search_response}")
    print("검색 기능 테스트 생략 - 아직 구현되지 않음")

if __name__ == "__main__":
    asyncio.run(main())