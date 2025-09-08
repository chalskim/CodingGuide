/**
 * MCP 클라이언트 구현 예제 (Java)
 * 
 * 이 파일은 MCP 서버와 통신하기 위한 Java 클라이언트 라이브러리의 예제 구현을 제공합니다.
 * 실제 프로젝트에서는 Jackson 라이브러리를 사용하는 것이 권장되지만, 이 예제에서는 
 * Java 표준 라이브러리만 사용하여 구현했습니다.
 * 
 * .env 파일 로딩을 위해 io.github.cdimascio:dotenv-java 라이브러리를 사용합니다.
 * Maven 의존성: <dependency>
 *     <groupId>io.github.cdimascio</groupId>
 *     <artifactId>dotenv-java</artifactId>
 *     <version>2.3.2</version>
 * </dependency>
 * 
 * Gradle 의존성: implementation 'io.github.cdimascio:dotenv-java:2.3.2'
 */

// 필요한 Java 표준 라이브러리 임포트
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.URI;
import java.net.URL;
import java.net.HttpURLConnection;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;
import java.util.UUID;

// 환경 변수 로딩을 위한 유틸리티 클래스
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Properties;

// CustomLLMConfig 클래스는 같은 패키지에 있으므로 import 필요 없음

// 참고: 실제 사용 시에는 pom.xml 또는 build.gradle에 다음 의존성을 추가해야 합니다:
// Maven:
// <dependency>
//     <groupId>com.fasterxml.jackson.core</groupId>
//     <artifactId>jackson-databind</artifactId>
//     <version>2.13.4</version>
// </dependency>
//
// Gradle:
// implementation 'com.fasterxml.jackson.core:jackson-databind:2.13.4'

// 이 예제에서는 Jackson 라이브러리 대신 표준 라이브러리만 사용합니다
// import com.fasterxml.jackson.databind.ObjectMapper;
// import com.fasterxml.jackson.core.type.TypeReference;

public class MCPClient {
    private String apiKey;
    private String baseUrl;
    private String sessionId;
    private CustomLLMConfig llmConfig;
    private String searchApiKey;
    private String searchEngineId;
    
    // 환경 변수를 로드하는 Properties 인스턴스
    private static final Properties envVars = loadEnvVars();
    
    /**
     * .env 파일에서 환경 변수를 로드하는 메서드
     * @return 환경 변수가 담긴 Properties 객체
     */
    private static Properties loadEnvVars() {
        Properties props = new Properties();
        Path dotenvPath = Paths.get(System.getProperty("user.dir"), ".env");
        
        if (Files.exists(dotenvPath)) {
            try (InputStream input = new FileInputStream(dotenvPath.toFile())) {
                props.load(input);
            } catch (IOException e) {
                System.err.println("Warning: Could not load .env file: " + e.getMessage());
            }
        }
        
        return props;
    }
    
    /**
     * 환경 변수 값을 가져오는 메서드
     * @param key 환경 변수 키
     * @return 환경 변수 값 또는 null
     */
    private static String getEnv(String key) {
        // 시스템 환경 변수를 먼저 확인
        String value = System.getenv(key);
        
        // 시스템 환경 변수가 없으면 .env 파일에서 로드한 값 사용
        if (value == null || value.isEmpty()) {
            value = envVars.getProperty(key);
        }
        
        return value;
    }

    /**
     * MCP 클라이언트 생성자
     * 
     * 환경 변수에서 설정을 로드합니다:
     * - MCP_API_KEY: API 키
     * - MCP_BASE_URL: 서버 기본 URL
     * - MCP_SEARCH_API_KEY: 검색 API 키
     */
    public MCPClient() {
        this.apiKey = getEnv("MCP_API_KEY");
        this.baseUrl = getEnv("MCP_BASE_URL");
        if (this.baseUrl == null || this.baseUrl.isEmpty()) {
            this.baseUrl = "http://localhost:8000";
        }
        this.searchApiKey = getEnv("MCP_SEARCH_API_KEY");
        this.sessionId = null;
        this.llmConfig = null;
        
        if (this.apiKey == null || this.apiKey.isEmpty()) {
            throw new IllegalArgumentException("API 키가 필요합니다. MCP_API_KEY 환경 변수를 설정하세요.");
        }
    }
    
