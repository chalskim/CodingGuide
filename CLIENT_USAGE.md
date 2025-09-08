# MCP 클라이언트 사용 가이드

## 목차

- [소개](#소개)
- [시작하기](#시작하기)
- [인증](#인증)
- [기본 API 사용법](#기본-api-사용법)
- [세션 관리](#세션-관리)
- [오류 처리](#오류-처리)
- [예제 코드](#예제-코드)
- [클라이언트 라이브러리](#클라이언트-라이브러리)
- [커스텀 LLM 사용하기](#커스텀-llm-사용하기)
- [문제 해결](#문제-해결)
- [자주 묻는 질문](#자주-묻는-질문)

## 소개

MCP(Model Control Protocol) 클라이언트는 MCP 서버와 통신하기 위한 인터페이스를 제공합니다. 이 가이드는 MCP 클라이언트를 사용하여 AI 모델과 상호작용하는 방법을 설명합니다.

### 주요 기능

- 채팅 및 대화 세션 관리
- 텍스트 생성 및 콘텐츠 생성
- 피드백 제공 및 조회
- 서버 상태 모니터링

### 요구사항

- MCP 서버 접근 권한
- API 키
- 지원되는 프로그래밍 언어 환경 (Python, JavaScript, Java 등)

## 시작하기

### 설치

각 언어별 클라이언트 라이브러리 설치 방법은 다음과 같습니다:

#### Python

```bash
pip install mcp-client
```

#### JavaScript (Node.js)

```bash
npm install mcp-client
```

#### Java

Maven:
```xml
<dependency>
    <groupId>com.mcp</groupId>
    <artifactId>mcp-client</artifactId>
    <version>1.0.0</version>
</dependency>
```

Gradle:
```groovy
implementation 'com.mcp:mcp-client:1.0.0'
```

## 인증

MCP 서버에 접근하기 위해서는 API 키가 필요합니다. API 키는 MCP 관리자로부터 발급받을 수 있습니다.

### API 키 발급 방법

1. MCP 관리 포털에 로그인합니다.
2. 개발자 설정 메뉴로 이동합니다.
3. "API 키 생성" 버튼을 클릭합니다.
4. 키 이름과 설명을 입력하고 생성합니다.
5. 생성된 API 키를 안전하게 보관합니다.

### 인증 예시

#### Python

```python
from mcp_client import MCPClient

# 클라이언트 초기화
client = MCPClient(api_key="your-api-key", base_url="http://localhost:8000")
```

#### JavaScript

```javascript
const { MCPClient } = require('mcp-client');

// 클라이언트 초기화
const client = new MCPClient({
  apiKey: 'your-api-key',
  baseUrl: 'http://localhost:8000'
});
```

#### Java

```java
import com.mcp.client.MCPClient;

// 클라이언트 초기화
MCPClient client = new MCPClient("your-api-key", "http://localhost:8000");
```

## 기본 API 사용법

### 서버 상태 확인

```python
# Python
health_status = client.check_health()
print(f"서버 상태: {health_status}")
```

```javascript
// JavaScript
client.checkHealth()
  .then(status => console.log(`서버 상태: ${JSON.stringify(status)}`))
  .catch(error => console.error(`오류: ${error.message}`));
```

```java
// Java
Map<String, Object> healthStatus = client.checkHealth();
System.out.println("서버 상태: " + healthStatus);
```

### 채팅 메시지 전송

```python
# Python
response = client.chat("안녕하세요, MCP!")
print(f"AI 응답: {response['message']['content']}")
```

```javascript
// JavaScript
client.chat("안녕하세요, MCP!")
  .then(response => console.log(`AI 응답: ${response.message.content}`))
  .catch(error => console.error(`오류: ${error.message}`));
```

```java
// Java
Map<String, Object> response = client.chat("안녕하세요, MCP!");
Map<String, Object> message = (Map<String, Object>) response.get("message");
System.out.println("AI 응답: " + message.get("content"));
```

### 콘텐츠 생성

```python
# Python
generated = client.generate(
    prompt="인공지능의 미래에 대해 설명해주세요",
    max_tokens=200,
    temperature=0.7
)
print(f"생성된 콘텐츠: {generated['content']}")
```

```javascript
// JavaScript
client.generate({
  prompt: "인공지능의 미래에 대해 설명해주세요",
  maxTokens: 200,
  temperature: 0.7
})
  .then(result => console.log(`생성된 콘텐츠: ${result.content}`))
  .catch(error => console.error(`오류: ${error.message}`));
```

```java
// Java
Map<String, Object> generated = client.generate(
    "인공지능의 미래에 대해 설명해주세요",
    200,
    0.7
);
System.out.println("생성된 콘텐츠: " + generated.get("content"));
```

### 응답 형식

MCP API 응답은 일반적으로 다음과 같은 JSON 형식을 따릅니다:

```json
{
  "request_id": "req_123456789",
  "timestamp": "2023-05-15T14:30:45Z",
  "status": "success",
  "data": { ... },  // 엔드포인트별 응답 데이터
  "message": { ... }  // 채팅 응답인 경우
}
```

## 세션 관리

### 세션 생성 및 사용

```python
# Python
session = client.create_chat_session()

# 첫 번째 메시지 전송
response1 = session.send_message("안녕하세요!")
print(f"AI 응답 1: {response1['content']}")

# 후속 메시지 전송 (세션 유지)
response2 = session.send_message("MCP에 대해 알려주세요")
print(f"AI 응답 2: {response2['content']}")

# 세션 기록 확인
history = session.get_history()
print(f"대화 기록: {history}")
```

```javascript
// JavaScript
const session = client.createChatSession();

// 첫 번째 메시지 전송
session.sendMessage("안녕하세요!")
  .then(response => {
    console.log(`AI 응답 1: ${response.content}`);
    
    // 후속 메시지 전송 (세션 유지)
    return session.sendMessage("MCP에 대해 알려주세요");
  })
  .then(response => {
    console.log(`AI 응답 2: ${response.content}`);
    
    // 세션 기록 확인
    const history = session.getHistory();
    console.log(`대화 기록: ${JSON.stringify(history)}`);
  })
  .catch(error => console.error(`오류: ${error.message}`));
```

```java
// Java
MCPClient.ChatSession session = client.createChatSession();

// 첫 번째 메시지 전송
Map<String, Object> response1 = session.sendMessage("안녕하세요!");
System.out.println("AI 응답 1: " + response1.get("content"));

// 후속 메시지 전송 (세션 유지)
Map<String, Object> response2 = session.sendMessage("MCP에 대해 알려주세요");
System.out.println("AI 응답 2: " + response2.get("content"));

// 세션 기록 확인
List<Map<String, Object>> history = session.getHistory();
System.out.println("대화 기록: " + history);
```

### 세션 관리 기능

- **세션 ID**: 각 세션은 고유한 ID를 가지며, 이를 통해 대화 컨텍스트를 유지합니다.
- **세션 기록**: 세션 내의 모든 메시지 기록을 조회할 수 있습니다.
- **세션 초기화**: 필요시 세션을 초기화하여 새로운 대화를 시작할 수 있습니다.

## 오류 처리

### 오류 유형

- **인증 오류**: API 키가 잘못되었거나 만료된 경우
- **요청 오류**: 잘못된 매개변수나 형식으로 요청한 경우
- **서버 오류**: 서버 내부 오류가 발생한 경우
- **네트워크 오류**: 네트워크 연결 문제가 발생한 경우

### 오류 처리 예시

```python
# Python
try:
    response = client.chat("안녕하세요")
    print(f"응답: {response}")
except MCPError as e:
    print(f"오류 발생: {e.message}")
    print(f"상태 코드: {e.status_code}")
    print(f"오류 데이터: {e.data}")
```

```javascript
// JavaScript
client.chat("안녕하세요")
  .then(response => console.log(`응답: ${JSON.stringify(response)}`))
  .catch(error => {
    console.error(`오류 발생: ${error.message}`);
    console.error(`상태 코드: ${error.statusCode}`);
    console.error(`오류 데이터: ${JSON.stringify(error.data)}`);
  });
```

```java
// Java
try {
    Map<String, Object> response = client.chat("안녕하세요");
    System.out.println("응답: " + response);
} catch (MCPException e) {
    System.err.println("오류 발생: " + e.getMessage());
    System.err.println("상태 코드: " + e.getStatusCode());
    System.err.println("오류 데이터: " + e.getData());
}
```

## 예제 코드

### 완전한 예제 (Python)

```python
from mcp_client import MCPClient, MCPError

# 클라이언트 초기화
client = MCPClient(api_key="your-api-key", base_url="http://localhost:8000")

try:
    # 서버 상태 확인
    health_status = client.check_health()
    print(f"서버 상태: {health_status}")
    
    # 채팅 세션 생성
    session = client.create_chat_session()
    
    # 첫 번째 메시지 전송
    response1 = session.send_message("안녕하세요, MCP!")
    print(f"AI 응답 1: {response1['content']}")
    
    # 후속 메시지 전송 (세션 유지)
    response2 = session.send_message("MCP 서버의 주요 기능은 무엇인가요?")
    print(f"AI 응답 2: {response2['content']}")
    
    # 세션 기록 확인
    history = session.get_history()
    print(f"대화 기록: {history}")
    
    # 콘텐츠 생성
    generated_content = client.generate(
        prompt="인공지능의 미래 발전 방향에 대해 설명해주세요",
        max_tokens=200,
        temperature=0.8
    )
    print(f"생성된 콘텐츠: {generated_content['content']}")
    
    # 피드백 제공
    feedback_response = client.provide_feedback(
        request_id=generated_content['request_id'],
        rating=5,
        comment="매우 유용한 정보를 제공해주셔서 감사합니다!"
    )
    print(f"피드백 제출 완료: {feedback_response}")
    
except MCPError as e:
    print(f"오류 발생: {e.message}")
    print(f"상태 코드: {e.status_code}")
    print(f"오류 데이터: {e.data}")
```

### 비동기 예제 (JavaScript)

```javascript
const { MCPClient } = require('mcp-client');

// 클라이언트 초기화
const client = new MCPClient({
  apiKey: 'your-api-key',
  baseUrl: 'http://localhost:8000'
});

async function runExample() {
  try {
    // 서버 상태 확인
    const healthStatus = await client.checkHealth();
    console.log(`서버 상태: ${JSON.stringify(healthStatus)}`);
    
    // 채팅 세션 생성
    const session = client.createChatSession();
    
    // 첫 번째 메시지 전송
    const response1 = await session.sendMessage("안녕하세요, MCP!");
    console.log(`AI 응답 1: ${response1.content}`);
    
    // 후속 메시지 전송 (세션 유지)
    const response2 = await session.sendMessage("MCP 서버의 주요 기능은 무엇인가요?");
    console.log(`AI 응답 2: ${response2.content}`);
    
    // 세션 기록 확인
    const history = session.getHistory();
    console.log(`대화 기록: ${JSON.stringify(history)}`);
    
    // 콘텐츠 생성
    const generatedContent = await client.generate({
      prompt: "인공지능의 미래 발전 방향에 대해 설명해주세요",
      maxTokens: 200,
      temperature: 0.8
    });
    console.log(`생성된 콘텐츠: ${generatedContent.content}`);
    
    // 피드백 제공
    const feedbackResponse = await client.provideFeedback({
      requestId: generatedContent.requestId,
      rating: 5,
      comment: "매우 유용한 정보를 제공해주셔서 감사합니다!"
    });
    console.log(`피드백 제출 완료: ${JSON.stringify(feedbackResponse)}`);
    
  } catch (error) {
    console.error(`오류 발생: ${error.message}`);
    console.error(`상태 코드: ${error.statusCode}`);
    console.error(`오류 데이터: ${JSON.stringify(error.data)}`);
  }
}

runExample();
```

### Java 예제

```java
import com.mcp.client.MCPClient;
import com.mcp.client.MCPException;

import java.util.List;
import java.util.Map;

public class MCPClientExample {
    public static void main(String[] args) {
        try {
            // 클라이언트 초기화
            MCPClient client = new MCPClient("your-api-key", "http://localhost:8000");

            // 서버 상태 확인
            Map<String, Object> healthStatus = client.checkHealth();
            System.out.println("서버 상태: " + healthStatus);

            // 채팅 세션 생성
            MCPClient.ChatSession session = client.createChatSession();

            // 첫 번째 메시지 전송
            Map<String, Object> response1 = session.sendMessage("안녕하세요, MCP!");
            System.out.println("AI 응답 1: " + response1.get("content"));

            // 후속 메시지 전송 (세션 유지)
            Map<String, Object> response2 = session.sendMessage("MCP 서버의 주요 기능은 무엇인가요?");
            System.out.println("AI 응답 2: " + response2.get("content"));

            // 세션 기록 확인
            List<Map<String, Object>> history = session.getHistory();
            System.out.println("대화 기록: " + history);

            // 콘텐츠 생성
            Map<String, Object> generatedContent = client.generate(
                    "인공지능의 미래 발전 방향에 대해 설명해주세요",
                    200,
                    0.8);
            System.out.println("생성된 콘텐츠: " + generatedContent.get("content"));

            // 피드백 제공
            Map<String, Object> feedbackResponse = client.provideFeedback(
                    (String) generatedContent.get("request_id"),
                    5,
                    "매우 유용한 정보를 제공해주셔서 감사합니다!");
            System.out.println("피드백 제출 완료: " + feedbackResponse);

        } catch (MCPException e) {
            System.err.println("오류 발생: " + e.getMessage());
            System.err.println("상태 코드: " + e.getStatusCode());
            System.err.println("오류 데이터: " + e.getData());
        } catch (Exception e) {
            System.err.println("예상치 못한 오류: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
```

## 클라이언트 라이브러리

### 지원되는 언어

- Python
- JavaScript (Node.js)
- Java
- Go (개발 중)
- C# (개발 중)

### 라이브러리 설치 방법

각 언어별 설치 방법은 [시작하기](#시작하기) 섹션을 참조하세요.

## 문제 해결

### 일반적인 문제

1. **인증 오류**
   - API 키가 올바르게 설정되었는지 확인하세요.
   - API 키가 만료되지 않았는지 확인하세요.

2. **연결 오류**
   - 서버 URL이 올바른지 확인하세요.
   - 네트워크 연결 상태를 확인하세요.
   - 방화벽 설정을 확인하세요.

3. **요청 오류**
   - 요청 매개변수가 올바른지 확인하세요.
   - 요청 형식이 API 명세와 일치하는지 확인하세요.

### 디버깅 팁

- 클라이언트 로깅을 활성화하여 요청/응답 세부 정보를 확인하세요.
- 서버 로그를 확인하여 서버 측 오류를 파악하세요.
- API 문서를 참조하여 올바른 요청 형식을 확인하세요.

## 커스텀 LLM 사용하기

### 자체 LLM 모델 연결하기

MCP 클라이언트는 사용자가 자신의 환경에 맞는 LLM(Large Language Model)을 연결하여 사용할 수 있는 기능을 제공합니다. 이를 통해 특정 요구사항에 맞는 모델을 선택하거나 자체 개발한 모델을 MCP 시스템과 통합할 수 있습니다.

#### 커스텀 LLM 설정 방법

##### Python

```python
from mcp_client import MCPClient, CustomLLMConfig

# 커스텀 LLM 설정
custom_llm_config = CustomLLMConfig(
    model_name="my-custom-model",
    model_endpoint="http://my-model-server:8080/generate",
    api_key="my-model-api-key",  # 선택 사항
    parameters={
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 0.95
    }
)

# 클라이언트 초기화 시 커스텀 LLM 설정 적용
client = MCPClient(
    api_key="your-mcp-api-key", 
    base_url="http://localhost:8000",
    llm_config=custom_llm_config
)

# 이제 모든 요청은 설정한 커스텀 LLM을 사용합니다
response = client.chat("안녕하세요, 커스텀 LLM입니다!")
```

##### JavaScript

```javascript
const { MCPClient, CustomLLMConfig } = require('mcp-client');

// 커스텀 LLM 설정
const customLLMConfig = {
  modelName: "my-custom-model",
  modelEndpoint: "http://my-model-server:8080/generate",
  apiKey: "my-model-api-key",  // 선택 사항
  parameters: {
    temperature: 0.7,
    maxTokens: 1000,
    topP: 0.95
  }
};

// 클라이언트 초기화 시 커스텀 LLM 설정 적용
const client = new MCPClient({
  apiKey: 'your-mcp-api-key',
  baseUrl: 'http://localhost:8000',
  llmConfig: customLLMConfig
});

// 이제 모든 요청은 설정한 커스텀 LLM을 사용합니다
client.chat("안녕하세요, 커스텀 LLM입니다!")
  .then(response => console.log(`AI 응답: ${response.message.content}`))
  .catch(error => console.error(`오류: ${error.message}`));
```

##### Java

```java
import com.mcp.client.MCPClient;
import com.mcp.client.CustomLLMConfig;

import java.util.HashMap;
import java.util.Map;

public class CustomLLMExample {
    public static void main(String[] args) {
        try {
            // 커스텀 LLM 파라미터 설정
            Map<String, Object> parameters = new HashMap<>();
            parameters.put("temperature", 0.7);
            parameters.put("maxTokens", 1000);
            parameters.put("topP", 0.95);
            
            // 커스텀 LLM 설정 생성
            CustomLLMConfig customLLMConfig = new CustomLLMConfig(
                "my-custom-model",
                "http://my-model-server:8080/generate",
                "my-model-api-key",  // 선택 사항
                parameters
            );
            
            // 클라이언트 초기화 시 커스텀 LLM 설정 적용
            MCPClient client = new MCPClient(
                "your-mcp-api-key", 
                "http://localhost:8000",
                customLLMConfig
            );
            
            // 이제 모든 요청은 설정한 커스텀 LLM을 사용합니다
            Map<String, Object> response = client.chat("안녕하세요, 커스텀 LLM입니다!");
            Map<String, Object> message = (Map<String, Object>) response.get("message");
            System.out.println("AI 응답: " + message.get("content"));
            
        } catch (Exception e) {
            System.err.println("오류 발생: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
```

### 세션별 LLM 설정

특정 세션에서만 다른 LLM을 사용하고 싶을 경우, 세션 생성 시 LLM 설정을 지정할 수 있습니다.

```python
# Python
# 세션별 커스텀 LLM 설정
session_llm_config = CustomLLMConfig(
    model_name="session-specific-model",
    model_endpoint="http://specialized-model:8080/generate"
)

# 특정 세션에만 다른 LLM 설정 적용
session = client.create_chat_session(llm_config=session_llm_config)
response = session.send_message("이 세션은 특별한 모델을 사용합니다")
```

### 요청별 LLM 설정

단일 요청에만 특정 LLM을 사용하고 싶을 경우, 요청 시 LLM 설정을 지정할 수 있습니다.

```python
# Python
# 요청별 커스텀 LLM 설정
request_llm_config = CustomLLMConfig(
    model_name="request-specific-model",
    model_endpoint="http://specialized-model:8080/generate"
)

# 특정 요청에만 다른 LLM 설정 적용
response = client.chat(
    "이 요청은 특별한 모델을 사용합니다", 
    llm_config=request_llm_config
)
```

### 지원되는 LLM 인터페이스

MCP 클라이언트는 다음과 같은 LLM 인터페이스를 지원합니다:

- **OpenAI 호환 API**: OpenAI API와 호환되는 모든 모델 서버
- **Hugging Face Inference API**: Hugging Face에서 호스팅되는 모델
- **자체 호스팅 모델 API**: 사용자가 직접 호스팅하는 모델 서버
- **클라우드 LLM 서비스**: Azure OpenAI, AWS Bedrock, Google Vertex AI 등

### 커스텀 LLM 응답 형식 매핑

사용자 LLM의 응답 형식이 MCP 클라이언트의 기본 형식과 다를 경우, 응답 형식 매핑을 설정할 수 있습니다.

```python
# Python
# 응답 형식 매핑 설정
response_mapping = {
    "content": "generated_text",  # LLM 응답의 'generated_text' 필드를 MCP의 'content'로 매핑
    "model_info": "model",      # LLM 응답의 'model' 필드를 MCP의 'model_info'로 매핑
    "usage": "usage_info"       # LLM 응답의 'usage_info' 필드를 MCP의 'usage'로 매핑
}

# 커스텀 LLM 설정에 응답 매핑 추가
custom_llm_config = CustomLLMConfig(
    model_name="my-custom-model",
    model_endpoint="http://my-model-server:8080/generate",
    response_mapping=response_mapping
)

client = MCPClient(
    api_key="your-mcp-api-key", 
    base_url="http://localhost:8000",
    llm_config=custom_llm_config
)
```

## 자주 묻는 질문

### 일반 질문

**Q: MCP 서버는 어떤 모델을 지원하나요?**

A: MCP 서버는 다양한 AI 모델을 지원합니다. 지원되는 모델 목록은 서버 관리자에게 문의하세요. 또한 [커스텀 LLM 사용하기](#커스텀-llm-사용하기) 섹션을 참조하여 자체 모델을 연결할 수도 있습니다.

**Q: API 요청 제한이 있나요?**

A: 네, 일반적으로 API 요청 제한이 있습니다. 정확한 제한 사항은 서버 관리자에게 문의하세요.

**Q: 세션은 얼마나 오래 유지되나요?**

A: 세션은 일반적으로 마지막 활동 후 24시간 동안 유지됩니다. 정확한 세션 유지 시간은 서버 설정에 따라 다를 수 있습니다.

### 기술 질문

**Q: 비동기 요청을 어떻게 처리하나요?**

A: 각 언어별 클라이언트 라이브러리는 비동기 요청을 위한 메서드를 제공합니다. 예제 코드를 참조하세요.

**Q: 오류 처리는 어떻게 하나요?**

A: 각 언어별 클라이언트 라이브러리는 오류 처리를 위한 예외 클래스를 제공합니다. [오류 처리](#오류-처리) 섹션을 참조하세요.

**Q: 커스텀 헤더를 추가할 수 있나요?**

A: 네, 대부분의 클라이언트 라이브러리는 커스텀 헤더를 추가하는 기능을 제공합니다. 자세한 내용은 라이브러리 문서를 참조하세요.

### 보안 질문

**Q: API 키를 안전하게 관리하는 방법은 무엇인가요?**

A: API 키는 환경 변수나 안전한 구성 파일에 저장하고, 소스 코드에 직접 포함하지 마세요. 또한 정기적으로 키를 교체하는 것이 좋습니다.

**Q: 통신은 암호화되나요?**

A: 네, MCP 클라이언트와 서버 간의 모든 통신은 HTTPS를 통해 암호화됩니다.

**Q: 개인 정보는 어떻게 처리되나요?**

A: 개인 정보 처리 방식은 서버 관리자의 정책에 따라 다릅니다. 자세한 내용은 서버 관리자에게 문의하세요.