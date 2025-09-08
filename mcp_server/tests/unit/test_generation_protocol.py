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

# LLMService 모킹
sys.modules["app.services.llm"] = MagicMock()
sys.modules["app.services.llm"].LLMService = MagicMock()

# 이제 ContentGenerationProtocol을 임포트
from app.protocols.generation import ContentGenerationProtocol

class TestContentGenerationProtocol:
    """Test cases for ContentGenerationProtocol"""

    @pytest.fixture
    def protocol(self):
        """Fixture for ContentGenerationProtocol instance"""
        with patch('app.protocols.generation.LLMService') as mock_llm_cls, \
             patch('app.protocols.generation.logger') as mock_logger:
            
            # Setup mock LLM service
            mock_llm = AsyncMock()
            mock_llm.generate_text.return_value = "Generated content"
            mock_llm_cls.return_value = mock_llm
            
            protocol = ContentGenerationProtocol()
            protocol.llm_service = mock_llm
            
            yield protocol

    @pytest.mark.asyncio
    async def test_execute_method(self, protocol):
        """Test execute method"""
        prompt = "Generate some text"
        context = {"max_tokens": 100}
        
        result = await protocol.execute(prompt, context)
        
        assert result == "Generated content"

    @pytest.mark.asyncio
    async def test_generate(self, protocol):
        """Test content generation"""
        prompt = "Generate some text"
        reasoning_result = {}
        knowledge_context = {}
        context = {"max_tokens": 100}
        
        result = await protocol.generate(prompt, reasoning_result, knowledge_context, context)
        
        assert result == "Generated content"
        protocol.llm_service.generate_text.assert_awaited_once()

    def test_prepare_generation_params_default(self, protocol):
        """Test parameter preparation with defaults"""
        prompt = "Generate some text"
        reasoning_result = {}
        knowledge_context = {}
        context = {}
        
        params = protocol._prepare_generation_params(prompt, reasoning_result, knowledge_context, context)
        
        assert "format" in params
        assert params["format"] == "text"  # Default value

    def test_prepare_generation_params_custom(self, protocol):
        """Test parameter preparation with custom values"""
        prompt = "Generate some text"
        reasoning_result = {"suggested_format": "markdown", "tone": "professional"}
        knowledge_context = {}
        context = {
            "format": "html",
            "domain": "technical"
        }
        
        params = protocol._prepare_generation_params(prompt, reasoning_result, knowledge_context, context)
        
        assert params["format"] == "markdown"  # From reasoning_result
        assert params["tone"] == "professional"  # From reasoning_result
        assert params["domain"] == "technical"  # From context

    @pytest.mark.asyncio
    async def test_build_enhanced_prompt(self, protocol):
        """Test enhanced prompt construction"""
        prompt = "Generate text"
        reasoning_result = {"key_points": ["Point 1", "Point 2"]}
        knowledge_context = {"sources": ["Source 1", "Source 2"]}
        
        # Mock the _build_enhanced_prompt method
        with patch.object(protocol, '_build_enhanced_prompt', return_value="Enhanced prompt") as mock_build:
            await protocol.generate(prompt, reasoning_result, knowledge_context, {})
            
            mock_build.assert_called_once_with(prompt, reasoning_result, knowledge_context)
            protocol.llm_service.generate_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generation_with_error(self, protocol):
        """Test generation with error"""
        prompt = "Generate text"
        reasoning_result = {}
        knowledge_context = {}
        context = {}
        
        # Simulate error in LLM service
        protocol.llm_service.generate_text.side_effect = Exception("LLM service error")
        
        with pytest.raises(Exception) as excinfo:
            await protocol.generate(prompt, reasoning_result, knowledge_context, context)
        
        assert "LLM service error" in str(excinfo.value)

    def test_store_generation_history(self, protocol):
        """Test storing generation history"""
        prompt = "Test prompt"
        content = "Generated content"
        context = {"temperature": 0.7}
        
        protocol._store_generation_history(prompt, content, context)
        
        assert len(protocol.generation_history) == 1
        assert protocol.generation_history[0]["prompt"] == "Test prompt"
        assert protocol.generation_history[0]["content"] == "Generated content"

    def test_generation_history(self, protocol):
        """Test generation history"""
        # Add some history
        protocol._store_generation_history("Prompt 1", "Content 1", {})
        protocol._store_generation_history("Prompt 2", "Content 2", {})
        
        # Check history
        assert len(protocol.generation_history) == 2
        assert protocol.generation_history[0]["prompt"] == "Prompt 1"
        assert protocol.generation_history[1]["prompt"] == "Prompt 2"