    /**
     * MCP 클라이언트 생성자
     * 
     * @param apiKey API 키 (null인 경우 MCP_API_KEY 환경 변수 사용)
     * @param baseUrl 서버 기본 URL (null인 경우 MCP_BASE_URL 환경 변수 또는 기본값 사용)
     */
    public MCPClient(String apiKey, String baseUrl) {
        this.apiKey = apiKey != null ? apiKey : getEnv("MCP_API_KEY");
        this.baseUrl = baseUrl != null ? baseUrl : getEnv("MCP_BASE_URL");
        if (this.baseUrl == null || this.baseUrl.isEmpty()) {
            this.baseUrl = "http://localhost:8000";
        }
        this.searchApiKey = getEnv("MCP_SEARCH_API_KEY");
        this.sessionId = null;
        this.llmConfig = null;
        
        if (this.apiKey == null || this.apiKey.isEmpty()) {
            throw new IllegalArgumentException("API 키가 필요합니다. 매개변수로 전달하거나 MCP_API_KEY 환경 변수를 설정하세요.");
        }
    }
    
    /**
     * MCP 클라이언트 생성자 (커스텀 LLM 설정 포함)
     * 
     * @param apiKey API 키 (null인 경우 MCP_API_KEY 환경 변수 사용)
     * @param baseUrl 서버 기본 URL (null인 경우 MCP_BASE_URL 환경 변수 또는 기본값 사용)
     * @param llmConfig 커스텀 LLM 설정
     */
    public MCPClient(String apiKey, String baseUrl, CustomLLMConfig llmConfig) {
        this.apiKey = apiKey != null ? apiKey : getEnv("MCP_API_KEY");
        this.baseUrl = baseUrl != null ? baseUrl : getEnv("MCP_BASE_URL");
        if (this.baseUrl == null || this.baseUrl.isEmpty()) {
            this.baseUrl = "http://localhost:8000";
        }
        this.searchApiKey = getEnv("MCP_SEARCH_API_KEY");
        this.sessionId = null;
        this.llmConfig = llmConfig;
        
        if (this.apiKey == null || this.apiKey.isEmpty()) {
            throw new IllegalArgumentException("API 키가 필요합니다. 매개변수로 전달하거나 MCP_API_KEY 환경 변수를 설정하세요.");
        }
    }
    
    /**
     * MCP 클라이언트 생성자 (검색 API 키 포함)
     * 
     * @param apiKey API 키 (null인 경우 MCP_API_KEY 환경 변수 사용)
     * @param baseUrl 서버 기본 URL (null인 경우 MCP_BASE_URL 환경 변수 또는 기본값 사용)
     * @param searchApiKey 검색 API 키 (null인 경우 MCP_SEARCH_API_KEY 환경 변수 사용)
     */
    public MCPClient(String apiKey, String baseUrl, String searchApiKey) {
        this.apiKey = apiKey != null ? apiKey : getEnv("MCP_API_KEY");
        this.baseUrl = baseUrl != null ? baseUrl : getEnv("MCP_BASE_URL");
        if (this.baseUrl == null || this.baseUrl.isEmpty()) {
            this.baseUrl = "http://localhost:8000";
        }
        this.searchApiKey = searchApiKey != null ? searchApiKey : getEnv("MCP_SEARCH_API_KEY");
        this.sessionId = null;
        this.llmConfig = null;
        
        if (this.apiKey == null || this.apiKey.isEmpty()) {
            throw new IllegalArgumentException("API 키가 필요합니다. 매개변수로 전달하거나 MCP_API_KEY 환경 변수를 설정하세요.");
        }
    }
    
    /**
     * MCP 클라이언트 생성자 (커스텀 LLM 설정 및 검색 API 키 포함)
     * 
     * @param apiKey API 키 (null인 경우 MCP_API_KEY 환경 변수 사용)
     * @param baseUrl 서버 기본 URL (null인 경우 MCP_BASE_URL 환경 변수 또는 기본값 사용)
     * @param llmConfig 커스텀 LLM 설정
     * @param searchApiKey 검색 API 키 (null인 경우 MCP_SEARCH_API_KEY 환경 변수 사용)
     * @param searchEngineId 검색 엔진 ID (null인 경우 MCP_SEARCH_ENGINE_ID 환경 변수 사용)
     */
    public MCPClient(String apiKey, String baseUrl, CustomLLMConfig llmConfig, String searchApiKey, String searchEngineId) {
        this.apiKey = apiKey != null ? apiKey : getEnv("MCP_API_KEY");
        this.baseUrl = baseUrl != null ? baseUrl : getEnv("MCP_BASE_URL");
        if (this.baseUrl == null || this.baseUrl.isEmpty()) {
            this.baseUrl = "http://localhost:8000";
        }
        this.searchApiKey = searchApiKey != null ? searchApiKey : getEnv("MCP_SEARCH_API_KEY");
        this.searchEngineId = searchEngineId != null ? searchEngineId : getEnv("MCP_SEARCH_ENGINE_ID");
        this.sessionId = null;
        this.llmConfig = llmConfig;
        
        if (this.apiKey == null || this.apiKey.isEmpty()) {
            throw new IllegalArgumentException("API 키가 필요합니다. 매개변수로 전달하거나 MCP_API_KEY 환경 변수를 설정하세요.");
        }
    }
    
