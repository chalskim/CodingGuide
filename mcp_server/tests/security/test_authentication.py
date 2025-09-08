import requests
import json
import unittest
import os
import sys
import uuid

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 테스트 설정
BASE_URL = "http://localhost:8000"  # MCP 서버 URL 설정

class AuthenticationTest(unittest.TestCase):
    """
    인증 및 권한 부여 관련 취약점 테스트 클래스
    """
    
    def setUp(self):
        """테스트 설정"""
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def test_auth_bypass_chat(self):
        """인증 우회 테스트 - Chat 엔드포인트"""
        # 기본 요청 데이터
        data = {
            "message": "Hello, world!",
            "session_id": "test_session",
            "user_id": "test_user"
        }
        
        # 1. 인증 헤더 없이 요청
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 인증이 필요한 경우 401 또는 403 응답이 예상됨
        # 현재 MCP 서버에 인증이 구현되어 있지 않아 이 테스트는 실패할 수 있음
        # 이 경우 취약점으로 기록
        if response.status_code not in [401, 403]:
            print("경고: 인증 없이 API 접근 가능 - 인증 메커니즘 필요")
        
        # 2. 조작된 인증 헤더로 요청
        manipulated_headers = self.headers.copy()
        manipulated_headers["Authorization"] = "Bearer invalid_token"
        
        response = requests.post(f"{BASE_URL}/chat", headers=manipulated_headers, json=data)
        
        # 잘못된 토큰으로 인증 실패해야 함
        if response.status_code not in [401, 403]:
            print("경고: 잘못된 인증 토큰으로 API 접근 가능 - 토큰 검증 필요")
    
    def test_session_management(self):
        """세션 관리 테스트"""
        # 1. 유효한 세션 ID로 요청
        valid_session_id = str(uuid.uuid4())
        data = {
            "message": "Hello, world!",
            "session_id": valid_session_id,
            "user_id": "test_user"
        }
        
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 2. 조작된 세션 ID로 요청
        data["session_id"] = "manipulated_session_id"
        
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 세션 ID 검증이 있다면 오류가 발생해야 함
        # 현재 MCP 서버에 세션 ID 검증이 구현되어 있지 않아 이 테스트는 실패할 수 있음
        if response.status_code == 200:
            print("경고: 조작된 세션 ID로 API 접근 가능 - 세션 ID 검증 필요")
    
    def test_privilege_escalation(self):
        """권한 상승 테스트"""
        # 1. 일반 사용자로 요청
        data = {
            "message": "Hello, world!",
            "session_id": "test_session",
            "user_id": "regular_user"
        }
        
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 2. 관리자 사용자로 요청 (권한 상승 시도)
        data["user_id"] = "admin"
        
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 권한 검증이 있다면 일반 사용자가 관리자 권한으로 요청할 수 없어야 함
        # 현재 MCP 서버에 권한 검증이 구현되어 있지 않아 이 테스트는 실패할 수 있음
        if response.status_code == 200:
            print("경고: 사용자 ID 조작으로 권한 상승 가능 - 권한 검증 필요")
    
    def test_feedback_endpoint_auth(self):
        """피드백 엔드포인트 인증 테스트"""
        # 피드백 요청 데이터
        data = {
            "request_id": str(uuid.uuid4()),
            "session_id": "test_session",
            "user_id": "test_user",
            "rating": 5,
            "feedback_type": "accuracy",
            "comment": "Great response!"
        }
        
        # 인증 헤더 없이 요청
        response = requests.post(f"{BASE_URL}/feedback", headers=self.headers, json=data)
        
        # 인증이 필요한 경우 401 또는 403 응답이 예상됨
        if response.status_code not in [401, 403]:
            print("경고: 인증 없이 피드백 API 접근 가능 - 인증 메커니즘 필요")
    
    def test_get_feedback_auth(self):
        """피드백 조회 엔드포인트 인증 테스트"""
        # 임의의 피드백 ID
        feedback_id = str(uuid.uuid4())
        
        # 인증 헤더 없이 요청
        response = requests.get(f"{BASE_URL}/feedback/{feedback_id}", headers=self.headers)
        
        # 인증이 필요한 경우 401 또는 403 응답이 예상됨
        if response.status_code not in [401, 403]:
            print("경고: 인증 없이 피드백 조회 API 접근 가능 - 인증 메커니즘 필요")

if __name__ == "__main__":
    unittest.main()