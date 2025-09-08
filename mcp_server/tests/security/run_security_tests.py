#!/usr/bin/env python3

import unittest
import os
import sys
import argparse
import requests
import time
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 테스트 모듈 임포트
from test_input_validation import InputValidationTest
from test_authentication import AuthenticationTest
from test_api_endpoints import APIEndpointSecurityTest
from test_data_processing import DataProcessingTest

# 테스트 설정
BASE_URL = "http://localhost:8000"  # MCP 서버 URL 설정

def check_server_availability():
    """MCP 서버가 실행 중인지 확인"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def run_tests(test_modules=None):
    """지정된 테스트 모듈 실행"""
    # 서버 가용성 확인
    if not check_server_availability():
        print("오류: MCP 서버가 실행 중이지 않습니다. 서버를 시작한 후 다시 시도하세요.")
        return False
    
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 모든 테스트 모듈 목록
    all_test_modules = {
        "input": InputValidationTest,
        "auth": AuthenticationTest,
        "api": APIEndpointSecurityTest,
        "data": DataProcessingTest
    }
    
    # 실행할 테스트 모듈 선택
    if test_modules:
        modules_to_run = {}
        for module in test_modules:
            if module in all_test_modules:
                modules_to_run[module] = all_test_modules[module]
            else:
                print(f"경고: 알 수 없는 테스트 모듈 '{module}'")
    else:
        modules_to_run = all_test_modules
    
    # 테스트 스위트에 테스트 추가
    for name, module in modules_to_run.items():
        print(f"테스트 모듈 추가: {name}")
        suite.addTest(loader.loadTestsFromTestCase(module))
    
    # 테스트 실행
    print("\n취약성 테스트 시작...\n")
    start_time = time.time()
    
    # 테스트 결과를 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"security_test_results_{timestamp}.txt"
    
    with open(result_file, "w") as f:
        # 테스트 헤더 작성
        f.write("=" * 80 + "\n")
        f.write(f"MCP 서버 취약성 테스트 결과 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # 테스트 실행
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        result = runner.run(suite)
        
        # 테스트 요약 작성
        f.write("\n" + "=" * 80 + "\n")
        f.write("테스트 요약:\n")
        f.write(f"실행된 테스트: {result.testsRun}\n")
        f.write(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}\n")
        f.write(f"실패: {len(result.failures)}\n")
        f.write(f"오류: {len(result.errors)}\n")
        f.write(f"소요 시간: {time.time() - start_time:.2f}초\n")
        f.write("=" * 80 + "\n")
    
    # 콘솔에 결과 출력
    print("\n" + "=" * 80)
    print("테스트 요약:")
    print(f"실행된 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    print(f"소요 시간: {time.time() - start_time:.2f}초")
    print(f"결과 파일: {result_file}")
    print("=" * 80)
    
    return len(result.failures) == 0 and len(result.errors) == 0

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="MCP 서버 취약성 테스트 실행")
    parser.add_argument(
        "--modules", 
        nargs="+", 
        choices=["input", "auth", "api", "data", "all"], 
        default=["all"],
        help="실행할 테스트 모듈 (input: 입력 검증, auth: 인증, api: API 엔드포인트, data: 데이터 처리, all: 모두)"
    )
    
    args = parser.parse_args()
    
    # 모든 테스트 실행 여부 확인
    if "all" in args.modules:
        test_modules = None
    else:
        test_modules = args.modules
    
    # 테스트 실행
    success = run_tests(test_modules)
    
    # 종료 코드 설정
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()