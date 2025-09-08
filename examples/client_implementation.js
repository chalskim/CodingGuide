/**
 * MCP 클라이언트 구현 예제 (JavaScript)
 * 
 * 이 파일은 MCP 서버와 통신하기 위한 클라이언트 라이브러리의 구현 예제입니다.
 * 실제 프로젝트에서는 공식 클라이언트 라이브러리를 사용하는 것을 권장합니다.
 * 
 * .env 파일 로딩을 위해 dotenv 패키지를 사용합니다.
 * npm install dotenv
 */

// .env 파일 로드
require('dotenv').config();

class MCPClient {
  /**
   * MCP 클라이언트 생성자
   * @param {string} apiKey - MCP 서버 인증을 위한 API 키 (기본값: 환경 변수 MCP_API_KEY)
   * @param {string} baseUrl - MCP 서버 기본 URL (기본값: 환경 변수 MCP_BASE_URL 또는 http://localhost:8000)
   * @param {string} searchApiKey - 검색 API 키 (기본값: 환경 변수 MCP_SEARCH_API_KEY)
   * @param {string} searchEngineId - 검색 엔진 ID (기본값: 환경 변수 MCP_SEARCH_ENGINE_ID)
   * @param {string} searchProvider - 검색 제공자 (기본값: 환경 변수 SEARCH_PROVIDER 또는 'google')
   */
  constructor(options = {}) {
    // 환경 변수에서 설정 로드
    this.apiKey = options.apiKey || process.env.MCP_API_KEY;
    this.baseUrl = options.baseUrl || process.env.MCP_BASE_URL || 'http://localhost:9000';
    this.searchApiKey = options.searchApiKey || process.env.MCP_SEARCH_API_KEY;
    this.searchEngineId = options.searchEngineId || process.env.MCP_SEARCH_ENGINE_ID;
    this.searchProvider = options.searchProvider || process.env.SEARCH_PROVIDER || 'google';
    this.sessionId = null;
    
    // API 키가 없으면 오류 발생
    if (!this.apiKey) {
      throw new Error("API 키가 필요합니다. 매개변수로 전달하거나 MCP_API_KEY 환경 변수를 설정하세요.");
    }
  }

  /**
   * HTTP 요청을 보내는 유틸리티 메서드
   * @param {string} endpoint - API 엔드포인트
   * @param {string} method - HTTP 메서드 (GET, POST 등)
   * @param {Object} data - 요청 본문 데이터
   * @returns {Promise<Object>} - 응답 데이터
   */
  async request(endpoint, method = 'GET', data = null) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey
    };
    
    // 검색 API 키와 검색 엔진 ID가 있고 검색 관련 엔드포인트인 경우 헤더에 추가
    if (endpoint.includes('/search')) {
      if (this.searchApiKey) {
        headers['X-Search-API-Key'] = this.searchApiKey;
      }
      if (this.searchEngineId) {
        headers['X-Search-Engine-ID'] = this.searchEngineId;
      }
      if (this.searchProvider) {
        headers['X-Search-Provider'] = this.searchProvider;
      }
    }

    const options = {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined
    };

    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new MCPError(
          `API 오류: ${errorData.error?.message || '알 수 없는 오류'}`,
          response.status,
          errorData
        );
      }
      
      return await response.json();
    } catch (error) {
      if (error instanceof MCPError) {
        throw error;
      }
      throw new MCPError(
        `네트워크 오류: ${error.message}`,
        0,
        { originalError: error }
      );
    }
  }

  /**
   * 서버 상태 확인
   * @returns {Promise<Object>} - 서버 상태 정보
   */
  async checkHealth() {
    return this.request('/health');
  }

  /**
   * 채팅 메시지 전송
   * @param {string} message - 사용자 메시지 내용
   * @param {string|null} sessionId - 세션 ID (없으면 새 세션 생성)
   * @returns {Promise<Object>} - 채팅 응답
   */
  async chat(message, sessionId = null) {
    const data = {
      session_id: sessionId || this.sessionId,
      message: {
        content: message,
        role: 'user'
      }
    };

    const response = await this.request('/api/v1/chat', 'POST', data);
    
    // 세션 ID 저장
    this.sessionId = response.session_id;
    
    return response;
  }

  /**
   * 콘텐츠 생성
   * @param {string} prompt - 생성 프롬프트
   * @param {number} maxTokens - 최대 토큰 수
   * @param {number} temperature - 생성 온도 (창의성 조절)
   * @returns {Promise<Object>} - 생성된 콘텐츠
   */
  async generate(prompt, maxTokens = 100, temperature = 0.7) {
    const data = {
      prompt,
      max_tokens: maxTokens,
      temperature
    };

    return this.request('/generate', 'POST', data);
  }

  /**
   * 피드백 제공
   * @param {string} requestId - 피드백을 제공할 요청 ID
   * @param {number} rating - 평점 (1-5)
   * @param {string} comment - 피드백 코멘트
   * @returns {Promise<Object>} - 피드백 응답
   */
  async provideFeedback(requestId, rating, comment = '') {
    const data = {
      request_id: requestId,
      rating,
      comment
    };

    return this.request('/feedback', 'POST', data);
  }

  /**
   * 특정 요청에 대한 피드백 조회
   * @param {string} requestId - 조회할 요청 ID
   * @returns {Promise<Object>} - 피드백 정보
   */
  async getFeedback(requestId) {
    return this.request(`/feedback/request/${requestId}`);
  }

  /**
   * 채팅 세션 생성
   * @returns {ChatSession} - 채팅 세션 객체
   */
  createChatSession() {
    return new ChatSession(this);
  }
}

