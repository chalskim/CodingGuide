#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
검색 API 키와 검색 엔진 ID를 사용하는 Python 클라이언트 예제
"""

import os
import asyncio
from dotenv import load_dotenv
from client_implementation import MCPClient

# .env 파일 로드 (없으면 환경 변수 사용)
load_dotenv()

async def main():
    # 환경 변수에서 설정 로드
    api_key = os.getenv('MCP_API_KEY')
    base_url = os.getenv('MCP_BASE_URL', 'http://localhost:9000')
    search_api_key = os.getenv('PERPLEXITY_API_KEY') or os.getenv('MCP_SEARCH_API_KEY')
    search_engine_id = os.getenv('MCP_SEARCH_ENGINE_ID')
    search_provider = os.getenv('SEARCH_PROVIDER', 'perplexity')
    
    # 클라이언트 생성
    client = MCPClient(
        api_key=api_key,
        base_url=base_url,
        search_api_key=search_api_key,
        search_engine_id=search_engine_id
    )
    
    # 다양한 검색 타입 테스트
    search_types = [
        {"type": "웹 검색", "search_type": "web", "query": "MCP 서버 아키텍처"},
        {"type": "뉴스 검색", "search_type": "news", "query": "인공지능 최신 뉴스"},
        {"type": "이미지 검색", "search_type": "image", "query": "파이썬 로고"}
    ]
    
    for search_config in search_types:
        try:
            print(f"\n===== {search_config['type']} =====")
            search_result = await client.request(
                method="POST",
                endpoint="/api/v1/search",
                data={
                    "query": search_config['query'],
                    "num_results": 3,
                    "search_provider": search_provider,
                    "search_type": search_config['search_type']
                }
            )
            
            print(f"검색 쿼리: {search_config['query']}")
            for i, result in enumerate(search_result.get("results", []), 1):
                print(f"{i}. {result.get('title')}")
                print(f"   URL: {result.get('link')}")
                print(f"   스니펫: {result.get('snippet')}")
                if search_config['search_type'] == 'image' and 'image_url' in result:
                    print(f"   이미지 URL: {result.get('image_url')}")
                print()
                
        except Exception as e:
            print(f"검색 요청 중 오류 발생: {e}")
            
    # 오류 처리 테스트 - 잘못된 검색 타입
    try:
        print("\n===== 오류 처리 테스트: 잘못된 검색 타입 =====")
        search_result = await client.request(
            method="POST",
            endpoint="/api/v1/search",
            data={
                "query": "테스트 쿼리",
                "search_type": "invalid_type",
                "search_provider": search_provider
            }
        )
        print("결과:", search_result)
    except Exception as e:
        print(f"예상된 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(main())