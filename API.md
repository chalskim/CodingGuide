# MCP 서버 API 문서

## 개요

MCP 서버는 다양한 컨텍스트와 프로토콜을 통합하여 AI 시스템과 사용자 간의 효율적인 상호작용을 지원하는 RESTful API를 제공합니다. 이 문서는 MCP 서버 API의 사용 방법을 설명합니다.

## 기본 정보

- **기본 URL**: `http://localhost:8000` (로컬 개발 환경)
- **인증**: API 키 기반 인증 (헤더에 `X-API-Key` 포함)
- **응답 형식**: JSON

## 인증

모든 API 요청은 인증이 필요합니다. API 키를 요청 헤더에 포함시켜야 합니다.

```
X-API-Key: your-api-key
```

## 엔드포인트

### 상태 확인

#### GET /health

서버 상태를 확인합니다.

**응답 예시**:

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### 채팅

#### POST /chat

사용자 메시지를 처리하고 응답을 생성합니다.

**요청 본문**:

```json
{
  "session_id": "optional-session-id",
  "message": {
    "content": "사용자 메시지 내용",
    "role": "user"
  }
}
```

**응답 예시**:

```json
{
  "request_id": "req-123456",
  "session_id": "sess-123456",
  "message": {
    "content": "AI 응답 내용",
    "role": "assistant"
  },
  "created_at": "2023-10-15T12:34:56Z"
}
```

**상태 코드**:

- `200 OK`: 요청이 성공적으로 처리됨
- `400 Bad Request`: 잘못된 요청 형식
- `401 Unauthorized`: 인증 실패
- `429 Too Many Requests`: 요청 속도 제한 초과
- `500 Internal Server Error`: 서버 오류

### 콘텐츠 생성

#### POST /generate

특정 프롬프트에 기반한 콘텐츠를 생성합니다.

**요청 본문**:

```json
{
  "prompt": "생성할 콘텐츠에 대한 프롬프트",
  "max_tokens": 100,
  "temperature": 0.7
}
```

**응답 예시**:

```json
{
  "request_id": "req-123456",
  "content": "생성된 콘텐츠",
  "created_at": "2023-10-15T12:34:56Z"
}
```

**상태 코드**:

- `200 OK`: 요청이 성공적으로 처리됨
- `400 Bad Request`: 잘못된 요청 형식
- `401 Unauthorized`: 인증 실패
- `429 Too Many Requests`: 요청 속도 제한 초과
- `500 Internal Server Error`: 서버 오류

### 피드백

#### POST /feedback

이전 요청에 대한 피드백을 제공합니다.

**요청 본문**:

```json
{
  "request_id": "req-123456",
  "rating": 5,
  "comment": "피드백 내용"
}
```

**응답 예시**:

```json
{
  "feedback_id": "fb-123456",
  "request_id": "req-123456",
  "created_at": "2023-10-15T12:34:56Z"
}
```

**상태 코드**:

- `200 OK`: 요청이 성공적으로 처리됨
- `400 Bad Request`: 잘못된 요청 형식
- `401 Unauthorized`: 인증 실패
- `404 Not Found`: 요청 ID를 찾을 수 없음
- `500 Internal Server Error`: 서버 오류

#### GET /feedback/request/{request_id}

특정 요청에 대한 피드백을 조회합니다.

**응답 예시**:

```json
{
  "feedback_id": "fb-123456",
  "request_id": "req-123456",
  "rating": 5,
  "comment": "피드백 내용",
  "created_at": "2023-10-15T12:34:56Z"
}
```

**상태 코드**:

- `200 OK`: 요청이 성공적으로 처리됨
- `401 Unauthorized`: 인증 실패
- `404 Not Found`: 요청 ID 또는 피드백을 찾을 수 없음
- `500 Internal Server Error`: 서버 오류

## 오류 응답

오류가 발생하면 서버는 다음과 같은 형식의 JSON 응답을 반환합니다:

```json
{
  "error": {
    "code": "error_code",
    "message": "오류 메시지",
    "details": {}
  }
}
```

## 속도 제한

API는 속도 제한이 적용됩니다. 기본적으로 분당 60개의 요청으로 제한됩니다. 속도 제한을 초과하면 `429 Too Many Requests` 상태 코드가 반환됩니다.

속도 제한 정보는 응답 헤더에 포함됩니다:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1634300096
```

## 세션 관리

채팅 API는 세션 기반으로 작동합니다. 세션을 유지하려면 응답에서 반환된 `session_id`를 후속 요청에 포함시켜야 합니다. 세션 ID를 제공하지 않으면 새 세션이 생성됩니다.

세션은 기본적으로 1시간 후에 만료됩니다. 이 시간은 서버 구성에서 조정할 수 있습니다.

## 예제

### cURL을 사용한 채팅 요청

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"message": {"content": "안녕하세요", "role": "user"}}'
```

### Python을 사용한 채팅 요청

```python
import requests

url = "http://localhost:8000/chat"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your-api-key"
}
data = {
    "message": {
        "content": "안녕하세요",
        "role": "user"
    }
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

## 웹소켓 API (향후 지원 예정)

실시간 상호작용을 위한 웹소켓 API는 향후 릴리스에서 지원될 예정입니다.