    /**
     * MCP 클라이언트 생성자 (커스텀 LLM 설정 및 검색 API 키 포함, 이전 버전과의 호환성 유지)
     * 
     * @param apiKey API 키 (null인 경우 MCP_API_KEY 환경 변수 사용)
     * @param baseUrl 서버 기본 URL (null인 경우 MCP_BASE_URL 환경 변수 또는 기본값 사용)
     * @param llmConfig 커스텀 LLM 설정
     * @param searchApiKey 검색 API 키 (null인 경우 MCP_SEARCH_API_KEY 환경 변수 사용)
     */
    public MCPClient(String apiKey, String baseUrl, CustomLLMConfig llmConfig, String searchApiKey) {
        this(apiKey, baseUrl, llmConfig, searchApiKey, null);
    }

    /**
     * API 요청 전송
     * 
     * @param endpoint API 엔드포인트
     * @param method HTTP 메서드 (GET, POST, PUT, DELETE)
     * @param data 요청 데이터 (선택 사항)
     * @return 응답 데이터
     * @throws MCPException API 오류 발생 시
     */
    private Map<String, Object> request(String endpoint, String method, Map<String, Object> data) throws MCPException {
        try {
            // URL 구성 시 중복 슬래시 방지 및 따옴표 제거
            String cleanBaseUrl = baseUrl.replace("\"", "");
            String url;
            if (cleanBaseUrl.endsWith("/") && endpoint.startsWith("/")) {
                url = cleanBaseUrl + endpoint.substring(1);
            } else if (!cleanBaseUrl.endsWith("/") && !endpoint.startsWith("/")) {
                url = cleanBaseUrl + "/" + endpoint;
            } else {
                url = cleanBaseUrl + endpoint;
            }
            HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
            connection.setRequestMethod(method);
            connection.setRequestProperty("Content-Type", "application/json");
            connection.setRequestProperty("X-API-Key", apiKey);
            
            // 검색 API 키와 검색 엔진 ID가 있고 검색 관련 엔드포인트인 경우 헤더에 추가
            if (endpoint.startsWith("/search")) {
                if (searchApiKey != null) {
                    connection.setRequestProperty("X-Search-API-Key", searchApiKey);
                }
                if (searchEngineId != null) {
                    connection.setRequestProperty("X-Search-Engine-ID", searchEngineId);
                }
            }
            
            connection.setConnectTimeout(30000);
            connection.setReadTimeout(30000);
            connection.setDoInput(true);

            if (method.equalsIgnoreCase("POST") || method.equalsIgnoreCase("PUT")) {
                connection.setDoOutput(true);
                if (data != null) {
                    String requestBody = mapToJson(data);
                    try (OutputStream os = connection.getOutputStream();
                         OutputStreamWriter writer = new OutputStreamWriter(os, StandardCharsets.UTF_8)) {
                        writer.write(requestBody);
                    }
                }
            } else if (!method.equalsIgnoreCase("GET") && !method.equalsIgnoreCase("DELETE")) {
                throw new MCPException("지원하지 않는 HTTP 메서드: " + method);
            }

            int statusCode = connection.getResponseCode();
            String responseBody;
            
            // 응답 본문 읽기 (성공 또는 오류)
            try (InputStream is = (statusCode >= 200 && statusCode < 300) ? 
                    connection.getInputStream() : connection.getErrorStream();
                 BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
                responseBody = reader.lines().collect(Collectors.joining("\n"));
            }

            if (statusCode >= 200 && statusCode < 300) {
                return jsonToMap(responseBody);
            } else {
                Map<String, Object> errorData;
                try {
                    errorData = jsonToMap(responseBody);
                } catch (Exception e) {
                    errorData = new HashMap<>();
                    errorData.put("error", responseBody);
                }

                Map<String, Object> error = (Map<String, Object>) errorData.getOrDefault("error", new HashMap<>());
                String errorMessage = (String) error.getOrDefault("message", "알 수 없는 오류");

                throw new MCPException("API 오류: " + errorMessage, statusCode, errorData);
            }
        } catch (IOException e) {
            Map<String, Object> errorData = new HashMap<>();
            errorData.put("original_error", e.getMessage());
            throw new MCPException("네트워크 오류: " + e.getMessage(), 0, errorData);
        }
    }
    
    /**
     * Map을 JSON 문자열로 변환 (간단한 구현)
     */
    private String mapToJson(Map<String, Object> map) {
        if (map == null) return "null";
        
        StringBuilder sb = new StringBuilder();
        sb.append('{');
        boolean first = true;
        
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            if (!first) sb.append(',');
            first = false;
            
            sb.append('"').append(entry.getKey()).append('"').append(':');
            appendJsonValue(sb, entry.getValue());
        }
        
