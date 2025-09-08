/**
 * 커스텀 LLM 설정을 위한 클래스
 */

import java.util.HashMap;
import java.util.Map;

public class CustomLLMConfig {
    private final String modelName;
    private final String modelEndpoint;
    private final String apiKey;
    private final Map<String, Object> parameters;
    private final Map<String, String> responseMapping;

    /**
     * 커스텀 LLM 설정 생성자
     * 
     * @param modelName 모델 이름
     * @param modelEndpoint 모델 엔드포인트 URL
     * @param apiKey 모델 API 키 (선택 사항)
     * @param parameters 모델 파라미터 (선택 사항)
     */
    public CustomLLMConfig(String modelName, String modelEndpoint, String apiKey, Map<String, Object> parameters) {
        this.modelName = modelName;
        this.modelEndpoint = modelEndpoint;
        this.apiKey = apiKey;
        this.parameters = parameters != null ? parameters : new HashMap<>();
        this.responseMapping = new HashMap<>();
    }

    /**
     * 커스텀 LLM 설정 생성자 (응답 매핑 포함)
     * 
     * @param modelName 모델 이름
     * @param modelEndpoint 모델 엔드포인트 URL
     * @param apiKey 모델 API 키 (선택 사항)
     * @param parameters 모델 파라미터 (선택 사항)
     * @param responseMapping 응답 필드 매핑 (선택 사항)
     */
    public CustomLLMConfig(String modelName, String modelEndpoint, String apiKey, 
                          Map<String, Object> parameters, Map<String, String> responseMapping) {
        this.modelName = modelName;
        this.modelEndpoint = modelEndpoint;
        this.apiKey = apiKey;
        this.parameters = parameters != null ? parameters : new HashMap<>();
        this.responseMapping = responseMapping != null ? responseMapping : new HashMap<>();
    }

    public String getModelName() {
        return modelName;
    }

    public String getModelEndpoint() {
        return modelEndpoint;
    }

    public String getApiKey() {
        return apiKey;
    }

    public Map<String, Object> getParameters() {
        return parameters;
    }

    public Map<String, String> getResponseMapping() {
        return responseMapping;
    }
}