import pytest
import time
import sys
from unittest.mock import MagicMock, patch

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

# 이제 BaseProtocol을 임포트
from app.protocols.base import BaseProtocol

class TestBaseProtocol:
    """Test cases for BaseProtocol"""

    class ConcreteProtocol(BaseProtocol):
        """Concrete implementation of BaseProtocol for testing"""
        async def execute(self, *args, **kwargs):
            """Implement abstract method"""
            self.log_execution("execute", {"message": "Executing concrete protocol"})
            return {"result": "success"}

    def test_initialization(self):
        """Test protocol initialization"""
        protocol = self.ConcreteProtocol()
        
        assert protocol.name == "ConcreteProtocol"
        assert protocol.execution_log == []
        assert protocol.metadata == {}

    @pytest.mark.asyncio
    async def test_execute_method(self):
        """Test execute method"""
        protocol = self.ConcreteProtocol()
        result = await protocol.execute()
        
        assert result == {"result": "success"}
        assert len(protocol.execution_log) == 1
        assert protocol.execution_log[0]["step"] == "execute"
        assert protocol.execution_log[0]["data"]["message"] == "Executing concrete protocol"

    def test_log_execution(self):
        """Test log_execution method"""
        protocol = self.ConcreteProtocol()
        protocol.log_execution("test", {"message": "Test message"})
        
        assert len(protocol.execution_log) == 1
        assert protocol.execution_log[0]["step"] == "test"
        assert protocol.execution_log[0]["data"]["message"] == "Test message"

    def test_get_execution_log(self):
        """Test get_execution_log method"""
        protocol = self.ConcreteProtocol()
        protocol.log_execution("step1", {"message": "Message 1"})
        protocol.log_execution("step2", {"message": "Message 2"})
        
        logs = protocol.get_execution_log()
        assert len(logs) == 2
        assert logs[0]["step"] == "step1"
        assert logs[0]["data"]["message"] == "Message 1"
        assert logs[1]["step"] == "step2"
        assert logs[1]["data"]["message"] == "Message 2"

    def test_set_metadata(self):
        """Test set_metadata method"""
        protocol = self.ConcreteProtocol()
        protocol.set_metadata("key1", "value1")
        protocol.set_metadata("key2", {"nested": "value2"})
        
        assert protocol.metadata["key1"] == "value1"
        assert protocol.metadata["key2"] == {"nested": "value2"}

    def test_get_metadata(self):
        """Test get_metadata method"""
        protocol = self.ConcreteProtocol()
        protocol.set_metadata("key1", "value1")
        
        assert protocol.get_metadata("key1") == "value1"
        assert protocol.get_metadata("non_existent") is None
        assert protocol.get_metadata("non_existent", "default") == "default"

    def test_get_all_metadata(self):
        """Test get_all_metadata method"""
        protocol = self.ConcreteProtocol()
        protocol.set_metadata("key1", "value1")
        protocol.set_metadata("key2", "value2")
        
        metadata = protocol.get_all_metadata()
        assert metadata == {"key1": "value1", "key2": "value2"}

    def test_str_representation(self):
        """Test string representation"""
        protocol = self.ConcreteProtocol()
        str_repr = str(protocol)
        
        assert "ConcreteProtocol Protocol" in str_repr