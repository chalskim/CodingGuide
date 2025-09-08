from typing import Dict, Any, List, Optional
from loguru import logger

from app.protocols.base import BaseProtocol
from app.services.vector_db import VectorDBService
from app.services.search import SearchService

class KnowledgeAccessProtocol(BaseProtocol):
    """지식 접근 프로토콜 (FR-301, FR-302)
    
    사용자 요청에 관련된 지식을 검색하고 접근합니다.
    """
    
    def __init__(self):
        super().__init__()
        self.vector_db = VectorDBService()
        self.search_service = SearchService()
        self.sources = []
    
    async def execute(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """프로토콜 실행 메서드
        
        Args:
            query: 사용자 쿼리
            context: 실행 컨텍스트
            
        Returns:
            지식 컨텍스트
        """
        return await self.retrieve_knowledge(query, context)
    
    async def retrieve_knowledge(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """지식 검색 메서드
        
        Args:
            query: 사용자 쿼리
            context: 실행 컨텍스트
            
        Returns:
            지식 컨텍스트
        """
        try:
            # 검색 시작 로그
            self.log_execution("knowledge_retrieval_start", {
                "query": query,
                "context": context
            })
            
            # 결과 초기화
            knowledge_context = {
                "relevant_info": [],
                "sources": [],
                "confidence": 0.0
            }
            
            # 벡터 검색 수행
            vector_results = await self._perform_vector_search(query, context)
            if vector_results:
                knowledge_context["relevant_info"].extend(vector_results["relevant_info"])
                knowledge_context["sources"].extend(vector_results["sources"])
                knowledge_context["confidence"] = max(knowledge_context["confidence"], vector_results["confidence"])
            
            # 외부 검색 필요 여부 확인
            if self._should_perform_external_search(knowledge_context, context):
                # 외부 검색 수행
                external_results = await self._perform_external_search(query, context)
                if external_results:
                    knowledge_context["relevant_info"].extend(external_results["relevant_info"])
                    knowledge_context["sources"].extend(external_results["sources"])
                    knowledge_context["confidence"] = max(knowledge_context["confidence"], external_results["confidence"])
            
            # 중복 제거 및 정렬
            knowledge_context["relevant_info"] = self._deduplicate_and_rank(knowledge_context["relevant_info"])
            knowledge_context["sources"] = list(set(knowledge_context["sources"]))
            
            # 소스 저장
            self.sources = knowledge_context["sources"]
            
            # 검색 완료 로그
            self.log_execution("knowledge_retrieval_complete", {
                "info_count": len(knowledge_context["relevant_info"]),
                "sources_count": len(knowledge_context["sources"]),
                "confidence": knowledge_context["confidence"]
            })
            
            return knowledge_context
            
        except Exception as e:
            logger.error(f"Knowledge retrieval failed: {str(e)}")
            self.log_execution("knowledge_retrieval_error", {"error": str(e)})
            # 오류 발생 시 빈 컨텍스트 반환
            return {"relevant_info": [], "sources": [], "confidence": 0.0}
    
    async def _perform_vector_search(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """벡터 검색 수행"""
        try:
            # 검색 파라미터 설정
            limit = context.get("vector_search_limit", 5)
            threshold = context.get("vector_search_threshold", 0.7)
            
            # 벡터 검색 실행
            results = await self.vector_db.search(query, limit=limit, threshold=threshold)
            
            if not results or len(results) == 0:
                return None
            
            # 결과 포맷팅
            relevant_info = []
            sources = []
            confidence = 0.0
            
            for result in results:
                relevant_info.append({
                    "content": result["content"],
                    "score": result["score"],
                    "source": result.get("metadata", {}).get("source", "vector_db")
                })
                
                if "metadata" in result and "source" in result["metadata"]:
                    sources.append(result["metadata"]["source"])
                
                confidence = max(confidence, result["score"])
            
            return {
                "relevant_info": relevant_info,
                "sources": sources,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return None
    
    def _should_perform_external_search(self, knowledge_context: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """외부 검색 필요 여부 확인"""
        # 항상 외부 검색 수행 옵션
        if context.get("always_search_external", False):
            return True
        
        # 벡터 검색 결과가 충분한 경우 외부 검색 생략
        if knowledge_context["confidence"] >= context.get("sufficient_confidence", 0.85):
            return False
        
        # 벡터 검색 결과가 없거나 부족한 경우 외부 검색 수행
        if len(knowledge_context["relevant_info"]) < context.get("min_relevant_info", 2):
            return True
        
        # 기본적으로 외부 검색 수행
        return True
    
    async def _perform_external_search(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """외부 검색 수행"""
        try:
            # 검색 파라미터 설정
            limit = context.get("external_search_limit", 3)
            
            # 외부 검색 실행
            results = await self.search_service.search(query, limit=limit)
            
            if not results or len(results) == 0:
                return None
            
            # 결과 포맷팅
            relevant_info = []
            sources = []
            confidence = 0.7  # 외부 검색 기본 신뢰도
            
            for result in results:
                relevant_info.append({
                    "content": result["content"],
                    "score": result.get("score", 0.7),
                    "source": result["source"]
                })
                
                sources.append(result["source"])
            
            return {
                "relevant_info": relevant_info,
                "sources": sources,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"External search failed: {str(e)}")
            return None
    
    def _deduplicate_and_rank(self, relevant_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 제거 및 정렬"""
        # 중복 제거 (내용 기준)
        unique_info = {}
        for info in relevant_info:
            content = info["content"]
            if content not in unique_info or info["score"] > unique_info[content]["score"]:
                unique_info[content] = info
        
        # 점수 기준 정렬
        sorted_info = sorted(unique_info.values(), key=lambda x: x["score"], reverse=True)
        
        return sorted_info
    
    def get_sources(self) -> List[str]:
        """검색 소스 반환"""
        return self.sources