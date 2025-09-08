import pytest
import sys
from unittest.mock import MagicMock, patch, AsyncMock

# Settings 클래스를 모킹하여 테스트 환경 설정
class MockSettings:
    ENVIRONMENT = "test"
    DEBUG = True
    LOG_LEVEL = "debug"
    SECRET_KEY = "test-secret-key"
    API_PREFIX = "/api/v1"
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8080"]
    DATABASE_URL = "sqlite:///./test.db"
    OPENAI_API_KEY = "sk-test"
    ANTHROPIC_API_KEY = "test-key"
    GOOGLE_API_KEY = "test-key"
    VECTOR_DB_PATH = "./data/test_vector_db"
    GOOGLE_SEARCH_API_KEY = "test-key"
    GOOGLE_SEARCH_ENGINE_ID = "test-id"

# app.core.config 모듈을 모킹
sys.modules["app.core.config"] = MagicMock()
sys.modules["app.core.config"].settings = MockSettings()

# 필요한 서비스 모킹
sys.modules["app.services.llm"] = MagicMock()
sys.modules["app.services.llm"].LLMService = MagicMock()

# 이제 AdaptiveLearningProtocol을 임포트
from app.protocols.adaptive_learning import AdaptiveLearningProtocol

class TestAdaptiveLearningProtocol:
    """Test cases for AdaptiveLearningProtocol"""

    @pytest.fixture
    def protocol(self):
        """Fixture for AdaptiveLearningProtocol instance"""
        with patch('app.protocols.adaptive_learning.LLMService') as mock_llm_cls, \
             patch('app.protocols.adaptive_learning.logger'):
            
            # Setup mock LLM service
            mock_llm = AsyncMock()
            mock_llm.generate_text.return_value = "Analysis result"
            mock_llm_cls.return_value = mock_llm
            
            protocol = AdaptiveLearningProtocol()
            protocol.llm_service = mock_llm
            
            yield protocol

    @pytest.mark.asyncio
    async def test_execute_method(self, protocol):
        """Test execute method"""
        feedback = {"rating": 4, "content": "Good response"}
        context = {"request_id": "req123", "response_id": "res456"}
        
        result = await protocol.execute(feedback, context)
        
        assert "feedback_id" in result
        assert "status" in result
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_process_feedback(self, protocol):
        """Test feedback processing"""
        feedback = {"rating": 4, "content": "Good response"}
        context = {"request_id": "req123", "response_id": "res456"}
        
        result = await protocol.process_feedback(feedback, context)
        
        assert "feedback_id" in result
        assert "status" in result
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_analyze_feedback(self, protocol):
        """Test feedback analysis"""
        feedback = {"rating": 2, "content": "Could be better", "type": "text_feedback"}
        context = {"request_id": "req123", "response_id": "res456"}
        
        result = await protocol._analyze_feedback(feedback, context)
        
        assert result is not None
        assert "sentiment" in result
        assert "summary" in result
        assert "confidence" in result
        assert "aspects" in result
        protocol.llm_service.generate_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_improvements(self, protocol):
        """Test improvements generation"""
        feedback = {"id": "feedback_123", "rating": 2, "content": "Could be better"}
        context = {"request_id": "req123", "response_id": "res456"}
        analysis = {
            "sentiment": "negative",
            "summary": "사용자가 응답에 불만족했습니다.",
            "confidence": 0.8,
            "aspects": {"clarity": {"score": 2}, "accuracy": {"score": 3}}
        }
        
        result = await protocol._generate_improvement_suggestion(feedback, analysis, context)
        
        assert result is not None
        assert "id" in result
        assert "feedback_id" in result
        assert "suggestion" in result
        assert "area" in result
        assert "priority" in result
        protocol.llm_service.generate_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_provide_learning_insights(self, protocol):
        """Test learning insights provision"""
        # 피드백 데이터 추가
        protocol.feedback_history = [
            {"id": "f1", "rating": 4, "content": "Good response", "timestamp": "2023-01-01T12:00:00Z"},
            {"id": "f2", "rating": 2, "content": "Not helpful", "timestamp": "2023-01-02T12:00:00Z"},
            {"analysis": {"sentiment": "positive"}}
        ]
        
        result = await protocol.get_learning_insights()
        
        assert "total_feedback" in result
        assert "average_rating" in result
        assert "sentiment_distribution" in result
        assert "improvement_areas" in result

    def test_store_feedback(self, protocol):
        """Test feedback storage"""
        feedback = {"id": "f1", "rating": 4, "content": "Good response", "timestamp": "2023-01-01T12:00:00Z"}
        
        protocol._store_feedback(feedback)
        
        assert len(protocol.feedback_history) == 1
        assert protocol.feedback_history[0] == feedback
        assert "last_feedback" in protocol.metadata

    @pytest.mark.asyncio
    async def test_process_with_error(self, protocol):
        """Test processing with error"""
        feedback = {"rating": 3, "content": "Could be better", "type": "text_feedback"}
        context = {"request_id": "req123", "response_id": "res456"}
        
        # Simulate error in LLM service
        protocol.llm_service.generate_text.side_effect = Exception("LLM service error")
        
        # 예외가 발생하지 않고 오류 처리가 되는지 확인
        result = await protocol.process_feedback(feedback, context)
        
        assert result["status"] == "processed"
        assert "analysis" in result
        assert result["analysis"]["sentiment"] == "unknown"

    def test_get_feedback_history(self, protocol):
        """Test feedback history retrieval"""
        # 피드백 데이터 추가
        protocol.feedback_history = [
            {"id": "f1", "rating": 4, "content": "Good response"},
            {"id": "f2", "rating": 2, "content": "Not helpful"}
        ]
        
        result = protocol.get_feedback_history()
        
        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_analyze_text_feedback(self, protocol):
        """Test text feedback analysis"""
        feedback = {"content": "The response was helpful but could include more examples"}
        context = {}
        
        result = await protocol._analyze_text_feedback(feedback, context)
        
        assert result is not None
        assert "sentiment" in result
        assert "summary" in result
        assert "confidence" in result
        assert "aspects" in result
        protocol.llm_service.generate_text.assert_awaited_once()