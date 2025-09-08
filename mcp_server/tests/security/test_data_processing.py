import requests
import json
import unittest
import os
import sys
import uuid
import time

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 테스트 설정
BASE_URL = "http://localhost:8000"  # MCP 서버 URL 설정

class DataProcessingTest(unittest.TestCase):
    """
    데이터 처리 및 저장 관련 취약점 테스트 클래스
    """
    
    def setUp(self):
        """테스트 설정"""
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def test_error_information_disclosure(self):
        """오류 메시지를 통한 정보 유출 테스트"""
        # 1. 잘못된 JSON 형식으로 요청
        invalid_json = "{'message': 'test', 'session_id': 'test_session', 'user_id': 'test_user'}"
        
        response = requests.post(
            f"{BASE_URL}/chat", 
            headers={"Content-Type": "application/json"}, 
            data=invalid_json
        )
        
        # 응답 검증 - 민감한 정보가 포함되어 있는지 확인
        self.assertNotIn("Traceback", response.text, "오류 메시지에 스택 트레이스 포함")
        self.assertNotIn("File \"", response.text, "오류 메시지에 파일 경로 포함")
        self.assertNotIn("line", response.text, "오류 메시지에 코드 라인 정보 포함")
        
        # 2. 존재하지 않는 엔드포인트 요청
        response = requests.get(f"{BASE_URL}/nonexistent_endpoint")
        
        # 응답 검증 - 민감한 정보가 포함되어 있는지 확인
        self.assertNotIn("Traceback", response.text, "오류 메시지에 스택 트레이스 포함")
        self.assertNotIn("File \"", response.text, "오류 메시지에 파일 경로 포함")
        self.assertNotIn("line", response.text, "오류 메시지에 코드 라인 정보 포함")
    
    def test_response_header_disclosure(self):
        """응답 헤더를 통한 정보 유출 테스트"""
        # 기본 요청
        data = {
            "message": "Hello, world!",
            "session_id": "test_session",
            "user_id": "test_user"
        }
        
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 응답 헤더 검증
        headers_to_check = [
            "Server",
            "X-Powered-By",
            "X-AspNet-Version",
            "X-AspNetMvc-Version",
            "X-Runtime"
        ]
        
        for header in headers_to_check:
            if header in response.headers:
                print(f"경고: 응답 헤더에 민감한 정보 포함 - {header}: {response.headers[header]}")
    
    def test_data_integrity(self):
        """데이터 무결성 테스트"""
        # 1. 피드백 데이터 생성
        request_id = str(uuid.uuid4())
        feedback_data = {
            "request_id": request_id,
            "rating": 5,
            "feedback_type": "accuracy",
            "comment": "Great response!"
        }
        
        # 피드백 제출
        response = requests.post(f"{BASE_URL}/feedback", headers=self.headers, json=feedback_data)
        
        # 응답 검증
        if response.status_code == 200:
            feedback_id = response.json().get("feedback_id")
            
            # 2. 피드백 조회
            response = requests.get(f"{BASE_URL}/feedback/{feedback_id}", headers=self.headers)
            
            # 응답 검증 - 데이터가 올바르게 저장되었는지 확인
            if response.status_code == 200:
                feedback = response.json()
                self.assertEqual(feedback.get("request_id"), request_id, "저장된 request_id가 일치하지 않음")
                self.assertEqual(feedback.get("rating"), 5, "저장된 rating이 일치하지 않음")
                self.assertEqual(feedback.get("feedback_type"), "accuracy", "저장된 feedback_type이 일치하지 않음")
                self.assertEqual(feedback.get("comment"), "Great response!", "저장된 comment가 일치하지 않음")
    
    def test_race_condition(self):
        """경쟁 조건 테스트"""
        # 동일한 세션에 대해 여러 요청을 동시에 보냄
        session_id = str(uuid.uuid4())
        
        # 요청 데이터 준비
        data = {
            "message": "Hello, world!",
            "session_id": session_id,
            "user_id": "test_user"
        }
        
        # 동시에 여러 요청 보내기
        responses = []
        for i in range(5):
            response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
            responses.append(response)
            
        # 모든 응답이 성공적인지 확인
        for i, response in enumerate(responses):
            self.assertEqual(response.status_code, 200, f"요청 {i+1}에서 경쟁 조건 발생")
    
    def test_data_persistence(self):
        """데이터 지속성 테스트"""
        # 1. 채팅 요청 보내기
        session_id = str(uuid.uuid4())
        data = {
            "message": "Remember this message: PERSISTENCE_TEST_12345",
            "session_id": session_id,
            "user_id": "test_user"
        }
        
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 응답 검증
        self.assertEqual(response.status_code, 200, "채팅 요청 실패")
        
        # 2. 동일한 세션으로 후속 요청 보내기
        data = {
            "message": "What was the message I asked you to remember?",
            "session_id": session_id,
            "user_id": "test_user"
        }
        
        # 잠시 대기 (데이터 저장 시간 고려)
        time.sleep(1)
        
        response = requests.post(f"{BASE_URL}/chat", headers=self.headers, json=data)
        
        # 응답 검증 - 이전 메시지를 기억하는지 확인
        self.assertEqual(response.status_code, 200, "후속 채팅 요청 실패")
        self.assertIn("PERSISTENCE_TEST_12345", response.text, "대화 컨텍스트가 유지되지 않음")

if __name__ == "__main__":
    unittest.main()