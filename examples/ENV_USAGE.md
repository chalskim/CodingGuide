# 환경 변수 사용 예제

이 문서는 각 클라이언트에서 환경 변수를 사용하는 방법을 설명합니다.

## .env 파일 구성

```
# MCP 서버 및 클라이언트 설정을 위한 환경 변수 파일

# 서버 설정
PROJECT_NAME="MCP Server"
DATABASE_URL="sqlite:///./data/mcp_server.db"
SECRET_KEY="your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM API 설정
OPENAI_API_KEY="your-openai-api-key"
ANTHROPIC_API_KEY="your-anthropic-api-key"
GOOGLE_API_KEY="your-google-api-key"

# 검색 API 설정
GOOGLE_SEARCH_API_KEY="your-google-search-api-key"
GOOGLE_SEARCH_ENGINE_ID="your-google-search-engine-id"
PERPLEXITY_API_KEY="your-perplexity-api-key"
SEARCH_PROVIDER="perplexity"  # google, bing, duckduckgo, perplexity

# 클라이언트 설정
MCP_API_KEY="your-mcp-api-key"
MCP_BASE_URL="http://localhost:9000"
```

## JavaScript 클라이언트

### 환경 변수 로딩

JavaScript 클라이언트에서는 `dotenv` 패키지를 사용하여 환경 변수를 로드합니다.

```javascript
// .env 파일 로드
require('dotenv').config();

// 환경 변수 사용
const apiKey = process.env.MCP_API_KEY;
const baseUrl = process.env.MCP_BASE_URL;
const searchApiKey = process.env.MCP_SEARCH_API_KEY;
```

### 클라이언트 초기화

```javascript
// 환경 변수에서 설정을 자동으로 로드
const client = new MCPClient();

// 또는 일부 설정만 환경 변수에서 로드
const client = new MCPClient(
  null,  // 환경 변수 MCP_API_KEY 사용
  'http://custom-url:8000',  // 직접 URL 지정
  null   // 환경 변수 MCP_SEARCH_API_KEY 사용
);
```

## Python 클라이언트

### 환경 변수 로딩

Python 클라이언트에서는 `python-dotenv` 패키지를 사용하여 환경 변수를 로드합니다.

```python
# .env 파일 로드
from dotenv import load_dotenv
load_dotenv()

# 환경 변수 사용
import os
api_key = os.getenv('MCP_API_KEY')
base_url = os.getenv('MCP_BASE_URL')
search_api_key = os.getenv('MCP_SEARCH_API_KEY')
```

### 클라이언트 초기화

```python
# 환경 변수에서 설정을 자동으로 로드
client = MCPClient()

# 또는 일부 설정만 환경 변수에서 로드
client = MCPClient(
    api_key=None,  # 환경 변수 MCP_API_KEY 사용
    base_url='http://custom-url:8000',  # 직접 URL 지정
    search_api_key=None  # 환경 변수 MCP_SEARCH_API_KEY 사용
)
```

## Java 클라이언트

### 환경 변수 로딩

Java 클라이언트에서는 `dotenv-java` 라이브러리를 사용하여 환경 변수를 로드합니다.

```java
// .env 파일 로드
import io.github.cdimascio.dotenv.Dotenv;

Dotenv dotenv = Dotenv.load();

// 환경 변수 사용
String apiKey = dotenv.get("MCP_API_KEY");
String baseUrl = dotenv.get("MCP_BASE_URL");
String searchApiKey = dotenv.get("MCP_SEARCH_API_KEY");
```

### 클라이언트 초기화

```java
// 환경 변수에서 설정을 자동으로 로드
MCPClient client = new MCPClient();

// 또는 일부 설정만 환경 변수에서 로드
MCPClient client = new MCPClient(
    null,  // 환경 변수 MCP_API_KEY 사용
    "http://custom-url:8000",  // 직접 URL 지정
    null   // 환경 변수에서 LLM 설정 로드
);
```

## Perplexity API 사용 예제

### 서버 설정

서버에서 Perplexity API를 사용하려면 다음과 같이 환경 변수를 설정합니다:

```
# 검색 API 설정
PERPLEXITY_API_KEY="your-perplexity-api-key"
SEARCH_PROVIDER="perplexity"  # 검색 제공자를 perplexity로 설정
```

### JavaScript 클라이언트에서 사용

```javascript
// .env 파일 로드
require('dotenv').config();

// Perplexity API 키 사용
const perplexityApiKey = process.env.PERPLEXITY_API_KEY;

// 검색 요청 시 Perplexity API 사용 설정
const searchResults = await client.search("검색 쿼리", {
  api_key: perplexityApiKey,
  search_provider: "perplexity"
});
```

### Python 클라이언트에서 사용

```python
# .env 파일 로드
from dotenv import load_dotenv
import os

load_dotenv()

# Perplexity API 키 사용
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")

# 검색 요청 시 Perplexity API 사용 설정
search_results = client.search("검색 쿼리", options={
  "api_key": perplexity_api_key,
  "search_provider": "perplexity"
})
```

## 주의사항

1. `.env` 파일은 버전 관리 시스템에 포함시키지 마세요. `.gitignore` 파일에 추가하는 것이 좋습니다.
2. 실제 프로덕션 환경에서는 환경 변수를 직접 설정하는 것이 더 안전합니다.
3. API 키와 같은 민감한 정보는 항상 안전하게 관리하세요.