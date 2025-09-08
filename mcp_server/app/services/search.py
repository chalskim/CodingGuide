from typing import Dict, Any, List, Optional
from loguru import logger
import httpx
import json
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

class SearchService:
    """외부 검색 서비스
    
    다양한 검색 API를 통합하여 외부 지식 검색 기능을 제공합니다.
    """
    
    def __init__(self):
        # 기본값 설정 (클라이언트에서 제공받음)
        self.api_key = None  # 클라이언트에서 제공받을 예정
        self.search_engine_id = None  # 클라이언트에서 제공받을 예정
        self.api_base_url = getattr(settings, "SEARCH_API_BASE_URL", "https://www.googleapis.com/customsearch/v1")
        self.perplexity_api_url = getattr(settings, "PERPLEXITY_API_URL", "https://api.perplexity.ai/chat/completions")
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search(self, 
                   query: str, 
                   num_results: int = 5,
                   search_type: str = "web",
                   options: Optional[Dict[str, Any]] = None,
                   api_key: Optional[str] = None,
                   search_engine_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """외부 검색 수행
        
        Args:
            query: 검색 쿼리
            num_results: 반환할 최대 결과 수
            search_type: 검색 유형 (web, image, news 등)
            options: 추가 검색 옵션
            api_key: 클라이언트에서 제공한 검색 API 키
            search_engine_id: 클라이언트에서 제공한 검색 엔진 ID
            
        Returns:
            검색 결과 목록
        """
        try:
            # 검색 제공자 확인
            search_provider = getattr(settings, "SEARCH_PROVIDER", "google").lower()
            
            # 클라이언트에서 제공한 API 키와 검색 엔진 ID 설정
            if api_key:
                self.api_key = api_key
            if search_engine_id and search_provider != "perplexity":
                self.search_engine_id = search_engine_id
                
            # API 키가 없으면 모의 검색 결과 반환
            if not self.api_key or (not self.search_engine_id and search_provider != "perplexity"):
                logger.warning("Search API key or engine ID not provided. Using mock search results.")
                return await self._search_mock(query, num_results, search_type, options)
                
            # 검색 API 선택 및 요청 수행
            search_provider = getattr(settings, "SEARCH_PROVIDER", "google").lower()
            if search_provider == "google":
                return await self._search_google(query, num_results, search_type, options)
            elif search_provider == "bing":
                return await self._search_bing(query, num_results, search_type, options)
            elif search_provider == "duckduckgo":
                return await self._search_duckduckgo(query, num_results, search_type, options)
            elif search_provider == "perplexity":
                return await self._search_perplexity(query, num_results, search_type, options)
            else:
                # 기본값: 모의 검색 결과 반환
                return await self._search_mock(query, num_results, search_type, options)
                
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            # 오류 발생 시 빈 결과 반환
            return []
    
    async def _search_google(self, 
                           query: str, 
                           num_results: int, 
                           search_type: str,
                           options: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Google Custom Search API를 사용한 검색"""
        try:
            # API 요청 URL 구성
            url = f"{self.api_base_url}?key={self.api_key}&cx={self.search_engine_id}&q={query}&num={num_results}"
            
            # 검색 유형에 따른 파라미터 추가
            if search_type == "image":
                url += "&searchType=image"
            elif search_type == "news":
                url += "&sort=date"
            
            # 추가 옵션 적용
            if options:
                for key, value in options.items():
                    url += f"&{key}={value}"
            
            # API 요청 전송
            response = await self.client.get(url)
            
            # 응답 처리
            if response.status_code == 200:
                result = response.json()
                
                # 검색 결과 변환
                search_results = []
                if "items" in result:
                    for item in result["items"]:
                        search_result = {
                            "title": item.get("title", ""),
                            "link": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "google"
                        }
                        
                        # 이미지 검색 결과인 경우 이미지 URL 추가
                        if search_type == "image" and "image" in item:
                            search_result["image_url"] = item["image"].get("thumbnailLink", "")
                        
                        search_results.append(search_result)
                
                return search_results
            else:
                logger.error(f"Google search API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Google search failed: {str(e)}")
            return []
    
    async def _search_bing(self, 
                         query: str, 
                         num_results: int, 
                         search_type: str,
                         options: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bing Search API를 사용한 검색"""
        try:
            # API 요청 헤더 구성
            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key
            }
            
            # 검색 유형에 따른 엔드포인트 및 파라미터 설정
            if search_type == "image":
                endpoint = f"{self.api_base_url}/images/search"
            elif search_type == "news":
                endpoint = f"{self.api_base_url}/news/search"
            else:
                endpoint = f"{self.api_base_url}/search"
            
            # 쿼리 파라미터 구성
            params = {
                "q": query,
                "count": num_results,
                "responseFilter": "webPages,news,entities"
            }
            
            # 추가 옵션 적용
            if options:
                params.update(options)
            
            # API 요청 전송
            response = await self.client.get(endpoint, headers=headers, params=params)
            
            # 응답 처리
            if response.status_code == 200:
                result = response.json()
                
                # 검색 결과 변환
                search_results = []
                
                # 웹 검색 결과 처리
                if "webPages" in result and "value" in result["webPages"]:
                    for item in result["webPages"]["value"]:
                        search_results.append({
                            "title": item.get("name", ""),
                            "link": item.get("url", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "bing"
                        })
                
                # 뉴스 검색 결과 처리
                if "news" in result and "value" in result["news"]:
                    for item in result["news"]["value"]:
                        search_results.append({
                            "title": item.get("name", ""),
                            "link": item.get("url", ""),
                            "snippet": item.get("description", ""),
                            "source": "bing_news",
                            "published": item.get("datePublished", "")
                        })
                
                # 이미지 검색 결과 처리
                if "images" in result and "value" in result["images"]:
                    for item in result["images"]["value"]:
                        search_results.append({
                            "title": item.get("name", ""),
                            "link": item.get("hostPageUrl", ""),
                            "snippet": item.get("name", ""),
                            "source": "bing_image",
                            "image_url": item.get("thumbnailUrl", "")
                        })
                
                return search_results
            else:
                logger.error(f"Bing search API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Bing search failed: {str(e)}")
            return []
    
    async def _search_duckduckgo(self, 
                              query: str, 
                              num_results: int, 
                              search_type: str,
                              options: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """DuckDuckGo API를 사용한 검색"""
        try:
            # DuckDuckGo Instant Answer API 사용
            url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=0"
            
            # API 요청 전송
            response = await self.client.get(url)
            
            # 응답 처리
            if response.status_code == 200:
                result = response.json()
                
                # 검색 결과 변환
                search_results = []
                
                # Abstract 결과 추가
                if result.get("Abstract"):
                    search_results.append({
                        "title": result.get("Heading", ""),
                        "link": result.get("AbstractURL", ""),
                        "snippet": result.get("Abstract", ""),
                        "source": "duckduckgo_abstract"
                    })
                
                # Related Topics 결과 추가
                if "RelatedTopics" in result:
                    for topic in result["RelatedTopics"][:num_results]:
                        if "Text" in topic and "FirstURL" in topic:
                            search_results.append({
                                "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else topic.get("Text", ""),
                                "link": topic.get("FirstURL", ""),
                                "snippet": topic.get("Text", ""),
                                "source": "duckduckgo_related"
                            })
                
                return search_results[:num_results]
            else:
                logger.error(f"DuckDuckGo search API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {str(e)}")
            return []
    
    async def _search_mock(self, 
                        query: str, 
                        num_results: int, 
                        search_type: str,
                        options: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """모의 검색 결과 반환 (API 키 없을 때 사용)"""
        # 모의 검색 결과 생성
        mock_results = [
            {
                "title": f"Mock Result 1 for '{query}'",
                "link": "https://example.com/result1",
                "snippet": f"This is a mock search result for the query '{query}'. It contains some sample text that might be relevant to the search.",
                "source": "mock_search"
            },
            {
                "title": f"Mock Result 2 for '{query}'",
                "link": "https://example.com/result2",
                "snippet": f"Another mock search result for '{query}'. This is just placeholder text to simulate a real search result.",
                "source": "mock_search"
            },
            {
                "title": f"Mock Result 3 for '{query}'",
                "link": "https://example.com/result3",
                "snippet": f"A third mock search result for the query '{query}'. In a real search, this would contain an excerpt from the webpage.",
                "source": "mock_search"
            }
        ]
        
        # 이미지 검색인 경우 이미지 URL 추가
        if search_type == "image":
            for result in mock_results:
                result["image_url"] = f"https://example.com/images/{result['title'].replace(' ', '_').lower()}.jpg"
        
        # 뉴스 검색인 경우 발행일 추가
        if search_type == "news":
            import datetime
            for i, result in enumerate(mock_results):
                result["published"] = (datetime.datetime.now() - datetime.timedelta(days=i)).isoformat()
        
        # 결과 수 제한
        return mock_results[:num_results]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _search_perplexity(self, query: str, num_results: int = 5, search_type: str = "web", options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Perplexity API를 사용하여 검색 수행"""
        try:
            if not self.api_key:
                logger.warning("Perplexity API 키가 제공되지 않았습니다. 모의 검색 결과를 반환합니다.")
                return await self._search_mock(query, num_results, search_type, options)

            # 요청 헤더 설정
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            # 요청 본문 설정
            payload = {
                "model": "sonar-medium-online",  # 온라인 검색 기능이 있는 모델 사용
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that provides search results."},
                    {"role": "user", "content": f"Search for: {query}"}
                ],
                "options": {
                    "temperature": 0.0,  # 결정적인 응답을 위해 낮은 온도 설정
                }
            }

            # 검색 타입에 따른 옵션 설정
            if search_type == "web":
                payload["options"]["search_domain"] = "internet"
            elif search_type == "news":
                payload["options"]["search_domain"] = "news"
                payload["options"]["recency_days"] = 7  # 최근 7일 내 뉴스로 제한
            elif search_type == "image":
                # 이미지 검색은 별도 처리 필요
                payload["options"]["search_domain"] = "internet"
                payload["messages"][1]["content"] = f"Search for images of: {query}"

            # 추가 옵션 적용
            if options:
                if "recency_days" in options:
                    payload["options"]["recency_days"] = options["recency_days"]

            # API 요청 전송
            response = await self.client.post(
                self.perplexity_api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            # 응답 처리 및 결과 변환
            search_results = []
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                
                # 응답에서 URL 추출 (간단한 구현)
                import re
                urls = re.findall(r'https?://[^\s)"]+', content)
                titles = re.findall(r'\*\*([^*]+)\*\*', content) or [f"Result {i+1}" for i in range(len(urls))]
                
                # 결과 형식화
                for i, (url, title) in enumerate(zip(urls[:num_results], titles[:num_results])):
                    snippet = content.split(url)[1].split("\n")[0] if url in content else ""
                    search_results.append({
                        "title": title,
                        "link": url,
                        "snippet": snippet.strip(),
                        "position": i + 1
                    })
                    
                    # 이미지 검색인 경우 이미지 URL 추가
                    if search_type == "image" and url.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                        search_results[-1]["image_url"] = url
                    
                    # 뉴스 검색인 경우 출처 및 날짜 추가
                    if search_type == "news":
                        source_match = re.search(r'Source: ([^\n]+)', content)
                        date_match = re.search(r'Date: ([^\n]+)', content)
                        if source_match:
                            search_results[-1]["source"] = source_match.group(1)
                        if date_match:
                            search_results[-1]["date"] = date_match.group(1)

            # 결과가 없는 경우 모의 결과 반환
            if not search_results:
                logger.warning("Perplexity API에서 검색 결과를 찾을 수 없습니다. 모의 검색 결과를 반환합니다.")
                return await self._search_mock(query, num_results, search_type, options)

            return search_results[:num_results]

        except Exception as e:
            logger.error(f"Perplexity 검색 중 오류 발생: {str(e)}")
            # 오류 발생 시 모의 검색 결과 반환
            return await self._search_mock(query, num_results, search_type, options)

    async def close(self):
        """클라이언트 종료"""
        if self.client:
            await self.client.aclose()