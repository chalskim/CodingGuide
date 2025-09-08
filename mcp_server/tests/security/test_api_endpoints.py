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

class APIEndpointSecurityTest(unittest.TestCase):
    """
    API 엔드포인트 보안 취약점 테스트 클래스
    """
    
    def setUp(self):
        """테스트 설정"""
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def test_chat_endpoint_security(self):
        """Chat 엔드포인트 보안 테스트"""
        # 1. 필수 필드 누락 테스트
        data = {
            # "message" 필드 누락
            "session_id": "test_session",
            "user_id": "test_user"
        }
        
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 필수 필드 누락 시 400 오류가 예상됨
        self.assertEqual(response.status_code, 400, "필수 필드 누락 시 400 오류를 반환해야 함")
        
        # 2. 잘못된 데이터 타입 테스트
        data = {
            "message": 12345,  # 문자열이 아닌 숫자
            "session_id": "test_session",
            "user_id": "test_user"
        }
        
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 잘못된 데이터 타입 시 400 오류가 예상됨
        self.assertEqual(response.status_code, 400, "잘못된 데이터 타입 시 400 오류를 반환해야 함")
        
        # 3. 추가 필드 테스트
        data = {
            "message": "Hello, world!",
            "session_id": "test_session",
            "user_id": "test_user",
            "malicious_field": "<script>alert('XSS')</script>"
        }
        
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 추가 필드는 무시되어야 하며 서버 오류가 발생하지 않아야 함
        self.assertNotEqual(response.status_code, 500, "추가 필드 처리 시 서버 오류 발생")
    
    def test_generate_endpoint_security(self):
        """Generate 엔드포인트 보안 테스트"""
        # 1. 필수 필드 누락 테스트
        data = {
            # "prompt" 필드 누락
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(f"{BASE_URL}/generate", headers=self.headers, json=data)
        
        # 필수 필드 누락 시 400 오류가 예상됨
        self.assertEqual(response.status_code, 400, "필수 필드 누락 시 400 오류를 반환해야 함")
        
        # 2. 잘못된 데이터 타입 테스트
        data = {
            "prompt": "Generate some text",
            "max_tokens": "not_a_number",  # 숫자가 아닌 문자열
            "temperature": 0.7
        }
        
        response = requests.post(f"{BASE_URL}/generate", headers=self.headers, json=data)
        
        # 잘못된 데이터 타입 시 400 오류가 예상됨
        self.assertEqual(response.status_code, 400, "잘못된 데이터 타입 시 400 오류를 반환해야 함")
        
        # 3. 범위를 벗어난 값 테스트
        data = {
            "prompt": "Generate some text",
            "max_tokens": 1000,
            "temperature": 2.0  # 0.0 ~ 1.0 범위를 벗어남
        }
        
        response = requests.post(f"{BASE_URL}/generate", headers=self.headers, json=data)
        
        # 범위를 벗어난 값 시 400 오류가 예상됨
        self.assertEqual(response.status_code, 400, "범위를 벗어난 값 시 400 오류를 반환해야 함")
    
    def test_feedback_endpoint_security(self):
        """Feedback 엔드포인트 보안 테스트"""
        # 1. 필수 필드 누락 테스트
        data = {
            # "request_id" 필드 누락
            "rating": 5,
            "feedback_type": "accuracy"
        }
        
        response = requests.post(f"{BASE_URL}/feedback", headers=self.headers, json=data)
        
        # 필수 필드 누락 시 400 오류가 예상됨
        self.assertEqual(response.status_code, 400, "필수 필드 누락 시 400 오류를 반환해야 함")
        
        # 2. 잘못된 데이터 타입 테스트
        data = {
            "request_id": str(uuid.uuid4()),
            "rating": "five",  # 숫자가 아닌 문자열
            "feedback_type": "accuracy"
        }
        
        response = requests.post(f"{BASE_URL}/feedback", headers=self.headers, json=data)
        
        # 잘못된 데이터 타입 시 400 오류가 예상됨
        self.assertEqual(response.status_code, 400, "잘못된 데이터 타입 시 400 오류를 반환해야 함")
        
        # 3. 범위를 벗어난 값 테스트
        data = {
            "request_id": str(uuid.uuid4()),
            "rating": 10,  # 1-5 범위를 벗어남
            "feedback_type": "accuracy"
        }
        
        response = requests.post(f"{BASE_URL}/feedback", headers=self.headers, json=data)
        
        # 범위를 벗어난 값 시 400 오류가 예상됨
        self.assertEqual(response.status_code, 400, "범위를 벗어난 값 시 400 오류를 반환해야 함")
    
    def test_http_methods(self):
        """허용되지 않은 HTTP 메서드 테스트"""
        # 1. OPTIONS 메서드 테스트
        response = requests.options(f"{BASE_URL}/chat")
        
        # OPTIONS 메서드는 CORS를 위해 허용될 수 있음
        print(f"OPTIONS 메서드 응답 코드: {response.status_code}")
        
        # 2. PUT 메서드 테스트
        data = {
            "message": "Hello, world!",
            "session_id": "test_session",
            "user_id": "test_user"
        }
        
        response = requests.put(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # PUT 메서드는 허용되지 않아야 함 (405 Method Not Allowed)
        self.assertEqual(response.status_code, 405, "PUT 메서드는 허용되지 않아야 함")
        
        # 3. DELETE 메서드 테스트
        response = requests.delete(f"{BASE_URL}/chat")
        
        # DELETE 메서드는 허용되지 않아야 함 (405 Method Not Allowed)
        self.assertEqual(response.status_code, 405, "DELETE 메서드는 허용되지 않아야 함")
    
    def test_header_injection(self):
        """HTTP 헤더 인젝션 테스트"""
        # 조작된 헤더 값으로 요청
        manipulated_headers = self.headers.copy()
        manipulated_headers["X-Forwarded-For"] = "127.0.0.1\r\nX-Injected: value"
        
        data = {
            "message": "Hello, world!",
            "session_id": "test_session",
            "user_id": "test_user"
        }
        
        response = requests.post(f"{BASE_URL}/chat", headers=manipulated_headers, json=data)
        
        # 헤더 인젝션이 차단되어야 함
        self.assertNotEqual(response.status_code, 500, "헤더 인젝션 시 서버 오류 발생")

if __name__ == "__main__":
    unittest.main()