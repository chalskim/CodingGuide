from typing import Dict, Any, List, Optional
from loguru import logger

from app.protocols.base import BaseProtocol
from app.services.llm import LLMService

class AnalyticalReasoningProtocol(BaseProtocol):
    """분석 추론 프로토콜 (FR-401)
    
    사용자 요청과 지식 컨텍스트를 분석하여 추론 결과를 생성합니다.
    """
    
    def __init__(self):
        super().__init__()
        self.llm_service = LLMService()
        self.reasoning_steps = []
    
    async def execute(self, query: str, knowledge_context: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """프로토콜 실행 메서드
        
        Args:
            query: 사용자 쿼리
            knowledge_context: 지식 컨텍스트
            context: 실행 컨텍스트
            
        Returns:
            추론 결과
        """
        return await self.analyze(query, knowledge_context, context)
    
    async def analyze(self, query: str, knowledge_context: Dict[str, Any], context: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        """분석 추론 메서드
        
        Args:
            query: 사용자 쿼리
            knowledge_context: 지식 컨텍스트
            context: 실행 컨텍스트
            
        Returns:
            추론 결과
        """
        try:
            # 분석 시작 로그
            self.log_execution("reasoning_start", {
                "query": query,
                "knowledge_info_count": len(knowledge_context.get("relevant_info", [])),
                "context": context
            })
            
            # 추론 단계 초기화
            self.reasoning_steps = []
            
            # API 키가 제공된 경우 새 LLM 서비스 인스턴스 생성
            llm_service = LLMService(api_key=api_key) if api_key else self.llm_service
            
            # 1단계: 요청 분석
            request_analysis = await self._analyze_request(query, context, llm_service)
            self.reasoning_steps.append({"step": "request_analysis", "result": request_analysis})
            
            # 2단계: 지식 평가
            knowledge_evaluation = await self._evaluate_knowledge(query, knowledge_context, context, llm_service)
            self.reasoning_steps.append({"step": "knowledge_evaluation", "result": knowledge_evaluation})
            
            # 3단계: 핵심 포인트 추출
            key_points = await self._extract_key_points(query, knowledge_context, request_analysis, context, llm_service)
            self.reasoning_steps.append({"step": "key_points_extraction", "result": key_points})
            
            # 4단계: 응답 계획 수립
            response_plan = await self._plan_response(query, key_points, request_analysis, context, llm_service)
            self.reasoning_steps.append({"step": "response_planning", "result": response_plan})
            
            # 최종 추론 결과 구성
            reasoning_result = {
                "intent": request_analysis.get("intent"),
                "domain": request_analysis.get("domain"),
                "complexity": request_analysis.get("complexity"),
                "knowledge_sufficiency": knowledge_evaluation.get("sufficiency"),
                "key_points": key_points.get("points", []),
                "suggested_format": response_plan.get("format"),
                "tone": response_plan.get("tone"),
                "structure": response_plan.get("structure")
            }
            
            # 분석 완료 로그
            self.log_execution("reasoning_complete", {
                "intent": reasoning_result["intent"],
                "key_points_count": len(reasoning_result["key_points"]),
                "suggested_format": reasoning_result["suggested_format"]
            })
            
            return reasoning_result
            
        except Exception as e:
            logger.error(f"Analytical reasoning failed: {str(e)}")
            self.log_execution("reasoning_error", {"error": str(e)})
            # 오류 발생 시 기본 추론 결과 반환
            return {
                "intent": "unknown",
                "domain": "general",
                "complexity": "medium",
                "knowledge_sufficiency": "unknown",
                "key_points": [],
                "suggested_format": "text",
                "tone": "neutral",
                "structure": "default"
            }
    
    async def _analyze_request(self, query: str, context: Dict[str, Any], llm_service: LLMService) -> Dict[str, Any]:
        """요청 분석"""
        prompt = f"""다음 사용자 요청을 분석하여 의도, 도메인, 복잡성을 파악하세요:

{query}

다음 형식으로 JSON 응답을 제공하세요:
{{
  "intent": "[정보 요청/작업 요청/의견 요청/기타]",
  "domain": "[기술/비즈니스/교육/의학/법률/일반/기타]",
  "complexity": "[낮음/중간/높음]",
  "keywords": [관련 키워드 목록]
}}"""
        
        try:
            response = await llm_service.generate_text(
                prompt=prompt,
                max_tokens=300,
                temperature=0.3,
                options={"format": "json"}
            )
            
            # JSON 파싱
            import json
            result = json.loads(response)
            return result
            
        except Exception as e:
            logger.error(f"Request analysis failed: {str(e)}")
            return {
                "intent": "unknown",
                "domain": "general",
                "complexity": "medium",
                "keywords": []
            }
    
    async def _evaluate_knowledge(self, query: str, knowledge_context: Dict[str, Any], context: Dict[str, Any], llm_service: LLMService) -> Dict[str, Any]:
        """지식 평가"""
        # 지식 컨텍스트가 비어있는 경우
        if not knowledge_context.get("relevant_info"):
            return {
                "sufficiency": "insufficient",
                "gaps": ["관련 정보 없음"],
                "reliability": "low"
            }
        
        # 지식 정보 결합
        knowledge_text = "\n\n".join(knowledge_context.get("relevant_info", []))
        
        prompt = f"""다음 사용자 요청과 관련 정보를 분석하여 지식의 충분성을 평가하세요:

사용자 요청: {query}

관련 정보:
{knowledge_text}

다음 형식으로 JSON 응답을 제공하세요:
{{
  "sufficiency": "[충분/부분적/불충분]",
  "gaps": [지식 격차 목록],
  "reliability": "[높음/중간/낮음]"
}}"""
        
        try:
            response = await llm_service.generate_text(
                prompt=prompt,
                max_tokens=300,
                temperature=0.3,
                options={"format": "json"}
            )
            
            # JSON 파싱
            import json
            result = json.loads(response)
            return result
            
        except Exception as e:
            logger.error(f"Knowledge evaluation failed: {str(e)}")
            return {
                "sufficiency": "unknown",
                "gaps": [],
                "reliability": "medium"
            }
    
    async def _extract_key_points(self, query: str, knowledge_context: Dict[str, Any], request_analysis: Dict[str, Any], context: Dict[str, Any], llm_service: LLMService) -> Dict[str, Any]:
        """핵심 포인트 추출"""
        # 지식 정보 결합
        knowledge_text = "\n\n".join(knowledge_context.get("relevant_info", []))
        
        prompt = f"""다음 사용자 요청과 관련 정보에서 핵심 포인트를 추출하세요:

사용자 요청: {query}

요청 분석:
- 의도: {request_analysis.get('intent', 'unknown')}
- 도메인: {request_analysis.get('domain', 'general')}
- 복잡성: {request_analysis.get('complexity', 'medium')}

관련 정보:
{knowledge_text}

다음 형식으로 JSON 응답을 제공하세요:
{{
  "points": [핵심 포인트 목록],
  "importance": [각 포인트의 중요도(1-5)],
  "relevance": [각 포인트의 관련성(1-5)]
}}"""
        
        try:
            response = await llm_service.generate_text(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3,
                options={"format": "json"}
            )
            
            # JSON 파싱
            import json
            result = json.loads(response)
            return result
            
        except Exception as e:
            logger.error(f"Key points extraction failed: {str(e)}")
            return {
                "points": [],
                "importance": [],
                "relevance": []
            }
    
    async def _plan_response(self, query: str, key_points: Dict[str, Any], request_analysis: Dict[str, Any], context: Dict[str, Any], llm_service: LLMService) -> Dict[str, Any]:
        """응답 계획 수립"""
        # 핵심 포인트 결합
        points_text = "\n".join([f"- {point}" for point in key_points.get("points", [])])
        
        prompt = f"""다음 사용자 요청과 핵심 포인트를 바탕으로 응답 계획을 수립하세요:

사용자 요청: {query}

요청 분석:
- 의도: {request_analysis.get('intent', 'unknown')}
- 도메인: {request_analysis.get('domain', 'general')}
- 복잡성: {request_analysis.get('complexity', 'medium')}

핵심 포인트:
{points_text}

다음 형식으로 JSON 응답을 제공하세요:
{{
  "format": "[text/markdown/json/code/table]",
  "tone": "[formal/conversational/technical/simple]",
  "structure": "[sequential/comparative/problem-solution/question-answer/other]",
  "sections": [응답 섹션 목록]
}}"""
        
        try:
            response = await llm_service.generate_text(
                prompt=prompt,
                max_tokens=400,
                temperature=0.3,
                options={"format": "json"}
            )
            
            # JSON 파싱
            import json
            result = json.loads(response)
            return result
            
        except Exception as e:
            logger.error(f"Response planning failed: {str(e)}")
            return {
                "format": "text",
                "tone": "neutral",
                "structure": "default",
                "sections": []
            }
    
    def get_steps(self) -> List[Dict[str, Any]]:
        """추론 단계 반환"""
        return self.reasoning_steps