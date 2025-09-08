import asyncio
import sys
import os
import json
from datetime import datetime

# 로컬 client_implementation.py에서 MCPClient 임포트
from client_implementation import MCPClient

async def main():
    # MCP 클라이언트 생성
    client = MCPClient(
        base_url="http://localhost:9000",
        api_key=None  # 처음에는 API 키 없이 시작
    )
    
    print("\n1. API 키 생성 테스트")
    try:
        # API 키 생성 요청
        response = await client.request(
            "/api/v1/auth/keys",
            method="POST",
            data={
                "user_id": "test_user",
                "description": "API 키 생성 테스트",
                "expires_in_days": 30
            }
        )
        
        print(f"API 키 생성 성공: {response}")
        api_key = response.get("api_key")
        key_id = response.get("key_id")
        
        # 생성된 API 키로 클라이언트 업데이트
        client.api_key = api_key
        print(f"API 키 설정: {api_key}")
    except Exception as e:
        print(f"API 키 생성 실패: {e}")
        return
    
    print("\n2. API 키 정보 조회 테스트")
    try:
        # API 키 정보 조회 요청
        response = await client.request(
            f"/api/v1/auth/keys/{key_id}",
            method="GET"
        )
        print(f"API 키 정보 조회 성공: {response}")
    except Exception as e:
        print(f"API 키 정보 조회 실패: {e}")
    
    print("\n3. 인증이 필요한 API 호출 테스트")
    try:
        # 검색 API 호출 (인증 필요)
        response = await client.request(
            "/api/v1/search",
            method="POST",
            data={
                "query": "MCP 프로토콜",
                "num_results": 3,
                "search_type": "web"
            }
        )
        print(f"검색 API 호출 성공: {json.dumps(response, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"검색 API 호출 실패: {e}")
    
    print("\n4. API 키 비활성화 테스트")
    try:
        # API 키 비활성화 요청
        response = await client.request(
            f"/api/v1/auth/keys/{key_id}",
            method="DELETE"
        )
        print(f"API 키 비활성화 성공")
        
        # 비활성화된 API 키로 API 호출 시도
        try:
            response = await client.request(
                f"/api/v1/auth/keys/{key_id}",
                method="GET"
            )
            print(f"비활성화된 API 키로 호출 성공 (예상치 못한 결과): {response}")
        except Exception as e:
            print(f"비활성화된 API 키로 호출 실패 (예상된 결과): {e}")
    except Exception as e:
        print(f"API 키 비활성화 실패: {e}")

if __name__ == "__main__":
    asyncio.run(main())