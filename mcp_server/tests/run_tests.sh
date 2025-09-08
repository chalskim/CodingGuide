#!/bin/bash

# MCP 서버 테스트 실행 스크립트

echo "MCP 서버 테스트 시작..."

# 현재 디렉토리를 프로젝트 루트로 변경
cd "$(dirname "$0")/.." || exit 1

# 가상 환경 활성화 (필요한 경우 주석 해제)
# source venv/bin/activate

# 단위 테스트 실행
echo "\n단위 테스트 실행 중..."
pytest tests/unit -v

# 통합 테스트 실행
echo "\n통합 테스트 실행 중..."
pytest tests/integration -v

# 전체 테스트 커버리지 보고서 생성 (선택 사항)
echo "\n테스트 커버리지 보고서 생성 중..."
pytest --cov=app tests/ --cov-report=term-missing

echo "\n모든 테스트 완료!"