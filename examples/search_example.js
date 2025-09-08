/**
 * 검색 API 키와 검색 엔진 ID를 사용하는 JavaScript 클라이언트 예제
 */

// .env 파일 로드 (Node.js 환경)
require('dotenv').config();

const { MCPClient } = require('./client_implementation');

async function main() {
  // 환경 변수에서 설정 로드
  const apiKey = process.env.MCP_API_KEY;
  const baseUrl = process.env.MCP_BASE_URL || 'http://localhost:9000';
  const searchApiKey = process.env.PERPLEXITY_API_KEY || process.env.MCP_SEARCH_API_KEY;
  const searchEngineId = process.env.MCP_SEARCH_ENGINE_ID;
  const searchProvider = process.env.SEARCH_PROVIDER || 'perplexity';
  
  // 클라이언트 생성
  const client = new MCPClient({
    apiKey,
    baseUrl,
    searchApiKey,
    searchEngineId,
    searchProvider
  });
  
  // 검색 요청 예제
  try {
    const searchResult = await client.request('/api/v1/search', 'POST', {
      query: 'MCP 서버 아키텍처',
      num_results: 5,
      options: {
        search_provider: searchProvider,
        api_key: searchApiKey
      }
    });
    
    console.log('검색 결과:');
    searchResult.results.forEach((result, index) => {
      console.log(`${index + 1}. ${result.title}`);
      console.log(`   URL: ${result.link}`);
      console.log(`   스니펫: ${result.snippet}`);
      console.log();
    });
    
  } catch (error) {
    console.error(`검색 요청 중 오류 발생: ${error.message}`);
  }
}

main().catch(console.error);