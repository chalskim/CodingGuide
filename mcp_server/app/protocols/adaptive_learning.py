from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime

from app.protocols.base import BaseProtocol
from app.services.llm import LLMService
from app.core.config import settings

class AdaptiveLearningProtocol(BaseProtocol):
    """적응형 학습 프로토콜 (FR-601, FR-602)
    
    사용자 피드백을 수집하고 분석하여 시스템의 응답을 개선합니다.
    """
    
    def __init__(self):
        super().__init__()
        self.llm_service = LLMService()
        self.feedback_history = []
        self.improvement_suggestions = []
    
    async def execute(self, feedback: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """프로토콜 실행 메서드
        
        Args:
            feedback: 사용자 피드백 데이터
            context: 실행 컨텍스트
            
        Returns:
            처리 결과
        """
        return await self.process_feedback(feedback, context)
    
    async def process_feedback(self, feedback: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """피드백 처리 메서드
        
        Args:
            feedback: 사용자 피드백 데이터
            context: 실행 컨텍스트
            
        Returns:
            처리 결과
        """
        try:
            # 피드백 처리 시작 로그
            self.log_execution("feedback_processing_start", {
                "feedback_id": feedback.get("id"),
                "feedback_type": feedback.get("type"),
                "rating": feedback.get("rating")
            })
            
            # 피드백 유효성 검사
            validated_feedback = self._validate_feedback(feedback)
            
            # 피드백 저장
            self._store_feedback(validated_feedback)
            
            # 피드백 분석
            analysis_result = await self._analyze_feedback(validated_feedback, context)
            
            # 개선 제안 생성
            if feedback.get("rating", 5) < 4:  # 낮은 평가에 대해서만 개선 제안 생성
                improvement = await self._generate_improvement_suggestion(validated_feedback, analysis_result, context)
                self.improvement_suggestions.append(improvement)
            
            # 처리 결과 구성
            result = {
                "feedback_id": validated_feedback.get("id"),
                "status": "processed",
                "timestamp": self._get_timestamp(),
                "analysis": analysis_result
            }
            
            # 피드백 처리 완료 로그
            self.log_execution("feedback_processing_complete", {
                "feedback_id": validated_feedback.get("id"),
                "analysis_summary": analysis_result.get("summary")
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Feedback processing failed: {str(e)}")
            self.log_execution("feedback_processing_error", {"error": str(e)})
            raise
    
    def _validate_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """피드백 유효성 검사"""
        validated = {}
        
        # 필수 필드 확인
        validated["id"] = feedback.get("id", f"feedback_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        validated["type"] = feedback.get("type", "general")
        validated["content"] = feedback.get("content", "")
        validated["rating"] = min(max(feedback.get("rating", 5), 1), 5)  # 1-5 범위로 제한
        
        # 선택적 필드 복사
        if "request_id" in feedback:
            validated["request_id"] = feedback["request_id"]
        if "user_id" in feedback:
            validated["user_id"] = feedback["user_id"]
        if "tags" in feedback:
            validated["tags"] = feedback["tags"]
        if "metadata" in feedback:
            validated["metadata"] = feedback["metadata"]
        
        # 타임스탬프 추가
        validated["timestamp"] = feedback.get("timestamp", self._get_timestamp())
        
        return validated
    
    def _store_feedback(self, feedback: Dict[str, Any]) -> None:
        """피드백 저장"""
        self.feedback_history.append(feedback)
        
        # 메타데이터 업데이트
        self.set_metadata("last_feedback", {
            "id": feedback["id"],
            "timestamp": feedback["timestamp"],
            "rating": feedback["rating"]
        })
        
        # 평균 평점 업데이트
        ratings = [f.get("rating", 0) for f in self.feedback_history if "rating" in f]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        self.set_metadata("average_rating", avg_rating)
    
    async def _analyze_feedback(self, feedback: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """피드백 분석"""
        # 피드백 유형에 따른 분석
        if feedback["type"] == "rating_only":
            return self._analyze_rating(feedback)
        elif feedback["type"] == "text_feedback":
            return await self._analyze_text_feedback(feedback, context)
        else:  # 일반 피드백
            return await self._analyze_general_feedback(feedback, context)
    
    def _analyze_rating(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """평점 분석"""
        rating = feedback["rating"]
        
        if rating >= 4:
            sentiment = "positive"
            summary = "사용자가 응답에 만족했습니다."
        elif rating >= 3:
            sentiment = "neutral"
            summary = "사용자가 응답에 보통 수준으로 만족했습니다."
        else:
            sentiment = "negative"
            summary = "사용자가 응답에 불만족했습니다."
        
        return {
            "sentiment": sentiment,
            "summary": summary,
            "confidence": 0.9,  # 평점은 명시적이므로 높은 신뢰도
            "aspects": {}
        }
    
    async def _analyze_text_feedback(self, feedback: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """텍스트 피드백 분석"""
        content = feedback.get("content", "")
        
        if not content:
            return {
                "sentiment": "unknown",
                "summary": "텍스트 피드백이 없습니다.",
                "confidence": 0.5,
                "aspects": {}
            }
        
        # LLM을 사용한 피드백 분석
        analysis_prompt = f"""다음 사용자 피드백을 분석하고 감정(positive/neutral/negative), 요약, 신뢰도(0.0-1.0), 
        그리고 언급된 측면(정확성, 유용성, 명확성, 속도 등)을 JSON 형식으로 반환하세요.
        
        피드백: {content}
        """
        
        try:
            analysis_result = await self.llm_service.generate_text(
                prompt=analysis_prompt,
                max_tokens=500,
                temperature=0.3,
                options={"format": "json"}
            )
            
            # JSON 파싱 시도
            import json
            try:
                parsed_result = json.loads(analysis_result)
                return {
                    "sentiment": parsed_result.get("sentiment", "unknown"),
                    "summary": parsed_result.get("summary", "분석 불가"),
                    "confidence": parsed_result.get("confidence", 0.5),
                    "aspects": parsed_result.get("aspects", {})
                }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM analysis result as JSON: {analysis_result}")
                # 기본 분석 결과 반환
                return {
                    "sentiment": "unknown",
                    "summary": "피드백 분석 중 오류가 발생했습니다.",
                    "confidence": 0.3,
                    "aspects": {}
                }
                
        except Exception as e:
            logger.error(f"Text feedback analysis failed: {str(e)}")
            return {
                "sentiment": "unknown",
                "summary": "피드백 분석 중 오류가 발생했습니다.",
                "confidence": 0.3,
                "aspects": {}
            }
    
    async def _analyze_general_feedback(self, feedback: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """일반 피드백 분석"""
        # 평점과 텍스트 모두 고려
        rating_analysis = self._analyze_rating(feedback)
        
        if feedback.get("content"):
            text_analysis = await self._analyze_text_feedback(feedback, context)
            
            # 두 분석 결과 통합
            combined_analysis = {
                "sentiment": text_analysis.get("sentiment", rating_analysis["sentiment"]),
                "summary": text_analysis.get("summary", rating_analysis["summary"]),
                "confidence": (rating_analysis["confidence"] + text_analysis.get("confidence", 0.5)) / 2,
                "aspects": text_analysis.get("aspects", {})
            }
            return combined_analysis
        else:
            return rating_analysis
    
    async def _generate_improvement_suggestion(self, feedback: Dict[str, Any], analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """개선 제안 생성"""
        # 피드백 및 분석 결과를 기반으로 개선 제안 생성
        suggestion_prompt = f"""다음 사용자 피드백과 분석 결과를 바탕으로 시스템 응답 개선을 위한 구체적인 제안을 생성하세요.
        
        피드백: {feedback.get('content', '(내용 없음)')}
        평점: {feedback.get('rating', '없음')}/5
        분석 요약: {analysis.get('summary', '분석 없음')}
        감정: {analysis.get('sentiment', '알 수 없음')}
        언급된 측면: {', '.join(analysis.get('aspects', {}).keys()) if analysis.get('aspects') else '없음'}
        
        개선 제안을 JSON 형식으로 반환하세요. 다음 필드를 포함해야 합니다:
        - area: 개선 영역 (예: 정확성, 명확성, 속도 등)
        - suggestion: 구체적인 개선 제안
        - priority: 우선순위 (high, medium, low)
        """
        
        try:
            suggestion_result = await self.llm_service.generate_text(
                prompt=suggestion_prompt,
                max_tokens=500,
                temperature=0.3,
                options={"format": "json"}
            )
            
            # JSON 파싱 시도
            import json
            try:
                parsed_suggestion = json.loads(suggestion_result)
                suggestion = {
                    "id": f"suggestion_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "feedback_id": feedback["id"],
                    "area": parsed_suggestion.get("area", "general"),
                    "suggestion": parsed_suggestion.get("suggestion", "개선 제안을 생성할 수 없습니다."),
                    "priority": parsed_suggestion.get("priority", "medium"),
                    "timestamp": self._get_timestamp(),
                    "implemented": False
                }
                return suggestion
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM suggestion result as JSON: {suggestion_result}")
                # 기본 제안 반환
                return {
                    "id": f"suggestion_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "feedback_id": feedback["id"],
                    "area": "general",
                    "suggestion": "사용자 피드백을 기반으로 응답의 품질을 개선하세요.",
                    "priority": "medium",
                    "timestamp": self._get_timestamp(),
                    "implemented": False
                }
                
        except Exception as e:
            logger.error(f"Improvement suggestion generation failed: {str(e)}")
            return {
                "id": f"suggestion_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "feedback_id": feedback["id"],
                "area": "general",
                "suggestion": "개선 제안을 생성하는 중 오류가 발생했습니다.",
                "priority": "low",
                "timestamp": self._get_timestamp(),
                "implemented": False
            }
    
    def get_feedback_history(self) -> List[Dict[str, Any]]:
        """피드백 이력 반환"""
        return self.feedback_history
    
    def get_improvement_suggestions(self, implemented_only: bool = False) -> List[Dict[str, Any]]:
        """개선 제안 목록 반환"""
        if implemented_only:
            return [s for s in self.improvement_suggestions if s.get("implemented", False)]
        return self.improvement_suggestions
        
    async def store_interaction(self, interaction_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """사용자 상호작용 저장 메서드
        
        Args:
            interaction_data: 상호작용 데이터
            context: 상호작용 컨텍스트 (선택적)
            
        Returns:
            저장된 상호작용 데이터
        """
        try:
            # 상호작용 데이터 구성
            interaction = {
                **interaction_data,
                "created_at": datetime.now()
            }
            
            # 컨텍스트가 제공된 경우 추가
            if context:
                interaction["context"] = context
            
            # 메모리에 저장
            if not hasattr(self, "interactions"):
                self.interactions = []
            self.interactions.append(interaction)
            
            # 저장 성공 로그
            self.log_execution("interaction_stored", {"interaction_id": interaction.get("interaction_id")})
            
            return interaction
        except Exception as e:
            # 저장 실패 로그
            self.log_execution("interaction_store_error", {"error": str(e)})
            logger.error(f"Interaction storage failed: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    def mark_suggestion_implemented(self, suggestion_id: str) -> bool:
        """개선 제안 구현 표시"""
        for suggestion in self.improvement_suggestions:
            if suggestion.get("id") == suggestion_id:
                suggestion["implemented"] = True
                suggestion["implementation_date"] = self._get_timestamp()
                return True
        return False
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """학습 인사이트 생성"""
        # 피드백 데이터 요약
        total_feedback = len(self.feedback_history)
        if total_feedback == 0:
            return {
                "total_feedback": 0,
                "average_rating": 0,
                "sentiment_distribution": {},
                "common_issues": [],
                "improvement_areas": [],
                "timestamp": self._get_timestamp()
            }
        
        # 평점 분석
        ratings = [f.get("rating", 0) for f in self.feedback_history if "rating" in f]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # 감정 분포 분석
        sentiments = []
        for feedback in self.feedback_history:
            if "analysis" in feedback and "sentiment" in feedback["analysis"]:
                sentiments.append(feedback["analysis"]["sentiment"])
        
        sentiment_distribution = {}
        for sentiment in sentiments:
            sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
        
        # 개선 영역 분석
        improvement_areas = {}
        for suggestion in self.improvement_suggestions:
            area = suggestion.get("area", "general")
            improvement_areas[area] = improvement_areas.get(area, 0) + 1
        
        # 상위 개선 영역 추출
        top_areas = sorted(improvement_areas.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_feedback": total_feedback,
            "average_rating": avg_rating,
            "sentiment_distribution": sentiment_distribution,
            "common_issues": self._extract_common_issues(),
            "improvement_areas": [area for area, count in top_areas],
            "timestamp": self._get_timestamp()
        }
    
    def _extract_common_issues(self) -> List[str]:
        """공통 이슈 추출"""
        # 부정적 피드백에서 공통 이슈 추출
        negative_feedback = []
        for feedback in self.feedback_history:
            if feedback.get("rating", 5) <= 3 or \
               ("analysis" in feedback and feedback["analysis"].get("sentiment") == "negative"):
                negative_feedback.append(feedback)
        
        # 이슈 카운팅
        issues = {}
        for feedback in negative_feedback:
            if "analysis" in feedback and "aspects" in feedback["analysis"]:
                for aspect, details in feedback["analysis"]["aspects"].items():
                    if isinstance(details, dict) and "issue" in details:
                        issue = details["issue"]
                        issues[issue] = issues.get(issue, 0) + 1
        
        # 상위 이슈 추출
        top_issues = sorted(issues.items(), key=lambda x: x[1], reverse=True)[:5]
        return [issue for issue, count in top_issues]