        sb.append('}');
        return sb.toString();
    }
    
    /**
     * JSON 값 추가 (간단한 구현)
     */
    private void appendJsonValue(StringBuilder sb, Object value) {
        if (value == null) {
            sb.append("null");
        } else if (value instanceof String) {
            sb.append('"').append(((String) value).replace("\"", "\\\"")).append('"');
        } else if (value instanceof Number || value instanceof Boolean) {
            sb.append(value);
        } else if (value instanceof Map) {
            sb.append(mapToJson((Map<String, Object>) value));
        } else if (value instanceof List) {
            sb.append('[');
            boolean first = true;
            for (Object item : (List<?>) value) {
                if (!first) sb.append(',');
                first = false;
                appendJsonValue(sb, item);
            }
            sb.append(']');
        } else {
            sb.append('"').append(value.toString()).append('"');
        }
    }
    
    /**
     * JSON 문자열을 Map으로 변환 (간단한 구현)
     * 참고: 이 구현은 매우 기본적이며 실제 프로젝트에서는 Jackson 같은 라이브러리 사용 권장
     */
    private Map<String, Object> jsonToMap(String json) {
        // 간단한 구현을 위해 기본 파싱 로직 제공
        // 실제 프로젝트에서는 Jackson 라이브러리 사용 권장
        Map<String, Object> result = new HashMap<>();
        
        // 가장 기본적인 파싱만 구현 (실제 프로젝트에서는 전체 JSON 파서 구현 필요)
        if (json == null || json.trim().isEmpty() || !json.trim().startsWith("{")) {
            return result;
        }
        
        // 매우 간단한 키-값 추출 (실제 구현에서는 더 견고한 파서 필요)
        String content = json.trim();
        content = content.substring(1, content.length() - 1).trim();
        
        // 키-값 쌍 분리 (매우 기본적인 구현)
        for (String pair : content.split(",")) {
            String[] keyValue = pair.split(":", 2);
            if (keyValue.length == 2) {
                String key = keyValue[0].trim();
                if (key.startsWith("\"") && key.endsWith("\"")) {
                    key = key.substring(1, key.length() - 1);
                }
                
                String valueStr = keyValue[1].trim();
                Object value;
                
                // 기본 타입 파싱 (문자열, 숫자, 불리언, null)
                if (valueStr.equals("null")) {
                    value = null;
                } else if (valueStr.startsWith("\"") && valueStr.endsWith("\"")) {
                    value = valueStr.substring(1, valueStr.length() - 1);
                } else if (valueStr.equals("true")) {
                    value = Boolean.TRUE;
                } else if (valueStr.equals("false")) {
                    value = Boolean.FALSE;
                } else {
                    try {
                        value = Double.parseDouble(valueStr);
                    } catch (NumberFormatException e) {
                        value = valueStr; // 파싱 실패 시 문자열로 처리
                    }
                }
                
                result.put(key, value);
            }
        }
        
        return result;
    }

    /**
     * 비동기 API 요청 전송
     * 
     * @param endpoint API 엔드포인트
     * @param method HTTP 메서드
     * @param data 요청 데이터
     * @return 응답 데이터를 포함한 CompletableFuture
     */
    private CompletableFuture<Map<String, Object>> requestAsync(String endpoint, String method, Map<String, Object> data) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return request(endpoint, method, data);
            } catch (MCPException e) {
                throw new java.util.concurrent.CompletionException(e);
            }
        });
    }

    /**
     * 서버 상태 확인
     * 
     * @return 서버 상태 정보
     * @throws MCPException API 오류 발생 시
     */
    public Map<String, Object> checkHealth() throws MCPException {
        return request("/api/health", "GET", null);
    }

    /**
     * 비동기 서버 상태 확인
     * 
     * @return 서버 상태 정보를 포함한 CompletableFuture
     */
    public CompletableFuture<Map<String, Object>> checkHealthAsync() {
        return requestAsync("/api/health", "GET", null);
    }
    
    /**
     * 일반 API 요청 전송 (공개 메서드)
     * 
     * @param method HTTP 메서드 (GET, POST, PUT, DELETE)
     * @param endpoint API 엔드포인트
     * @param data 요청 데이터 (선택 사항)
     * @return 응답 데이터
     * @throws IOException API 오류 발생 시
     */
    public Map<String, Object> sendRequest(String method, String endpoint, Map<String, Object> data) throws IOException {
        try {
            return request(endpoint, method, data);
        } catch (MCPException e) {
            throw new IOException(e.getMessage(), e);
        }
    }

    /**
     * 채팅 메시지 전송
     * 
     * @param content 사용자 메시지 내용
     * @return 채팅 응답
     * @throws MCPException API 오류 발생 시
     */
    public Map<String, Object> chat(String content) throws MCPException {
        Map<String, Object> data = new HashMap<>();
        data.put("content", content);

        if (sessionId != null && !sessionId.isEmpty()) {
            data.put("session_id", sessionId);
        }
        
        // 커스텀 LLM 설정이 있는 경우 추가
        if (llmConfig != null) {
            Map<String, Object> llmData = new HashMap<>();
            llmData.put("model_name", llmConfig.getModelName());
            llmData.put("model_endpoint", llmConfig.getModelEndpoint());
            
            if (llmConfig.getApiKey() != null) {
                llmData.put("api_key", llmConfig.getApiKey());
            }
            
            if (!llmConfig.getParameters().isEmpty()) {
                llmData.put("parameters", llmConfig.getParameters());
            }
            
            if (!llmConfig.getResponseMapping().isEmpty()) {
                llmData.put("response_mapping", llmConfig.getResponseMapping());
            }
            
            data.put("llm_config", llmData);
        }

        Map<String, Object> response = request("/api/chat", "POST", data);
        this.sessionId = (String) response.get("session_id");
        return response;
    }
    
    /**
     * 채팅 메시지 전송 (요청별 커스텀 LLM 설정)
     * 
     * @param content 사용자 메시지 내용
     * @param requestLlmConfig 이 요청에만 적용할 커스텀 LLM 설정
     * @return 채팅 응답
     * @throws MCPException API 오류 발생 시
     */
    public Map<String, Object> chat(String content, CustomLLMConfig requestLlmConfig) throws MCPException {
        Map<String, Object> data = new HashMap<>();
        data.put("content", content);

        if (sessionId != null && !sessionId.isEmpty()) {
            data.put("session_id", sessionId);
        }
        
        // 요청별 커스텀 LLM 설정 추가
        if (requestLlmConfig != null) {
            Map<String, Object> llmData = new HashMap<>();
            llmData.put("model_name", requestLlmConfig.getModelName());
            llmData.put("model_endpoint", requestLlmConfig.getModelEndpoint());
            
            if (requestLlmConfig.getApiKey() != null) {
                llmData.put("api_key", requestLlmConfig.getApiKey());
            }
            
            if (!requestLlmConfig.getParameters().isEmpty()) {
                llmData.put("parameters", requestLlmConfig.getParameters());
            }
            
            if (!requestLlmConfig.getResponseMapping().isEmpty()) {
                llmData.put("response_mapping", requestLlmConfig.getResponseMapping());
            }
            
            data.put("llm_config", llmData);
        }

        Map<String, Object> response = request("/api/chat", "POST", data);
        this.sessionId = (String) response.get("session_id");
        return response;
    }

    /**
     * 비동기 채팅 메시지 전송
     * 
     * @param content   사용자 메시지 내용
     * @param sessionId 세션 ID (선택 사항)
     * @return 채팅 응답을 포함한 CompletableFuture
     */
    public CompletableFuture<Map<String, Object>> chatAsync(String content, String sessionId) {
        Map<String, Object> data = new HashMap<>();
        data.put("content", content);

        if (sessionId != null && !sessionId.isEmpty()) {
            data.put("session_id", sessionId);
        } else if (this.sessionId != null && !this.sessionId.isEmpty()) {
            data.put("session_id", this.sessionId);
        }
        
        // 커스텀 LLM 설정이 있는 경우 추가
        if (llmConfig != null) {
            Map<String, Object> llmData = new HashMap<>();
            llmData.put("model_name", llmConfig.getModelName());
            llmData.put("model_endpoint", llmConfig.getModelEndpoint());
            
            if (llmConfig.getApiKey() != null) {
                llmData.put("api_key", llmConfig.getApiKey());
            }
            
            if (!llmConfig.getParameters().isEmpty()) {
                llmData.put("parameters", llmConfig.getParameters());
            }
            
            if (!llmConfig.getResponseMapping().isEmpty()) {
                llmData.put("response_mapping", llmConfig.getResponseMapping());
            }
            
            data.put("llm_config", llmData);
        }

        return requestAsync("/api/v1/chat", "POST", data);
    }
    
    /**
     * 비동기 채팅 메시지 전송 (요청별 커스텀 LLM 설정)
     * 
     * @param content   사용자 메시지 내용
     * @param sessionId 세션 ID (선택 사항)
     * @param requestLlmConfig 이 요청에만 적용할 커스텀 LLM 설정
     * @return 채팅 응답을 포함한 CompletableFuture
     */
    public CompletableFuture<Map<String, Object>> chatAsync(String content, String sessionId, CustomLLMConfig requestLlmConfig) {
        Map<String, Object> data = new HashMap<>();
        data.put("content", content);

        if (sessionId != null && !sessionId.isEmpty()) {
            data.put("session_id", sessionId);
        } else if (this.sessionId != null && !this.sessionId.isEmpty()) {
            data.put("session_id", this.sessionId);
        }
        
        // 요청별 커스텀 LLM 설정 추가
        if (requestLlmConfig != null) {
            Map<String, Object> llmData = new HashMap<>();
            llmData.put("model_name", requestLlmConfig.getModelName());
            llmData.put("model_endpoint", requestLlmConfig.getModelEndpoint());
            
            if (requestLlmConfig.getApiKey() != null) {
                llmData.put("api_key", requestLlmConfig.getApiKey());
            }
            
            if (!requestLlmConfig.getParameters().isEmpty()) {
                llmData.put("parameters", requestLlmConfig.getParameters());
            }
            
            if (!requestLlmConfig.getResponseMapping().isEmpty()) {
                llmData.put("response_mapping", requestLlmConfig.getResponseMapping());
            }
            
            data.put("llm_config", llmData);
        }

        return requestAsync("/api/chat", "POST", data);
    }

    /**
     * 콘텐츠 생성
     * 
     * @param prompt 생성 프롬프트
     * @param maxTokens 최대 토큰 수 (선택 사항)
     * @param temperature 온도 (선택 사항)
     * @return 생성된 콘텐츠
     * @throws MCPException API 오류 발생 시
     */
    public Map<String, Object> generate(String prompt, Integer maxTokens, Double temperature) throws MCPException {
        Map<String, Object> data = new HashMap<>();
        data.put("prompt", prompt);

        if (maxTokens != null) {
            data.put("max_tokens", maxTokens);
        }

        if (temperature != null) {
            data.put("temperature", temperature);
        }
        
        // 커스텀 LLM 설정이 있는 경우 추가
        if (llmConfig != null) {
            Map<String, Object> llmData = new HashMap<>();
            llmData.put("model_name", llmConfig.getModelName());
            llmData.put("model_endpoint", llmConfig.getModelEndpoint());
            
            if (llmConfig.getApiKey() != null) {
                llmData.put("api_key", llmConfig.getApiKey());
            }
            
            if (!llmConfig.getParameters().isEmpty()) {
                llmData.put("parameters", llmConfig.getParameters());
            }
            
            if (!llmConfig.getResponseMapping().isEmpty()) {
                llmData.put("response_mapping", llmConfig.getResponseMapping());
            }
            
            data.put("llm_config", llmData);
        }

        return request("/api/generate", "POST", data);
    }
    
    /**
     * 콘텐츠 생성 (요청별 커스텀 LLM 설정)
     * 
     * @param prompt 생성 프롬프트
     * @param maxTokens 최대 토큰 수 (선택 사항)
     * @param temperature 온도 (선택 사항)
     * @param requestLlmConfig 이 요청에만 적용할 커스텀 LLM 설정
     * @return 생성된 콘텐츠
     * @throws MCPException API 오류 발생 시
     */
    public Map<String, Object> generate(String prompt, Integer maxTokens, Double temperature, 
                                      CustomLLMConfig requestLlmConfig) throws MCPException {
        Map<String, Object> data = new HashMap<>();
        data.put("prompt", prompt);

        if (maxTokens != null) {
            data.put("max_tokens", maxTokens);
        }

        if (temperature != null) {
            data.put("temperature", temperature);
        }
        
        // 요청별 커스텀 LLM 설정 추가
        if (requestLlmConfig != null) {
            Map<String, Object> llmData = new HashMap<>();
            llmData.put("model_name", requestLlmConfig.getModelName());
            llmData.put("model_endpoint", requestLlmConfig.getModelEndpoint());
            
            if (requestLlmConfig.getApiKey() != null) {
                llmData.put("api_key", requestLlmConfig.getApiKey());
            }
            
            if (!requestLlmConfig.getParameters().isEmpty()) {
                llmData.put("parameters", requestLlmConfig.getParameters());
            }
            
            if (!requestLlmConfig.getResponseMapping().isEmpty()) {
                llmData.put("response_mapping", requestLlmConfig.getResponseMapping());
            }
            
            data.put("llm_config", llmData);
        }

        return request("/api/generate", "POST", data);
    }

    /**
     * 비동기 콘텐츠 생성
     * 
     * @param prompt 생성 프롬프트
     * @return 생성된 콘텐츠를 포함한 CompletableFuture
     */
    public CompletableFuture<Map<String, Object>> generateAsync(String prompt) {
        Map<String, Object> data = new HashMap<>();
        data.put("prompt", prompt);
        
        // 커스텀 LLM 설정이 있는 경우 추가
        if (llmConfig != null) {
            Map<String, Object> llmData = new HashMap<>();
            llmData.put("model_name", llmConfig.getModelName());
            llmData.put("model_endpoint", llmConfig.getModelEndpoint());
            
            if (llmConfig.getApiKey() != null) {
                llmData.put("api_key", llmConfig.getApiKey());
            }
            
            if (!llmConfig.getParameters().isEmpty()) {
                llmData.put("parameters", llmConfig.getParameters());
            }
            
            if (!llmConfig.getResponseMapping().isEmpty()) {
                llmData.put("response_mapping", llmConfig.getResponseMapping());
            }
            
            data.put("llm_config", llmData);
        }
        
        return requestAsync("/api/generate", "POST", data);
    }
    
    /**
     * 비동기 콘텐츠 생성 (요청별 커스텀 LLM 설정)
     * 
     * @param prompt 생성 프롬프트
     * @param requestLlmConfig 이 요청에만 적용할 커스텀 LLM 설정
     * @return 생성된 콘텐츠를 포함한 CompletableFuture
     */
    public CompletableFuture<Map<String, Object>> generateAsync(String prompt, CustomLLMConfig requestLlmConfig) {
        Map<String, Object> data = new HashMap<>();
        data.put("prompt", prompt);
        
        // 요청별 커스텀 LLM 설정 추가
        if (requestLlmConfig != null) {
            Map<String, Object> llmData = new HashMap<>();
            llmData.put("model_name", requestLlmConfig.getModelName());
            llmData.put("model_endpoint", requestLlmConfig.getModelEndpoint());
            
            if (requestLlmConfig.getApiKey() != null) {
                llmData.put("api_key", requestLlmConfig.getApiKey());
            }
            
            if (!requestLlmConfig.getParameters().isEmpty()) {
                llmData.put("parameters", requestLlmConfig.getParameters());
            }
            
            if (!requestLlmConfig.getResponseMapping().isEmpty()) {
                llmData.put("response_mapping", requestLlmConfig.getResponseMapping());
            }
            
            data.put("llm_config", llmData);
        }
        
        return requestAsync("/api/generate", "POST", data);
    }

    /**
     * 피드백 제공
     * 
     * @param requestId 요청 ID
     * @param rating 평점 (1-5)
     * @param comment 코멘트 (선택 사항)
     * @return 피드백 응답
     * @throws MCPException API 오류 발생 시
     */
    public Map<String, Object> provideFeedback(String requestId, int rating, String comment) throws MCPException {
        Map<String, Object> data = new HashMap<>();
        data.put("request_id", requestId);
        data.put("rating", rating);

        if (comment != null && !comment.isEmpty()) {
            data.put("comment", comment);
        }

        return request("/api/feedback", "POST", data);
    }

    /**
     * 피드백 조회
     * 
     * @param requestId 요청 ID
     * @return 피드백 정보
     * @throws MCPException API 오류 발생 시
     */
    public Map<String, Object> getFeedback(String requestId) throws MCPException {
        return request("/api/feedback/" + requestId, "GET", null);
    }

    /**
     * 채팅 세션 생성
     * 
     * @return 새 채팅 세션
     */
    public ChatSession createChatSession() {
        return new ChatSession(this);
    }

    /**
     * 채팅 세션 클래스
     */
    public static class ChatSession {
        private final MCPClient client;
        private String sessionId;
        private final List<Map<String, Object>> messages;

        /**
         * 채팅 세션 생성자
         * 
         * @param client MCP 클라이언트
         */
        public ChatSession(MCPClient client) {
            this.client = client;
            this.sessionId = null;
            this.messages = new ArrayList<>();
        }

        /**
         * 메시지 전송
         * 
         * @param content 사용자 메시지 내용
         * @return 채팅 응답
         * @throws MCPException API 오류 발생 시
         */
        public Map<String, Object> sendMessage(String content) throws MCPException {
            Map<String, Object> response = client.chat(content);
            this.sessionId = (String) response.get("session_id");

            // 메시지 기록 저장
            Map<String, Object> userMessage = new HashMap<>();
            userMessage.put("role", "user");
            userMessage.put("content", content);
            messages.add(userMessage);

            @SuppressWarnings("unchecked")
            Map<String, Object> assistantMessage = (Map<String, Object>) response.get("message");
            messages.add(assistantMessage);

            return assistantMessage;
        }

        /**
         * 메시지 비동기 전송
         * 
         * @param content 사용자 메시지 내용
         * @return 채팅 응답을 포함한 CompletableFuture
         */
        public CompletableFuture<Map<String, Object>> sendMessageAsync(String content) {
            return client.chatAsync(content, sessionId).thenApply(response -> {
                // 세션 ID 저장
                this.sessionId = (String) response.get("session_id");

                // 메시지 기록 저장
                Map<String, Object> userMessage = new HashMap<>();
                userMessage.put("role", "user");
                userMessage.put("content", content);
                messages.add(userMessage);

                @SuppressWarnings("unchecked")
                Map<String, Object> assistantMessage = (Map<String, Object>) response.get("message");
                messages.add(assistantMessage);

                return assistantMessage;
            });
        }

        /**
         * 세션 기록 가져오기
         * 
         * @return 세션 메시지 기록
         */
        public List<Map<String, Object>> getHistory() {
            return new ArrayList<>(messages);
        }

        /**
         * 세션 초기화
         */
        public void reset() {
            this.sessionId = null;
            this.messages.clear();
        }

        /**
         * 세션 ID 가져오기
         * 
         * @return 세션 ID
         */
        public String getSessionId() {
            return sessionId;
        }
    }

    /**
     * MCP 클라이언트 오류 클래스
     */
    public static class MCPException extends Exception {
        private static final long serialVersionUID = 1L;
        private final int statusCode;
        private final Map<String, Object> data;

        /**
         * MCP 오류 생성자
         * 
         * @param message    오류 메시지
         * @param statusCode HTTP 상태 코드
         * @param data       추가 오류 데이터
         */
        public MCPException(String message, int statusCode, Map<String, Object> data) {
            super(message);
            this.statusCode = statusCode;
            this.data = data != null ? data : new HashMap<>();
        }

        /**
         * MCP 오류 생성자 (데이터 없음)
         * 
         * @param message 오류 메시지
         */
        public MCPException(String message) {
            this(message, 0, null);
        }

        /**
         * HTTP 상태 코드 가져오기
         * 
         * @return HTTP 상태 코드
         */
        public int getStatusCode() {
            return statusCode;
        }

        /**
         * 오류 데이터 가져오기
         * 
         * @return 오류 데이터
         */
        public Map<String, Object> getData() {
            return new HashMap<>(data);
        }
    }
}

