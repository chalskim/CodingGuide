import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.protocols.reasoning import AnalyticalReasoningProtocol

@pytest.mark.asyncio
class TestAnalyticalReasoningProtocol:
    """Test cases for AnalyticalReasoningProtocol"""

    @pytest.fixture
    def protocol(self):
        """Fixture for AnalyticalReasoningProtocol instance"""
        with patch('app.protocols.reasoning.LLMService') as mock_llm_cls, \
             patch('app.protocols.reasoning.logger') as mock_logger:
            
            # Setup mock LLM service
            mock_llm = AsyncMock()
            mock_llm.generate_text.return_value = "Reasoning result"
            mock_llm_cls.return_value = mock_llm
            
            protocol = AnalyticalReasoningProtocol()
            protocol.llm_service = mock_llm
            
            yield protocol

    @pytest.mark.asyncio
    async def test_execute_method(self, protocol):
        """Test execute method"""
        query = "Analyze this problem"
        context = {"knowledge_context": {"relevant_info": ["Info 1", "Info 2"]}}
        
        result = await protocol.execute(query, context)
        
        assert "analysis" in result
        assert "key_points" in result
        assert "response_plan" in result

    @pytest.mark.asyncio
    async def test_analyze_request(self, protocol):
        """Test request analysis"""
        query = "Analyze this problem"
        context = {}
        
        result = await protocol._analyze_request(query, context)
        
        assert result is not None
        assert "query_type" in result
        assert "domain" in result
        assert "complexity" in result
        protocol.llm_service.generate_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_evaluate_knowledge(self, protocol):
        """Test knowledge evaluation"""
        query = "Analyze this problem"
        context = {
            "knowledge_context": {
                "relevant_info": [
                    {"content": "Relevant info 1", "score": 0.9},
                    {"content": "Relevant info 2", "score": 0.8}
                ],
                "confidence": 0.85
            }
        }
        request_analysis = {"query_type": "informational", "domain": "science"}
        
        result = await protocol._evaluate_knowledge(query, context, request_analysis)
        
        assert result is not None
        assert "sufficiency" in result
        assert "relevance" in result
        assert "gaps" in result
        protocol.llm_service.generate_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_extract_key_points(self, protocol):
        """Test key points extraction"""
        query = "Analyze this problem"
        context = {
            "knowledge_context": {
                "relevant_info": [
                    {"content": "Relevant info 1", "score": 0.9},
                    {"content": "Relevant info 2", "score": 0.8}
                ]
            }
        }
        request_analysis = {"query_type": "informational", "domain": "science"}
        knowledge_evaluation = {"sufficiency": "sufficient", "relevance": "high"}
        
        result = await protocol._extract_key_points(query, context, request_analysis, knowledge_evaluation)
        
        assert result is not None
        assert isinstance(result, list)
        protocol.llm_service.generate_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_plan_response(self, protocol):
        """Test response planning"""
        query = "Analyze this problem"
        context = {}
        request_analysis = {"query_type": "informational", "domain": "science"}
        key_points = ["Point 1", "Point 2"]
        
        result = await protocol._plan_response(query, context, request_analysis, key_points)
        
        assert result is not None
        assert "format" in result
        assert "structure" in result
        assert "tone" in result
        protocol.llm_service.generate_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_analyze_with_error(self, protocol):
        """Test analysis with error"""
        query = "Analyze this problem"
        context = {}
        
        # Simulate error in LLM service
        protocol.llm_service.generate_text.side_effect = Exception("LLM service error")
        
        result = await protocol.execute(query, context)
        
        assert "error" in result
        assert "LLM service error" in result["error"]
        assert result["analysis"] == {}
        assert result["key_points"] == []
        assert result["response_plan"] == {}

    @pytest.mark.asyncio
    async def test_analyze_with_empty_knowledge(self, protocol):
        """Test analysis with empty knowledge context"""
        query = "Analyze this problem"
        context = {"knowledge_context": {"relevant_info": [], "confidence": 0}}
        
        result = await protocol.execute(query, context)
        
        # Should still complete analysis but might indicate knowledge gaps
        assert "analysis" in result
        assert "key_points" in result
        assert "response_plan" in result