# MCP (Multi-Context Protocol) 서버

## 1. 개발 목적

MCP 서버는 다양한 컨텍스트와 프로토콜을 통합하여 AI 시스템과 사용자 간의 효율적인 상호작용을 지원하기 위해 개발되었습니다. 이 서버는 다음과 같은 목적을 가지고 있습니다:

- 다양한 지식 소스와 데이터베이스에 대한 통합 액세스 제공
- 사용자 요청에 대한 컨텍스트 인식 처리 지원
- 보안 및 안정성이 강화된 AI 서비스 인프라 구축
- 확장 가능하고 유연한 프로토콜 아키텍처 제공

## 2. 사용 시 장점

### 통합된 컨텍스트 관리
- 다양한 지식 소스와 데이터베이스를 단일 인터페이스로 통합
- 컨텍스트 기반 요청 처리로 더 정확한 응답 생성
- 사용자 세션 관리를 통한 일관된 상호작용 유지

### 강화된 보안
- XSS 및 인젝션 공격에 대한 강력한 방어 메커니즘
- 입력 검증 및 이스케이프 처리를 통한 데이터 보호
- API 키 기반 인증 및 세션 관리
- 안전한 API 키 생성, 관리 및 비활성화 기능

### 확장성 및 유연성
- 모듈식 아키텍처로 새로운 프로토콜 및 기능 쉽게 추가 가능
- 다양한 AI 모델 및 서비스와의 통합 지원
- 고성능 비동기 처리를 통한 효율적인 리소스 관리

## 3. 설치 방법

### 요구 사항
- Python 3.8 이상
- Docker 및 Docker Compose (선택 사항)
- Node.js 14 이상 (JavaScript 클라이언트 사용 시)
- Java 11 이상 (Java 클라이언트 사용 시)

### 로컬 설치

1. 저장소 클론
```bash
git clone https://github.com/your-username/mcp-server.git
cd mcp-server
```

2. 가상 환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정 값을 입력하세요
```

4. 의존성 설치
```bash
pip install -r requirements.txt
```



5. 서버 실행
```bash
cd mcp_server
python -m app.main
```

## 4. 클라이언트 사용 방법

### 환경 변수 설정

MCP 클라이언트는 `.env` 파일에서 설정을 로드할 수 있습니다. 다음 환경 변수를 설정하세요:

```
# 클라이언트 설정
MCP_API_KEY=your-mcp-api-key
MCP_BASE_URL=http://localhost:9000
MCP_SEARCH_API_KEY=your-search-api-key
```

### 인증 API 사용

MCP 서버는 API 키 기반 인증 시스템을 제공합니다. 다음은 인증 API를 사용하는 방법입니다:

```python
# Python 클라이언트에서 인증 API 사용
from client_implementation import MCPClient

client = MCPClient(base_url="http://localhost:9000")

# API 키 생성
api_key_response = client.request(
    endpoint="/api/v1/auth/keys",
    method="POST",
    data={"name": "my-api-key", "description": "API 키 설명"}
)
api_key = api_key_response["key"]

# API 키 정보 조회
key_info = client.request(
    endpoint=f"/api/v1/auth/keys/{api_key}",
    method="GET"
)

# 인증이 필요한 API 호출
client.api_key = api_key  # API 키 설정
search_response = client.request(
    endpoint="/api/v1/search",
    method="POST",
    data={"query": "검색어", "type": "web"}
)

# API 키 비활성화
client.request(
    endpoint=f"/api/v1/auth/keys/{api_key}",
    method="DELETE"
)
```

자세한 인증 API 사용 예제는 `examples/auth_example.py` 파일을 참조하세요.

### Python 클라이언트

```python
# .env 파일에서 설정을 로드하여 클라이언트 생성
from client_implementation import MCPClient

# 환경 변수에서 설정을 자동으로 로드
client = MCPClient()

# 또는 직접 설정 제공
client = MCPClient(api_key="your-api-key", base_url="http://localhost:9000")

# 채팅 메시지 전송
response = client.chat("안녕하세요, MCP!")
```

### Java 클라이언트

```java
// .env 파일에서 설정을 로드하여 클라이언트 생성
MCPClient client = new MCPClient();

// 또는 직접 설정 제공
MCPClient client = new MCPClient("your-api-key", "http://localhost:9000");

// 채팅 메시지 전송
Map<String, Object> response = client.chat("안녕하세요, MCP!");
```

### JavaScript 클라이언트

```javascript
// .env 파일에서 설정을 로드하여 클라이언트 생성
const { MCPClient } = require('./client_implementation');

// 환경 변수에서 설정을 자동으로 로드
const client = new MCPClient();

// 또는 직접 설정 제공
const client = new MCPClient("your-api-key", "http://localhost:9000");

// 채팅 메시지 전송
const response = await client.chat("안녕하세요, MCP!");
```

자세한 사용 예제는 `examples` 디렉토리의 예제 파일을 참조하세요.

### Docker를 사용한 설치

1. Docker 컨테이너 빌드 및 실행
```bash
docker-compose up -d
```

## 4. 주의사항

### 보안 관련
- 프로덕션 환경에서는 반드시 강력한 API 키를 사용하세요.
- `.env` 파일에 민감한 정보를 저장할 때 주의하고, 이 파일을 버전 관리 시스템에 포함시키지 마세요.
- 정기적으로 보안 업데이트를 확인하고 적용하세요.
- API 키 관리:
  - 사용하지 않는 API 키는 즉시 비활성화하세요.
  - API 키에 설명적인 이름과 용도를 지정하여 관리하세요.
  - 정기적으로 API 키를 순환하고 오래된 키는 비활성화하세요.
  - 각 클라이언트 애플리케이션마다 별도의 API 키를 사용하세요.

### 성능 관련
- 대량의 요청을 처리할 때는 서버 리소스 사용량을 모니터링하세요.
- 메모리 누수를 방지하기 위해 장기 실행 세션을 적절히 관리하세요.
- 프로덕션 환경에서는 로드 밸런싱 및 고가용성 설정을 고려하세요.

### 개발 관련
- API 변경 시 기존 클라이언트와의 호환성을 고려하세요.
- 새로운 기능을 추가하기 전에 충분한 테스트를 수행하세요.
- 코드 변경 후에는 보안 테스트를 실행하여 새로운 취약점이 도입되지 않았는지 확인하세요.

## 라이선스

이 프로젝트는 [라이선스 이름] 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 기여

기여는 언제나 환영합니다! 버그 리포트, 기능 요청 또는 코드 기여를 위해 이슈를 열거나 풀 리퀘스트를 제출해 주세요.