/**
 * MCP 클라이언트 사용 예시
 */
class MCPClientExample {
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

            // 비동기 예제
            client.checkHealthAsync()
                    .thenCompose(health -> {
                        System.out.println("비동기 서버 상태: " + health);
                        return client.generateAsync("비동기 프로그래밍의 장점은 무엇인가요?");
                    })
                    .thenAccept(content -> {
                        System.out.println("비동기 생성 콘텐츠: " + content.get("content"));
                    })
                    .join(); // 예제를 위해 완료 대기
                    
            // 커스텀 LLM 설정 예시
            System.out.println("\n=== 커스텀 LLM 사용 예시 ===");
            
            // 커스텀 LLM 파라미터 설정
            Map<String, Object> llmParams = new HashMap<>();
            llmParams.put("temperature", 0.8);
            llmParams.put("max_tokens", 500);
            llmParams.put("top_p", 0.95);
            
            // 응답 필드 매핑 설정
            Map<String, String> responseMapping = new HashMap<>();
            responseMapping.put("content", "choices[0].message.content");
            responseMapping.put("model", "model");
            
            // 커스텀 LLM 설정 생성
            CustomLLMConfig llmConfig = new CustomLLMConfig(
                "gpt-4",
                "https://api.openai.com/v1/chat/completions",
                "your-openai-api-key",
                llmParams,
                responseMapping
            );
            
