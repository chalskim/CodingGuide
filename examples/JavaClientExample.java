/**
 * MCP Java 클라이언트 사용 예제
 * 
 * 이 예제는 .env 파일에서 설정을 로드하여 MCP 클라이언트를 사용하는 방법을 보여줍니다.
 */

import java.util.Map;
import java.util.HashMap;

public class JavaClientExample {
    
    public static void main(String[] args) {
        try {
            // .env 파일에서 설정을 로드하여 클라이언트 생성
            // 환경 변수: MCP_API_KEY, MCP_BASE_URL, MCP_SEARCH_API_KEY
            MCPClient client = new MCPClient();
            
            // 서버 상태 확인
            Map<String, Object> health = client.checkHealth();
            System.out.println("서버 상태: " + health);
            
            // 채팅 메시지 전송
            Map<String, Object> response = client.chat("안녕하세요, MCP!");
            Map<String, Object> message = (Map<String, Object>) response.get("message");
            System.out.println("AI 응답: " + message.get("content"));
            
            // 커스텀 LLM 설정 사용
            Map<String, Object> parameters = new HashMap<>();
            parameters.put("temperature", 0.7);
            parameters.put("max_tokens", 1000);
            
            CustomLLMConfig customLlmConfig = new CustomLLMConfig(
                "gpt-4",
                "/v1/chat/completions",
                null,  // 환경 변수 OPENAI_API_KEY 사용
                parameters,
                null
            );
            
            // 커스텀 LLM 설정으로 새 클라이언트 생성
            MCPClient customClient = new MCPClient(null, null, customLlmConfig);
            
            // 커스텀 LLM으로 채팅
            Map<String, Object> customResponse = customClient.chat("커스텀 LLM 설정으로 대화합니다.");
            Map<String, Object> customMessage = (Map<String, Object>) customResponse.get("message");
            System.out.println("커스텀 LLM 응답: " + customMessage.get("content"));
            
            // 검색 기능은 현재 구현되어 있지 않아 주석 처리
            // Map<String, Object> searchResponse = client.search("인공지능 최신 동향");
            // System.out.println("검색 결과: " + searchResponse);
            System.out.println("검색 기능 테스트 생략 - 아직 구현되지 않음");
            
        } catch (Exception e) {
            System.err.println("오류 발생: " + e.getMessage());
            e.printStackTrace();
        }
    }
}