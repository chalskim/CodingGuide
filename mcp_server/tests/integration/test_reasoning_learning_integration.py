import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.protocols.reasoning import AnalyticalReasoningProtocol
from app.protocols.learning import AdaptiveLearningProtocol

@pytest.mark.asyncio
class TestReasoningLearningIntegration:
    """Test the integration between AnalyticalReasoningProtocol and AdaptiveLearningProtocol"""

    @pytest.fixture
    def reasoning_protocol(self):
        """Fixture for AnalyticalReasoningProtocol instance"""
        with patch('app.protocols.reasoning.LLMService') as mock_llm_cls, \
             patch('app.protocols.reasoning.logger') as mock_logger:
            
            # Setup mock LLM service
            mock_llm = AsyncMock()
            mock_llm.generate_text.return_value = "Reasoning analysis result"
            mock_llm_cls.return_value = mock_llm
            
            protocol = AnalyticalReasoningProtocol()
            protocol.llm_service = mock_llm
            
            yield protocol

    @pytest.fixture
    def learning_protocol(self):
        """Fixture for AdaptiveLearningProtocol instance"""
        with patch('app.protocols.learning.DatabaseService') as mock_db_cls, \
             patch('app.protocols.learning.logger') as mock_logger:
            
            # Setup mock DB service
            mock_db = AsyncMock()
            mock_db.insert_one = AsyncMock(return_value="inserted_id")
            mock_db.find_one = AsyncMock(return_value={"feedback_id": "test_id", "rating": 4})
            mock_db.update_one = AsyncMock(return_value=True)
            mock_db_cls.return_value = mock_db
            
            protocol = AdaptiveLearningProtocol()
            protocol.db_service = mock_db
            
            yield protocol

    @pytest.mark.asyncio
    async def test_reasoning_to_learning_flow(self, reasoning_protocol, learning_protocol):
        """Test the flow from reasoning to learning feedback"""
        # Step 1: Perform reasoning
        request = "Analyze this information"
        knowledge_context = [
            {"content": "Information piece 1", "source": "source1"},
            {"content": "Information piece 2", "source": "source2"}
        ]
        reasoning_context = {"request_id": "req123"}
        
        reasoning_result = await reasoning_protocol.execute(request, {
            "knowledge_context": knowledge_context,
            **reasoning_context
        })
        
        assert "analysis" in reasoning_result
        assert "key_points" in reasoning_result
        assert "response_plan" in reasoning_result
        
        # Step 2: Provide feedback on reasoning result
        feedback_data = {
            "feedback_id": "feedback123",
            "request_id": "req123",
            "rating": 4,
            "feedback_type": "accuracy",
            "comment": "Good analysis",
            "metadata": {
                "reasoning_result_id": reasoning_result.get("result_id", "unknown")
            }
        }
        
        learning_result = await learning_protocol.execute(feedback_data)
        
        assert learning_result["status"] == "success"
        assert learning_result["feedback_id"] == "feedback123"
        assert "analysis" in learning_result
        
        # Verify the feedback was stored with reference to the reasoning result
        learning_protocol.db_service.insert_one.assert_awaited_once()
        args, _ = learning_protocol.db_service.insert_one.await_args
        assert args[0] == learning_protocol.feedback_collection
        assert "reasoning_result_id" in args[1]["metadata"]

    @pytest.mark.asyncio
    async def test_reasoning_to_learning_with_negative_feedback(self, reasoning_protocol, learning_protocol):
        """Test the flow with negative feedback on reasoning"""
        # Step 1: Perform reasoning
        request = "Analyze this information"
        knowledge_context = [
            {"content": "Information piece 1", "source": "source1"}
        ]
        reasoning_context = {"request_id": "req456"}
        
        reasoning_result = await reasoning_protocol.execute(request, {
            "knowledge_context": knowledge_context,
            **reasoning_context
        })
        
        # Step 2: Provide negative feedback
        feedback_data = {
            "feedback_id": "feedback456",
            "request_id": "req456",
            "rating": 2,  # Negative rating
            "feedback_type": "accuracy",
            "comment": "Analysis missed key points",
            "metadata": {
                "reasoning_result_id": reasoning_result.get("result_id", "unknown")
            }
        }
        
        learning_result = await learning_protocol.execute(feedback_data)
        
        assert learning_result["status"] == "success"
        assert "analysis" in learning_result
        
        # Check that the analysis detected negative sentiment
        assert learning_result["analysis"].get("sentiment") == "negative"
        assert "improvement_areas" in learning_result["analysis"]

    @pytest.mark.asyncio
    async def test_reasoning_error_handling_in_learning(self, reasoning_protocol, learning_protocol):
        """Test handling reasoning errors in the learning protocol"""
        # Step 1: Simulate error in reasoning
        reasoning_protocol.llm_service.generate_text.side_effect = Exception("LLM service error")
        
        request = "Analyze this information"
        knowledge_context = [{"content": "Information", "source": "source"}]
        reasoning_context = {"request_id": "req789"}
        
        reasoning_result = await reasoning_protocol.execute(request, {
            "knowledge_context": knowledge_context,
            **reasoning_context
        })
        
        assert "error" in reasoning_result
        
        # Step 2: Process feedback about the error
        feedback_data = {
            "feedback_id": "feedback789",
            "request_id": "req789",
            "rating": 1,  # Very negative
            "feedback_type": "error",
            "comment": "System error occurred",
            "metadata": {
                "error": reasoning_result.get("error"),
                "reasoning_result_id": "error"
            }
        }
        
        learning_result = await learning_protocol.execute(feedback_data)
        
        assert learning_result["status"] == "success"
        assert learning_result["analysis"].get("sentiment") == "negative"
        
        # Verify error feedback was stored
        learning_protocol.db_service.insert_one.assert_awaited_once()
        args, _ = learning_protocol.db_service.insert_one.await_args
        assert "error" in args[1]["metadata"]