            // 커스텀 LLM을 사용하는 클라이언트 생성
            MCPClient customLLMClient = new MCPClient("your-api-key", "http://localhost:8000", llmConfig);
            
            // 커스텀 LLM으로 채팅
            Map<String, Object> customLLMResponse = customLLMClient.chat("커스텀 LLM을 사용한 질문입니다.");
            System.out.println("커스텀 LLM 응답: " + customLLMResponse.get("content"));
            
            // 요청별 커스텀 LLM 설정 사용
            CustomLLMConfig requestSpecificConfig = new CustomLLMConfig(
                "claude-3-opus",
                "https://api.anthropic.com/v1/messages",
                "your-anthropic-api-key",
                new HashMap<String, Object>() {{
                    put("temperature", 0.5);
                    put("max_tokens", 1000);
                }}
            );
            
            // 기본 클라이언트에서 요청별 커스텀 LLM 사용
            Map<String, Object> requestSpecificResponse = client.chat(
                "이 질문은 요청별 커스텀 LLM 설정을 사용합니다.", 
                requestSpecificConfig
            );
            System.out.println("요청별 커스텀 LLM 응답: " + requestSpecificResponse.get("content"));

        } catch (MCPClient.MCPException e) {
            System.err.println("오류 발생: " + e.getMessage());
            System.err.println("상태 코드: " + e.getStatusCode());
            System.err.println("오류 데이터: " + e.getData());
        } catch (Exception e) {
            System.err.println("예상치 못한 오류: " + e.getMessage());
            e.printStackTrace();
        }
    }
}