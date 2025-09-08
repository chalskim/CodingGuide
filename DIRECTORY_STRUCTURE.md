# MCP 서버 디렉토리 구조

이 문서는 MCP 서버 프로젝트의 디렉토리 구조와 각 파일 및 폴더의 역할을 설명합니다.

## 최상위 디렉토리

```
/
├── mcp_server/         # 메인 소스 코드
├── tests/              # 테스트 코드
├── docs/               # 문서
├── scripts/            # 유틸리티 스크립트
├── .env.example        # 환경 변수 예제 파일
├── .gitignore          # Git 무시 파일 목록
├── API.md              # API 문서
├── CONTRIBUTING.md     # 기여 가이드라인
├── DIRECTORY_STRUCTURE.md # 디렉토리 구조 설명
├── INSTALL.md          # 설치 가이드
├── LICENSE             # 라이선스 정보
├── README.md           # 프로젝트 개요
├── SECURITY.md         # 보안 정책
├── docker-compose.yml  # Docker Compose 설정
├── Dockerfile          # Docker 빌드 설정
├── requirements.txt    # 의존성 목록
└── requirements-dev.txt # 개발 의존성 목록
```

## mcp_server 디렉토리

```
mcp_server/
├── __init__.py         # 패키지 초기화
├── main.py             # 애플리케이션 진입점
├── config.py           # 설정 관리
├── api/                # API 엔드포인트
│   ├── __init__.py
│   ├── chat.py         # 채팅 API
│   ├── generate.py     # 콘텐츠 생성 API
│   └── feedback.py     # 피드백 API
├── core/               # 핵심 기능
│   ├── __init__.py
│   ├── session.py      # 세션 관리
│   ├── security.py     # 보안 기능
│   └── rate_limit.py   # 속도 제한
├── models/             # 데이터 모델
│   ├── __init__.py
│   ├── chat.py         # 채팅 관련 모델
│   ├── generate.py     # 생성 관련 모델
│   └── feedback.py     # 피드백 관련 모델
├── utils/              # 유틸리티 함수
│   ├── __init__.py
│   ├── sanitize.py     # 입력 검증 및 이스케이프
│   ├── logging.py      # 로깅 유틸리티
│   └── helpers.py      # 기타 헬퍼 함수
└── db/                 # 데이터베이스 관련
    ├── __init__.py
    ├── models.py       # 데이터베이스 모델
    └── migrations/     # 데이터베이스 마이그레이션
```

## tests 디렉토리

```
tests/
├── __init__.py
├── conftest.py         # pytest 설정
├── unit/               # 단위 테스트
│   ├── __init__.py
│   ├── test_api/       # API 테스트
│   ├── test_core/      # 핵심 기능 테스트
│   └── test_utils/     # 유틸리티 테스트
├── integration/        # 통합 테스트
│   ├── __init__.py
│   └── test_endpoints/ # 엔드포인트 통합 테스트
└── security/           # 보안 테스트
    ├── __init__.py
    ├── test_secure_server.py # 보안 서버 테스트
    └── secure_mock_server.py # 보안 테스트용 목 서버
```

## docs 디렉토리

```
docs/
├── api/                # API 문서
├── architecture/       # 아키텍처 문서
├── development/        # 개발 가이드
└── security/           # 보안 문서
```

## scripts 디렉토리

```
scripts/
├── setup.sh            # 설치 스크립트
├── run_tests.sh        # 테스트 실행 스크립트
└── deploy.sh           # 배포 스크립트
```

## 주요 파일 설명

### 최상위 파일

- **main.py**: 애플리케이션의 진입점으로, FastAPI 애플리케이션을 초기화하고 실행합니다.
- **config.py**: 환경 변수 및 설정을 관리합니다.
- **.env.example**: 필요한 환경 변수의 예제를 제공합니다.
- **requirements.txt**: 프로젝트 의존성 목록을 포함합니다.
- **docker-compose.yml**: Docker Compose 설정을 정의합니다.

### API 디렉토리

- **chat.py**: 채팅 관련 API 엔드포인트를 정의합니다.
- **generate.py**: 콘텐츠 생성 API 엔드포인트를 정의합니다.
- **feedback.py**: 피드백 관련 API 엔드포인트를 정의합니다.

### 핵심 기능 디렉토리

- **session.py**: 사용자 세션 관리 기능을 구현합니다.
- **security.py**: 인증, 권한 부여 및 기타 보안 기능을 구현합니다.
- **rate_limit.py**: API 요청 속도 제한 기능을 구현합니다.

### 모델 디렉토리

- **chat.py**: 채팅 관련 Pydantic 모델을 정의합니다.
- **generate.py**: 콘텐츠 생성 관련 Pydantic 모델을 정의합니다.
- **feedback.py**: 피드백 관련 Pydantic 모델을 정의합니다.

### 유틸리티 디렉토리

- **sanitize.py**: 입력 검증 및 이스케이프 함수를 제공합니다.
- **logging.py**: 로깅 설정 및 유틸리티를 제공합니다.
- **helpers.py**: 다양한 헬퍼 함수를 제공합니다.

### 데이터베이스 디렉토리

- **models.py**: 데이터베이스 모델을 정의합니다.
- **migrations/**: 데이터베이스 스키마 변경을 관리합니다.

## 개발 워크플로우

1. **기능 개발**: `mcp_server/` 디렉토리 내에서 관련 모듈을 수정하거나 추가합니다.
2. **테스트 작성**: `tests/` 디렉토리에 새 기능에 대한 테스트를 추가합니다.
3. **테스트 실행**: `scripts/run_tests.sh`를 사용하여 테스트를 실행합니다.
4. **문서 업데이트**: 필요한 경우 `docs/` 디렉토리의 문서를 업데이트합니다.
5. **변경 사항 커밋**: 변경 사항을 커밋하고 풀 리퀘스트를 생성합니다.

## 코드 스타일 및 규칙

- 모든 Python 코드는 PEP 8 스타일 가이드를 따릅니다.
- 모든 함수, 클래스, 메서드에는 문서 문자열(docstring)이 있어야 합니다.
- 모든 API 엔드포인트는 적절한 입력 검증을 포함해야 합니다.
- 보안 관련 코드는 `SECURITY.md`의 지침을 따라야 합니다.