/**
 * MCP JavaScript 클라이언트 사용 예제
 * 
 * 이 예제는 .env 파일에서 설정을 로드하여 MCP 클라이언트를 사용하는 방법을 보여줍니다.
 */

// client_implementation.js 모듈 가져오기
const { MCPClient } = require('./client_implementation');

async function main() {
  try {
    // .env 파일에서 설정을 로드하여 클라이언트 생성
    // 환경 변수: MCP_API_KEY, MCP_BASE_URL, MCP_SEARCH_API_KEY
    const client = new MCPClient();
    
    // 서버 상태 확인
    const health = await client.checkHealth();
    console.log(`서버 상태: ${JSON.stringify(health)}`);
    
    // 채팅 메시지 전송
    const response = await client.chat("안녕하세요, MCP!");
    console.log(`AI 응답: ${response.message.content}`);
    
    // 커스텀 LLM 설정 사용
    const customClient = new MCPClient(
      null, // 환경 변수 MCP_API_KEY 사용
      null, // 환경 변수 MCP_BASE_URL 사용
      null  // 환경 변수 MCP_SEARCH_API_KEY 사용
    );
    
    // 커스텀 LLM 설정으로 채팅
    const customResponse = await customClient.chat("커스텀 LLM 설정으로 대화합니다.", {
      model_name: "gpt-4",
      model_endpoint: "/v1/chat/completions",
      parameters: {
        temperature: 0.7,
        max_tokens: 1000
      }
    });
    console.log(`커스텀 LLM 응답: ${customResponse.message.content}`);
    
    // 검색 기능은 현재 구현되어 있지 않아 주석 처리
    // const searchResponse = await client.search("인공지능 최신 동향");
    // console.log(`검색 결과: ${JSON.stringify(searchResponse)}`);
    console.log("검색 기능 테스트 생략 - 아직 구현되지 않음");
    
  } catch (error) {
    console.error(`오류 발생: ${error.message}`);
  }
}

// 메인 함수 실행
main();