import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from app.protocols.learning import AdaptiveLearningProtocol

@pytest.mark.asyncio
class TestAdaptiveLearningProtocol:
    """Test cases for AdaptiveLearningProtocol"""

    @pytest.fixture
    def protocol(self):
        """Fixture for AdaptiveLearningProtocol instance"""
        with patch('app.protocols.learning.DatabaseService') as mock_db_cls, \
             patch('app.protocols.learning.logger') as mock_logger:
            
            # Setup mock DB service
            mock_db = AsyncMock()
            mock_db.insert_one = AsyncMock(return_value="inserted_id")
            mock_db.find_one = AsyncMock(return_value={"feedback_id": "test_id", "rating": 4})
            mock_db.find = AsyncMock(return_value=[{"feedback_id": "test_id", "rating": 4}])
            mock_db.update_one = AsyncMock(return_value=True)
            mock_db_cls.return_value = mock_db
            
            protocol = AdaptiveLearningProtocol()
            protocol.db_service = mock_db
            
            yield protocol

    @pytest.mark.asyncio
    async def test_execute_method(self, protocol):
        """Test execute method"""
        feedback_data = {
            "feedback_id": "test_id",
            "request_id": "req123",
            "rating": 4,
            "feedback_type": "accuracy",
            "comment": "좋은 응답입니다."
        }
        
        result = await protocol.execute(feedback_data)
        
        assert result["status"] == "success"
        assert result["feedback_id"] == "test_id"
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_process_feedback(self, protocol):
        """Test feedback processing"""
        feedback_data = {
            "feedback_id": "test_id",
            "request_id": "req123",
            "rating": 4,
            "feedback_type": "accuracy",
            "comment": "좋은 응답입니다."
        }
        
        result = await protocol.process_feedback(feedback_data)
        
        assert result["status"] == "success"
        assert result["feedback_id"] == "test_id"
        assert "analysis" in result
        protocol.db_service.insert_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_store_feedback(self, protocol):
        """Test feedback storage"""
        await protocol.store_feedback(
            feedback_id="test_id",
            request_id="req123",
            session_id="sess456",
            user_id="user789",
            rating=4,
            feedback_type="accuracy",
            comment="좋은 응답입니다.",
            metadata={"source": "test"}
        )
        
        protocol.db_service.insert_one.assert_awaited_once()
        # Check that the first argument is the collection name
        args, _ = protocol.db_service.insert_one.await_args
        assert args[0] == protocol.feedback_collection
        # Check that the second argument is a dict containing the feedback data
        assert isinstance(args[1], dict)
        assert args[1]["feedback_id"] == "test_id"
        assert args[1]["request_id"] == "req123"

    @pytest.mark.asyncio
    async def test_get_feedback(self, protocol):
        """Test feedback retrieval"""
        feedback = await protocol.get_feedback("test_id")
        
        assert feedback is not None
        assert feedback["feedback_id"] == "test_id"
        protocol.db_service.find_one.assert_awaited_once_with(
            protocol.feedback_collection, {"feedback_id": "test_id"}
        )

    @pytest.mark.asyncio
    async def test_get_feedback_by_request(self, protocol):
        """Test feedback retrieval by request ID"""
        feedbacks = await protocol.get_feedback_by_request("req123")
        
        assert len(feedbacks) == 1
        assert feedbacks[0]["feedback_id"] == "test_id"
        protocol.db_service.find.assert_awaited_once_with(
            protocol.feedback_collection, {"request_id": "req123"}
        )

    @pytest.mark.asyncio
    async def test_analyze_feedback_positive(self, protocol):
        """Test feedback analysis with positive rating"""
        feedback_data = {
            "rating": 5,
            "feedback_type": "accuracy",
            "comment": "매우 정확한 응답입니다."
        }
        
        analysis = await protocol._analyze_feedback(feedback_data)
        
        assert analysis["sentiment"] == "positive"
        assert "높은 정확성" in analysis["strengths"]

    @pytest.mark.asyncio
    async def test_analyze_feedback_negative(self, protocol):
        """Test feedback analysis with negative rating"""
        feedback_data = {
            "rating": 2,
            "feedback_type": "clarity",
            "comment": "이해하기 어려움"
        }
        
        analysis = await protocol._analyze_feedback(feedback_data)
        
        assert analysis["sentiment"] == "negative"
        assert "명확성 향상 필요" in analysis["improvement_areas"]
        assert "개선 필요" in analysis["improvement_areas"]

    @pytest.mark.asyncio
    async def test_analyze_feedback_neutral(self, protocol):
        """Test feedback analysis with neutral rating"""
        feedback_data = {
            "rating": 3,
            "feedback_type": "relevance",
            "comment": "보통입니다."
        }
        
        analysis = await protocol._analyze_feedback(feedback_data)
        
        assert analysis["sentiment"] == "neutral"
        assert "관련성 향상 필요" in analysis["improvement_areas"]

    @pytest.mark.asyncio
    async def test_update_learning_metrics_new(self, protocol):
        """Test learning metrics update with new metrics"""
        # Mock find_one to return None (no existing metrics)
        protocol.db_service.find_one.return_value = None
        
        feedback_data = {"rating": 4}
        analysis_result = {
            "sentiment": "positive",
            "improvement_areas": ["개선 필요"],
            "strengths": ["높은 정확성"]
        }
        
        await protocol._update_learning_metrics(feedback_data, analysis_result)
        
        protocol.db_service.update_one.assert_awaited_once()
        # Check that the first argument is the collection name
        args, kwargs = protocol.db_service.update_one.await_args
        assert args[0] == protocol.metrics_collection
        assert kwargs.get("upsert") is True

    @pytest.mark.asyncio
    async def test_update_learning_metrics_existing(self, protocol):
        """Test learning metrics update with existing metrics"""
        # Mock find_one to return existing metrics
        existing_metrics = {
            "metric_type": "feedback_summary",
            "total_feedback_count": 10,
            "average_rating": 3.5,
            "sentiment_distribution": {
                "positive": 5,
                "neutral": 3,
                "negative": 2
            },
            "improvement_areas": {"개선 필요": 2},
            "strengths": {"높은 정확성": 5},
            "last_updated": datetime.now().isoformat()
        }
        protocol.db_service.find_one.return_value = existing_metrics
        
        feedback_data = {"rating": 4}
        analysis_result = {
            "sentiment": "positive",
            "improvement_areas": ["개선 필요"],
            "strengths": ["높은 정확성"]
        }
        
        await protocol._update_learning_metrics(feedback_data, analysis_result)
        
        protocol.db_service.update_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_learning_metrics(self, protocol):
        """Test learning metrics retrieval"""
        metrics = {
            "metric_type": "feedback_summary",
            "total_feedback_count": 10,
            "average_rating": 3.5
        }
        protocol.db_service.find_one.return_value = metrics
        
        result = await protocol.get_learning_metrics()
        
        assert result == metrics
        protocol.db_service.find_one.assert_awaited_once_with(
            protocol.metrics_collection, {"metric_type": "feedback_summary"}
        )

    @pytest.mark.asyncio
    async def test_get_learning_metrics_empty(self, protocol):
        """Test learning metrics retrieval with no existing metrics"""
        protocol.db_service.find_one.return_value = None
        
        result = await protocol.get_learning_metrics()
        
        assert result["total_feedback_count"] == 0
        assert result["average_rating"] == 0
        assert "sentiment_distribution" in result

    @pytest.mark.asyncio
    async def test_process_feedback_with_error(self, protocol):
        """Test feedback processing with error"""
        feedback_data = {"feedback_id": "test_id"}
        
        # Simulate error in store_feedback
        protocol.db_service.insert_one.side_effect = Exception("Database error")
        
        result = await protocol.process_feedback(feedback_data)
        
        assert result["status"] == "error"
        assert "Database error" in result["error"]