/**
 * 채팅 세션 클래스
 * 연속적인 대화를 위한 세션 관리
 */
class ChatSession {
  /**
   * 채팅 세션 생성자
   * @param {MCPClient} client - MCP 클라이언트 인스턴스
   */
  constructor(client) {
    this.client = client;
    this.sessionId = null;
    this.messages = [];
  }

  /**
   * 메시지 전송
   * @param {string} content - 사용자 메시지 내용
   * @returns {Promise<Object>} - 채팅 응답
   */
  async sendMessage(content) {
    const response = await this.client.chat(content, this.sessionId);
    
    // 세션 ID 저장
    this.sessionId = response.session_id;
    
    // 메시지 기록 저장
    this.messages.push({
      role: 'user',
      content
    });
    
    this.messages.push({
      role: 'assistant',
      content: response.message.content
    });
    
    return response.message;
  }

  /**
   * 세션 기록 가져오기
   * @returns {Array} - 세션 메시지 기록
   */
  getHistory() {
    return [...this.messages];
  }

  /**
   * 세션 초기화
   */
  reset() {
    this.sessionId = null;
    this.messages = [];
  }
}

/**
 * MCP 클라이언트 오류 클래스
 */
class MCPError extends Error {
  /**
   * MCP 오류 생성자
   * @param {string} message - 오류 메시지
   * @param {number} statusCode - HTTP 상태 코드
   * @param {Object} data - 추가 오류 데이터
   */
  constructor(message, statusCode = 0, data = {}) {
    super(message);
    this.name = 'MCPError';
    this.statusCode = statusCode;
    this.data = data;
  }
}

// 사용 예시
async function example() {
  try {
    // 클라이언트 초기화
    const client = new MCPClient('your-api-key', 'http://localhost:8000');
    
    // 서버 상태 확인
    const healthStatus = await client.checkHealth();
    console.log('서버 상태:', healthStatus);
    
    // 채팅 세션 생성
    const session = client.createChatSession();
    
    // 첫 번째 메시지 전송
    const response1 = await session.sendMessage('안녕하세요, MCP!');
    console.log('AI 응답 1:', response1.content);
    
    // 후속 메시지 전송 (세션 유지)
    const response2 = await session.sendMessage('MCP 서버의 주요 기능은 무엇인가요?');
    console.log('AI 응답 2:', response2.content);
    
    // 세션 기록 확인
    const history = session.getHistory();
    console.log('대화 기록:', history);
    
    // 콘텐츠 생성
    const generatedContent = await client.generate(
      '인공지능의 미래 발전 방향에 대해 설명해주세요',
      200,
      0.8
    );
    console.log('생성된 콘텐츠:', generatedContent.content);
    
    // 피드백 제공
    const feedbackResponse = await client.provideFeedback(
      generatedContent.request_id,
      5,
      '매우 유용한 정보를 제공해주셔서 감사합니다!'
    );
    console.log('피드백 제출 완료:', feedbackResponse);
    
  } catch (error) {
    console.error('오류 발생:', error.message);
    if (error instanceof MCPError) {
      console.error('상태 코드:', error.statusCode);
      console.error('오류 데이터:', error.data);
    }
  }
}

// Node.js 환경에서 실행
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MCPClient, ChatSession, MCPError };
}

// 브라우저 환경에서 실행
if (typeof window !== 'undefined') {
  window.MCPClient = MCPClient;
  window.ChatSession = ChatSession;
  window.MCPError = MCPError;
}