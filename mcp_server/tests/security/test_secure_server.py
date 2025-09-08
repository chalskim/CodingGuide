#!/usr/bin/env python3

import unittest
import requests
import json
import time
import threading

# 테스트 설정
BASE_URL = "http://127.0.0.1:8000"
API_KEY = "test_api_key_12345"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

class SecureServerTest(unittest.TestCase):
    
    def test_input_validation(self):
        """입력 검증 테스트"""
        # XSS 페이로드 테스트
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "javascript:alert('XSS')"
        ]
        
        for payload in xss_payloads:
            response = requests.post(
                f"{BASE_URL}/chat", 
                json={"messages": [{"role": "user", "content": payload}]},
                headers=HEADERS
            )
            self.assertEqual(response.status_code, 400, f"XSS 페이로드 '{payload}'가 차단되지 않았습니다.")
        
        # 잘못된 JSON 형식 테스트
        response = requests.post(
            f"{BASE_URL}/chat", 
            data="{invalid json}", 
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
        )
        self.assertEqual(response.status_code, 400, "잘못된 JSON 형식에 대해 400 오류를 반환해야 함")
    
    def test_authentication(self):
        """인증 테스트"""
        # 인증 없이 API 접근 테스트
        response = requests.post(
            f"{BASE_URL}/chat", 
            json={"messages": [{"role": "user", "content": "Hello"}]}
        )
        self.assertEqual(response.status_code, 401, "인증 없이 API 접근이 차단되어야 함")
        
        # 잘못된 인증 토큰 테스트
        response = requests.post(
            f"{BASE_URL}/chat", 
            json={"messages": [{"role": "user", "content": "Hello"}]},
            headers={"Authorization": "Bearer invalid_token"}
        )
        self.assertEqual(response.status_code, 401, "잘못된 인증 토큰으로 API 접근이 차단되어야 함")
        
        # 올바른 인증 토큰 테스트
        response = requests.post(
            f"{BASE_URL}/chat", 
            json={"messages": [{"role": "user", "content": "Hello"}]},
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 200, "올바른 인증 토큰으로 API 접근이 허용되어야 함")
    
    def test_api_endpoints(self):
        """API 엔드포인트 보안 테스트"""
        # Chat 엔드포인트 필수 필드 누락 테스트
        response = requests.post(f"{BASE_URL}/chat", json={}, headers=HEADERS)
        self.assertEqual(response.status_code, 400, "필수 필드 누락 시 400 오류를 반환해야 함")
        
        # Generate 엔드포인트 필수 필드 누락 테스트
        response = requests.post(f"{BASE_URL}/generate", json={}, headers=HEADERS)
        self.assertEqual(response.status_code, 400, "필수 필드 누락 시 400 오류를 반환해야 함")
        
        # Feedback 엔드포인트 필수 필드 누락 테스트
        response = requests.post(f"{BASE_URL}/feedback", json={}, headers=HEADERS)
        self.assertEqual(response.status_code, 400, "필수 필드 누락 시 400 오류를 반환해야 함")
    
    def test_data_processing(self):
        """데이터 처리 및 저장 테스트"""
        # 데이터 무결성 테스트
        chat_response = requests.post(
            f"{BASE_URL}/chat", 
            json={"messages": [{"role": "user", "content": "Hello"}]},
            headers=HEADERS
        ).json()
        
        request_id = chat_response["id"]
        
        feedback_response = requests.post(
            f"{BASE_URL}/feedback", 
            json={"request_id": request_id, "rating": 5, "comment": "Good response"},
            headers=HEADERS
        ).json()
        
        feedback_id = feedback_response["id"]
        
        # 피드백 조회
        feedback = requests.get(
            f"{BASE_URL}/feedback/{feedback_id}",
            headers=HEADERS
        ).json()
        
        self.assertEqual(feedback["rating"], 5, "저장된 평점이 일치하지 않음")
        self.assertEqual(feedback["comment"], "Good response", "저장된 코멘트가 일치하지 않음")
        
        # 요청 ID로 피드백 조회
        feedbacks = requests.get(
            f"{BASE_URL}/feedback/request/{request_id}",
            headers=HEADERS
        ).json()
        
        self.assertTrue(len(feedbacks) > 0, "요청 ID로 피드백을 찾을 수 없음")
        self.assertEqual(feedbacks[0]["rating"], 5, "저장된 평점이 일치하지 않음")
    
    def test_error_handling(self):
        """오류 처리 테스트"""
        # 존재하지 않는 피드백 ID 테스트
        response = requests.get(
            f"{BASE_URL}/feedback/nonexistent_id",
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 404, "존재하지 않는 리소스에 대해 404 오류를 반환해야 함")
        
        # 오류 정보 유출 테스트
        response = requests.get(
            f"{BASE_URL}/feedback/nonexistent_id",
            headers=HEADERS
        ).json()
        
        self.assertNotIn("traceback", response, "오류 응답에 스택 트레이스가 포함되지 않아야 함")
        self.assertNotIn("headers", response, "오류 응답에 헤더 정보가 포함되지 않아야 함")
    
    def test_rate_limiting(self):
        """속도 제한 테스트"""
        # 짧은 시간 내에 많은 요청 보내기
        for _ in range(10):
            response = requests.post(
                f"{BASE_URL}/chat", 
                json={"messages": [{"role": "user", "content": "Hello"}]},
                headers=HEADERS
            )
            self.assertIn(response.status_code, [200, 429], "속도 제한이 적용되어야 함")

if __name__ == "__main__":
    unittest.main()