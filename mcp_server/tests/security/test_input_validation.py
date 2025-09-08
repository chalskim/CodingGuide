import requests
import json
import unittest
import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 테스트 설정
BASE_URL = "http://localhost:8000"  # MCP 서버 URL 설정

class InputValidationTest(unittest.TestCase):
    """
    입력 검증 관련 취약점 테스트 클래스
    """
    
    def setUp(self):
        """테스트 설정"""
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def test_sql_injection_chat(self):
        """SQL 인젝션 테스트 - Chat 엔드포인트"""
        # SQL 인젝션 페이로드 목록
        payloads = [
            "' OR '1'='1",
            "\" OR \"1\"=\"1",
            "1; DROP TABLE users;",
            "' UNION SELECT username, password FROM users; --",
            "admin'--"
        ]
        
        for payload in payloads:
            # 테스트할 요청 데이터
            data = {
                "message": payload,
                "session_id": "test_session",
                "user_id": "test_user"
            }
            
            # 요청 전송
            response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
            
            # 응답 검증
            self.assertNotIn("SQL syntax", response.text, f"SQL 인젝션 취약점 발견: {payload}")
            self.assertNotIn("ORA-", response.text, f"Oracle SQL 인젝션 취약점 발견: {payload}")
            self.assertNotIn("mysql_fetch_array", response.text, f"MySQL 인젝션 취약점 발견: {payload}")
    
    def test_xss_chat(self):
        """XSS 취약점 테스트 - Chat 엔드포인트"""
        # XSS 페이로드 목록
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<a href=\"javascript:alert('XSS')\">Click me</a>"
        ]
        
        for payload in payloads:
            # 테스트할 요청 데이터
            data = {
                "message": payload,
                "session_id": "test_session",
                "user_id": "test_user"
            }
            
            # 요청 전송
            response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
            
            # 응답 검증 - 스크립트가 그대로 반환되는지 확인
            if payload in response.text:
                print(f"경고: XSS 취약점 발견 - 페이로드가 응답에 그대로 포함됨: {payload}")
    
    def test_input_length_chat(self):
        """입력 길이 제한 테스트 - Chat 엔드포인트"""
        # 매우 긴 입력 생성 (100KB)
        long_input = "A" * 100000
        
        # 테스트할 요청 데이터
        data = {
            "message": long_input,
            "session_id": "test_session",
            "user_id": "test_user"
        }
        
        # 요청 전송
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 응답 검증 - 서버가 적절히 처리하는지 확인
        self.assertNotEqual(response.status_code, 500, "서버 오류: 긴 입력에 대한 처리 실패")
    
    def test_special_chars_chat(self):
        """특수 문자 및 유니코드 처리 테스트 - Chat 엔드포인트"""
        # 특수 문자 및 유니코드 문자 목록
        payloads = [
            "!@#$%^&*()_+{}[]:;\"'<>,.?/~`|",
            "한글 테스트",
            "日本語テスト",
            "Русский тест",
            "😀😁😂🤣😃😄😅"
        ]
        
        for payload in payloads:
            # 테스트할 요청 데이터
            data = {
                "message": payload,
                "session_id": "test_session",
                "user_id": "test_user"
            }
            
            # 요청 전송
            response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
            
            # 응답 검증 - 서버가 특수 문자를 적절히 처리하는지 확인
            self.assertNotEqual(response.status_code, 500, f"서버 오류: 특수 문자 처리 실패 - {payload}")

    def test_invalid_json_chat(self):
        """잘못된 JSON 형식 테스트 - Chat 엔드포인트"""
        # 잘못된 JSON 데이터
        invalid_json = "{'message': 'test', 'session_id': 'test_session', 'user_id': 'test_user'}"
        
        # 요청 전송
        response = requests.post(
            f"{BASE_URL}/chat", 
            headers={"Content-Type": "application/json"}, 
            data=invalid_json
        )
        
        # 응답 검증 - 서버가 적절한 오류 메시지를 반환하는지 확인
        self.assertNotEqual(response.status_code, 500, "서버 오류: 잘못된 JSON 형식 처리 실패")
        self.assertEqual(response.status_code, 400, "잘못된 JSON 형식에 대해 400 오류를 반환해야 함")

if __name__ == "__main__":
    unittest.main()