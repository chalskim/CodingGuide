import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.protocols.knowledge import KnowledgeAccessProtocol
from app.protocols.generation import ContentGenerationProtocol

@pytest.mark.asyncio
class TestKnowledgeGenerationIntegration:
    """Test the integration between KnowledgeAccessProtocol and ContentGenerationProtocol"""

    @pytest.fixture
    def knowledge_protocol(self):
        """Fixture for KnowledgeAccessProtocol instance"""
        with patch('app.protocols.knowledge.VectorDBService') as mock_vector_db_cls, \
             patch('app.protocols.knowledge.SearchService') as mock_search_cls, \
             patch('app.protocols.knowledge.logger') as mock_logger:
            
            # Setup mock vector DB service
            mock_vector_db = AsyncMock()
            mock_vector_db.search.return_value = [
                {"content": "Test content 1", "metadata": {"source": "source1"}},
                {"content": "Test content 2", "metadata": {"source": "source2"}}
            ]
            mock_vector_db_cls.return_value = mock_vector_db
            
            # Setup mock search service
            mock_search = AsyncMock()
            mock_search.search.return_value = [
                {"content": "External content 1", "url": "http://example.com/1"},
                {"content": "External content 2", "url": "http://example.com/2"}
            ]
            mock_search_cls.return_value = mock_search
            
            protocol = KnowledgeAccessProtocol()
            protocol.vector_db = mock_vector_db
            protocol.search_service = mock_search
            
            yield protocol

    @pytest.fixture
    def generation_protocol(self):
        """Fixture for ContentGenerationProtocol instance"""
        with patch('app.protocols.generation.LLMService') as mock_llm_cls, \
             patch('app.protocols.generation.DatabaseService') as mock_db_cls, \
             patch('app.protocols.generation.logger') as mock_logger:
            
            # Setup mock LLM service
            mock_llm = AsyncMock()
            mock_llm.generate_text.return_value = "Generated content based on knowledge"
            mock_llm_cls.return_value = mock_llm
            
            # Setup mock DB service
            mock_db = MagicMock()
            mock_db.save.return_value = "record_id"
            mock_db_cls.return_value = mock_db
            
            protocol = ContentGenerationProtocol()
            protocol.llm_service = mock_llm
            protocol.db_service = mock_db
            
            yield protocol

    @pytest.mark.asyncio
    async def test_knowledge_to_generation_flow(self, knowledge_protocol, generation_protocol):
        """Test the flow from knowledge retrieval to content generation"""
        # Step 1: Retrieve knowledge
        query = "test query"
        knowledge_context = {"max_results": 4, "use_external_search": True}
        
        knowledge_result = await knowledge_protocol.execute(query, knowledge_context)
        
        assert "results" in knowledge_result
        assert len(knowledge_result["results"]) > 0
        assert "sources" in knowledge_result
        
        # Step 2: Use knowledge results for content generation
        generation_prompt = "Generate content based on this knowledge"
        generation_context = {
            "knowledge": knowledge_result["results"],
            "sources": knowledge_result["sources"],
            "parameters": {"max_tokens": 500, "temperature": 0.7}
        }
        
        generation_result = await generation_protocol.execute(generation_prompt, generation_context)
        
        assert "content" in generation_result
        assert generation_result["content"] == "Generated content based on knowledge"
        assert "metadata" in generation_result
        
        # Verify the LLM service was called with knowledge context
        generation_protocol.llm_service.generate_text.assert_awaited_once()
        args, kwargs = generation_protocol.llm_service.generate_text.await_args
        assert "knowledge" in args[1]  # Check that knowledge was passed in the context

    @pytest.mark.asyncio
    async def test_knowledge_to_generation_with_empty_results(self, knowledge_protocol, generation_protocol):
        """Test the flow when knowledge retrieval returns empty results"""
        # Mock empty results from knowledge protocol
        knowledge_protocol.vector_db.search.return_value = []
        knowledge_protocol.search_service.search.return_value = []
        
        # Step 1: Retrieve knowledge (empty results)
        query = "unknown query"
        knowledge_context = {"max_results": 4, "use_external_search": True}
        
        knowledge_result = await knowledge_protocol.execute(query, knowledge_context)
        
        assert "results" in knowledge_result
        assert len(knowledge_result["results"]) == 0
        
        # Step 2: Use empty knowledge results for content generation
        generation_prompt = "Generate content based on this knowledge"
        generation_context = {
            "knowledge": knowledge_result["results"],
            "sources": knowledge_result.get("sources", []),
            "parameters": {"max_tokens": 500, "temperature": 0.7}
        }
        
        generation_result = await generation_protocol.execute(generation_prompt, generation_context)
        
        assert "content" in generation_result
        # The generation should still work even with empty knowledge
        assert generation_result["content"] == "Generated content based on knowledge"

    @pytest.mark.asyncio
    async def test_knowledge_to_generation_with_error_handling(self, knowledge_protocol, generation_protocol):
        """Test error handling in the knowledge to generation flow"""
        # Mock error in knowledge retrieval
        knowledge_protocol.vector_db.search.side_effect = Exception("Vector DB error")
        
        # Step 1: Attempt to retrieve knowledge (will fail)
        query = "test query"
        knowledge_context = {"max_results": 4, "use_external_search": False}
        
        knowledge_result = await knowledge_protocol.execute(query, knowledge_context)
        
        assert "error" in knowledge_result
        assert "Vector DB error" in knowledge_result["error"]
        
        # Step 2: Handle error in generation protocol
        generation_prompt = "Generate content based on this knowledge"
        generation_context = {
            "knowledge": [],  # Empty knowledge due to error
            "error": knowledge_result.get("error"),
            "parameters": {"max_tokens": 500, "temperature": 0.7}
        }
        
        generation_result = await generation_protocol.execute(generation_prompt, generation_context)
        
        assert "content" in generation_result
        # The generation should still produce content even with error in knowledge
        assert generation_result["content"] == "Generated content based on knowledge"