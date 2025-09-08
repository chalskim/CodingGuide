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
    ***REMOVED*** = "***REMOVED***test"
    ***REMOVED*** = "test-key"
    GOOGLE_API_KEY = "test-key"
    VECTOR_DB_PATH = "./data/test_vector_db"
    GOOGLE_SEARCH_API_KEY = "test-key"
    GOOGLE_SEARCH_ENGINE_ID = "test-id"

# app.core.config 모듈을 모킹
sys.modules["app.core.config"] = MagicMock()
sys.modules["app.core.config"].settings = MockSettings()

# 필요한 서비스 모킹
sys.modules["app.services.vector_db"] = MagicMock()
sys.modules["app.services.vector_db"].VectorDBService = MagicMock()
sys.modules["app.services.search"] = MagicMock()
sys.modules["app.services.search"].SearchService = MagicMock()

# 이제 KnowledgeAccessProtocol을 임포트
from app.protocols.knowledge import KnowledgeAccessProtocol

class TestKnowledgeAccessProtocol:
    """Test cases for KnowledgeAccessProtocol"""

    @pytest.fixture
    def protocol(self):
        """Fixture for KnowledgeAccessProtocol instance"""
        with patch('app.protocols.knowledge.VectorDBService') as mock_vector_db_cls, \
             patch('app.protocols.knowledge.SearchService') as mock_search_cls, \
             patch('app.protocols.knowledge.logger'):
            
            # Setup mock vector db service
            mock_vector_db = AsyncMock()
            mock_vector_db.search.return_value = [
                {"content": "Vector result 1", "score": 0.9, "metadata": {"source": "doc1"}},
                {"content": "Vector result 2", "score": 0.8, "metadata": {"source": "doc2"}}
            ]
            mock_vector_db_cls.return_value = mock_vector_db
            
            # Setup mock search service
            mock_search = AsyncMock()
            mock_search.search.return_value = [
                {"content": "External result 1", "score": 0.7, "source": "web1"},
                {"content": "External result 2", "score": 0.6, "source": "web2"}
            ]
            mock_search_cls.return_value = mock_search
            
            protocol = KnowledgeAccessProtocol()
            protocol.vector_db = mock_vector_db
            protocol.search_service = mock_search
            
            yield protocol

    @pytest.mark.asyncio
    async def test_retrieve_knowledge_success(self, protocol):
        """Test successful knowledge retrieval"""
        query = "test query"
        context = {"vector_search_limit": 5, "external_search_limit": 3}
        
        result = await protocol.retrieve_knowledge(query, context)
        
        assert "relevant_info" in result
        assert "sources" in result
        assert "confidence" in result
        assert len(result["relevant_info"]) > 0
        assert len(result["sources"]) > 0
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_execute_method(self, protocol):
        """Test execute method"""
        query = "test query"
        context = {"vector_search_limit": 5}
        
        result = await protocol.execute(query, context)
        
        assert "relevant_info" in result
        assert "sources" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_vector_search(self, protocol):
        """Test vector search functionality"""
        query = "test query"
        context = {"vector_search_limit": 5, "vector_search_threshold": 0.7}
        
        result = await protocol._perform_vector_search(query, context)
        
        assert result is not None
        assert "relevant_info" in result
        assert len(result["relevant_info"]) == 2
        assert result["confidence"] == 0.9
        protocol.vector_db.search.assert_awaited_once_with(query, limit=5, threshold=0.7)

    @pytest.mark.asyncio
    async def test_external_search(self, protocol):
        """Test external search functionality"""
        query = "test query"
        context = {"external_search_limit": 3}
        
        result = await protocol._perform_external_search(query, context)
        
        assert result is not None
        assert "relevant_info" in result
        assert len(result["relevant_info"]) == 2
        assert result["confidence"] == 0.7
        protocol.search_service.search.assert_awaited_once_with(query, limit=3)

    def test_should_perform_external_search(self, protocol):
        """Test external search decision logic"""
        # Case 1: Always search external
        context = {"always_search_external": True}
        knowledge_context = {"confidence": 0.9, "relevant_info": [1, 2, 3]}
        assert protocol._should_perform_external_search(knowledge_context, context) is True
        
        # Case 2: High confidence, no external search needed
        context = {"sufficient_confidence": 0.8}
        knowledge_context = {"confidence": 0.9, "relevant_info": [1, 2, 3]}
        assert protocol._should_perform_external_search(knowledge_context, context) is False
        
        # Case 3: Low confidence, external search needed
        context = {"sufficient_confidence": 0.8}
        knowledge_context = {"confidence": 0.7, "relevant_info": [1, 2, 3]}
        assert protocol._should_perform_external_search(knowledge_context, context) is True
        
        # Case 4: Not enough relevant info
        context = {"min_relevant_info": 3}
        knowledge_context = {"confidence": 0.7, "relevant_info": [1]}
        assert protocol._should_perform_external_search(knowledge_context, context) is True

    def test_deduplicate_and_rank(self, protocol):
        """Test deduplication and ranking"""
        relevant_info = [
            {"content": "Duplicate content", "score": 0.7, "source": "source1"},
            {"content": "Duplicate content", "score": 0.8, "source": "source2"},  # Higher score should be kept
            {"content": "Unique content", "score": 0.6, "source": "source3"}
        ]
        
        result = protocol._deduplicate_and_rank(relevant_info)
        
        assert len(result) == 2  # Duplicates should be removed
        assert result[0]["content"] == "Duplicate content"  # Highest score should be first
        assert result[0]["score"] == 0.8  # Higher score version should be kept
        assert result[1]["content"] == "Unique content"

    @pytest.mark.asyncio
    async def test_retrieve_knowledge_with_error(self, protocol):
        """Test knowledge retrieval with error"""
        query = "test query"
        context = {}
        
        # Simulate error in vector search
        protocol.vector_db.search.side_effect = Exception("Vector search error")
        # 외부 검색도 실패하도록 설정
        protocol.search_service.search.side_effect = Exception("External search error")
        
        result = await protocol.retrieve_knowledge(query, context)
        
        # Should return empty context on error
        assert result["relevant_info"] == []
        assert result["sources"] == []
        assert result["confidence"] == 0.0

    def test_get_sources(self, protocol):
        """Test get_sources method"""
        protocol.sources = ["source1", "source2"]
        
        sources = protocol.get_sources()
        
        assert sources == ["source1", "source2"]