from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime

from app.protocols.base import BaseProtocol
from app.services.database import DatabaseService

class AdaptiveLearningProtocol(BaseProtocol):
    """적응형 학습 프로토콜 (FR-601, FR-602)
    
    사용자 피드백을 수집하고 분석하여 시스템 성능을 개선합니다.
    """
    
    def __init__(self):
        super().__init__()
        self.db_service = DatabaseService()
        self.feedback_collection = "feedback"
        self.metrics_collection = "learning_metrics"
        self.context_collection = "conversation_context"
    
    async def manage_context(self, messages: List[Any], session_id: str) -> Dict[str, Any]:
        """대화 맥락 관리 메서드
        
        Args:
            messages: 대화 메시지 목록
            session_id: 세션 ID
            
        Returns:
            대화 맥락 정보
        """
        try:
            # 기존 맥락 조회
            context = await self.db_service.find_one(self.context_collection, {"session_id": session_id})
            
            # 맥락이 없으면 새로 생성
            if not context:
                context = {
                    "session_id": session_id,
                    "messages": [],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            
            # 메시지 추가 및 맥락 업데이트
            context["messages"] = [msg.dict() for msg in messages]
            context["updated_at"] = datetime.now()
            
            # 맥락 저장
            await self.db_service.upsert(self.context_collection, {"session_id": session_id}, context)
            
            return context
        except Exception as e:
            logger.error(f"Context management failed: {str(e)}")
            # 오류 발생 시 기본 맥락 반환
            return {
                "session_id": session_id,
                "messages": [msg.dict() for msg in messages],
                "error": str(e)
            }
    
    async def execute(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """프로토콜 실행 메서드
        
        Args:
            feedback_data: 피드백 데이터
            
        Returns:
            처리 결과
        """
        return await self.process_feedback(feedback_data)
    
    async def process_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """피드백 처리 메서드
        
        Args:
            feedback_data: 피드백 데이터
            
        Returns:
            처리 결과
        """
        try:
            # 피드백 처리 시작 로그
            self.log_execution("feedback_processing_start", {
                "feedback_id": feedback_data.get("feedback_id"),
                "request_id": feedback_data.get("request_id")
            })
            
            # 피드백 저장
            await self.store_feedback(
                feedback_id=feedback_data.get("feedback_id"),
                request_id=feedback_data.get("request_id"),
                session_id=feedback_data.get("session_id"),
                user_id=feedback_data.get("user_id"),
                rating=feedback_data.get("rating"),
                feedback_type=feedback_data.get("feedback_type"),
                comment=feedback_data.get("comment"),
                metadata=feedback_data.get("metadata")
            )
            
            # 피드백 분석
            analysis_result = await self._analyze_feedback(feedback_data)
            
            # 학습 지표 업데이트
            await self._update_learning_metrics(feedback_data, analysis_result)
            
            # 피드백 처리 완료 로그
            self.log_execution("feedback_processing_complete", {
                "feedback_id": feedback_data.get("feedback_id"),
                "analysis": analysis_result
            })
            
            return {
                "status": "success",
                "feedback_id": feedback_data.get("feedback_id"),
                "analysis": analysis_result
            }
            
        except Exception as e:
            logger.error(f"Feedback processing failed: {str(e)}")
            self.log_execution("feedback_processing_error", {"error": str(e)})
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def store_feedback(self, 
                           feedback_id: str, 
                           request_id: str, 
                           session_id: Optional[str] = None,
                           user_id: Optional[str] = None,
                           rating: Optional[int] = None,
                           feedback_type: Optional[str] = None,
                           comment: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> None:
        """피드백 저장"""
        try:
            # 피드백 데이터 구성
            feedback_data = {
                "feedback_id": feedback_id,
                "request_id": request_id,
                "session_id": session_id,
                "user_id": user_id,
                "rating": rating,
                "feedback_type": feedback_type,
                "comment": comment,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }
            
            # 데이터베이스에 저장
            await self.db_service.insert_data(self.feedback_collection, feedback_data)
            logger.info(f"Feedback stored: {feedback_id}")
            
        except Exception as e:
            logger.error(f"Failed to store feedback: {str(e)}")
            raise
            
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
            
            # 데이터베이스에 저장
            collection_name = "user_interactions"
            await self.db_service.insert_data(collection_name, interaction)
            
            # 저장 성공 로그
            self.log_execution("interaction_stored", {"interaction_id": interaction.get("interaction_id")})
            
            return interaction
        except Exception as e:
            # 저장 실패 로그
            self.log_execution("interaction_store_error", {"error": str(e)})
            logger.error(f"Interaction storage failed: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    async def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """피드백 조회"""
        try:
            # 데이터베이스에서 조회
            feedback = await self.db_service.find_one(self.feedback_collection, {"feedback_id": feedback_id})
            return feedback
            
        except Exception as e:
            logger.error(f"Failed to get feedback: {str(e)}")
            return None
    
    async def get_feedback_by_request(self, request_id: str) -> List[Dict[str, Any]]:
        """요청별 피드백 조회"""
        try:
            # 데이터베이스에서 조회
            feedbacks = await self.db_service.find(self.feedback_collection, {"request_id": request_id})
            return feedbacks
            
        except Exception as e:
            logger.error(f"Failed to get feedback by request: {str(e)}")
            return []
    
    async def _analyze_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """피드백 분석"""
        try:
            analysis = {
                "sentiment": "neutral",
                "improvement_areas": [],
                "strengths": []
            }
            
            # 평점 기반 감성 분석
            rating = feedback_data.get("rating", 0)
            if rating >= 4:
                analysis["sentiment"] = "positive"
            elif rating <= 2:
                analysis["sentiment"] = "negative"
            
            # 피드백 유형 분석
            feedback_type = feedback_data.get("feedback_type", "")
            if feedback_type == "accuracy":
                if rating <= 3:
                    analysis["improvement_areas"].append("정확성 향상 필요")
                else:
                    analysis["strengths"].append("높은 정확성")
            elif feedback_type == "relevance":
                if rating <= 3:
                    analysis["improvement_areas"].append("관련성 향상 필요")
                else:
                    analysis["strengths"].append("높은 관련성")
            elif feedback_type == "clarity":
                if rating <= 3:
                    analysis["improvement_areas"].append("명확성 향상 필요")
                else:
                    analysis["strengths"].append("높은 명확성")
            elif feedback_type == "completeness":
                if rating <= 3:
                    analysis["improvement_areas"].append("완전성 향상 필요")
                else:
                    analysis["strengths"].append("높은 완전성")
            
            # 코멘트 분석 (간단한 키워드 기반 분석)
            comment = feedback_data.get("comment", "")
            if comment:
                # 부정적 키워드 확인
                negative_keywords = ["오류", "잘못", "부정확", "이해하기 어려움", "불완전", "관련 없음"]
                for keyword in negative_keywords:
                    if keyword in comment and "개선 필요" not in analysis["improvement_areas"]:
                        analysis["improvement_areas"].append("개선 필요")
                        break
                
                # 긍정적 키워드 확인
                positive_keywords = ["좋음", "정확", "명확", "유용", "도움", "완벽"]
                for keyword in positive_keywords:
                    if keyword in comment and "전반적으로 만족" not in analysis["strengths"]:
                        analysis["strengths"].append("전반적으로 만족")
                        break
            
            return analysis
            
        except Exception as e:
            logger.error(f"Feedback analysis failed: {str(e)}")
            return {
                "sentiment": "neutral",
                "improvement_areas": [],
                "strengths": []
            }
    
    async def _update_learning_metrics(self, feedback_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> None:
        """학습 지표 업데이트"""
        try:
            # 현재 지표 조회
            metrics = await self.db_service.find_one(self.metrics_collection, {"metric_type": "feedback_summary"})
            
            if not metrics:
                # 지표가 없는 경우 초기화
                metrics = {
                    "metric_type": "feedback_summary",
                    "total_feedback_count": 0,
                    "average_rating": 0,
                    "sentiment_distribution": {
                        "positive": 0,
                        "neutral": 0,
                        "negative": 0
                    },
                    "improvement_areas": {},
                    "strengths": {},
                    "last_updated": datetime.now().isoformat()
                }
            
            # 지표 업데이트
            metrics["total_feedback_count"] += 1
            
            # 평균 평점 업데이트
            current_total = metrics["average_rating"] * (metrics["total_feedback_count"] - 1)
            new_total = current_total + feedback_data.get("rating", 0)
            metrics["average_rating"] = new_total / metrics["total_feedback_count"]
            
            # 감성 분포 업데이트
            sentiment = analysis_result.get("sentiment", "neutral")
            metrics["sentiment_distribution"][sentiment] += 1
            
            # 개선 영역 업데이트
            for area in analysis_result.get("improvement_areas", []):
                if area in metrics["improvement_areas"]:
                    metrics["improvement_areas"][area] += 1
                else:
                    metrics["improvement_areas"][area] = 1
            
            # 강점 업데이트
            for strength in analysis_result.get("strengths", []):
                if strength in metrics["strengths"]:
                    metrics["strengths"][strength] += 1
                else:
                    metrics["strengths"][strength] = 1
            
            # 마지막 업데이트 시간
            metrics["last_updated"] = datetime.now().isoformat()
            
            # 데이터베이스에 저장
            await self.db_service.update_one(
                self.metrics_collection,
                {"metric_type": "feedback_summary"},
                {"$set": metrics},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Failed to update learning metrics: {str(e)}")
    
    async def get_learning_metrics(self) -> Dict[str, Any]:
        """학습 지표 조회"""
        try:
            # 데이터베이스에서 조회
            metrics = await self.db_service.find_one(self.metrics_collection, {"metric_type": "feedback_summary"})
            return metrics or {
                "metric_type": "feedback_summary",
                "total_feedback_count": 0,
                "average_rating": 0,
                "sentiment_distribution": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                },
                "improvement_areas": {},
                "strengths": {},
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get learning metrics: {str(e)}")
            return {
                "error": str(e)
            }