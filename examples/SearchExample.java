/**
 * 검색 API 키와 검색 엔진 ID를 사용하는 Java 클라이언트 예제
 */

import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.io.IOException;

public class SearchExample {
    
    public static void main(String[] args) {
        try {
            // 환경 변수에서 설정 로드
            String apiKey = System.getenv("MCP_API_KEY");
            String baseUrl = System.getenv("MCP_BASE_URL");
            if (baseUrl == null || baseUrl.isEmpty()) {
                baseUrl = "http://localhost:9000";
            }
            String searchApiKey = System.getenv("MCP_SEARCH_API_KEY");
            String searchEngineId = System.getenv("MCP_SEARCH_ENGINE_ID");
            
            // 클라이언트 생성
            MCPClient client = new MCPClient(apiKey, baseUrl, null, searchApiKey, searchEngineId);
            
            // 검색 요청 데이터 준비
            Map<String, Object> searchData = new HashMap<>();
            searchData.put("query", "MCP 서버 아키텍처");
            searchData.put("num_results", 5);
            
            // 검색 요청 실행
            // MCPClient의 request 메서드는 private이므로 공개된 메서드를 사용해야 함
            // 여기서는 가정된 공개 메서드를 사용합니다. 실제 구현에 맞게 수정 필요
            Map<String, Object> searchResult = client.sendRequest("POST", "/search", searchData);
            
            // 검색 결과 출력
            System.out.println("검색 결과:");
            List<Map<String, Object>> results = (List<Map<String, Object>>) searchResult.get("results");
            if (results != null) {
                for (int i = 0; i < results.size(); i++) {
                    Map<String, Object> result = results.get(i);
                    System.out.println((i + 1) + ". " + result.get("title"));
                    System.out.println("   URL: " + result.get("link"));
                    System.out.println("   스니펫: " + result.get("snippet"));
                    System.out.println();
                }
            }
            
        } catch (IOException e) {
            System.err.println("검색 요청 중 오류 발생: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("예상치 못한 오류 발생: " + e.getMessage());
            e.printStackTrace();
        }
    }
}