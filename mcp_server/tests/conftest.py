import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# 테스트 환경 설정을 위한 패치
@pytest.fixture(scope="session", autouse=True)
def mock_settings():
    """Settings 객체를 모킹하여 테스트 환경 설정"""
    # app.core.config 모듈 임포트 전에 패치 적용
    with patch.dict(os.environ, {
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "LOG_LEVEL": "debug",
        "SECRET_KEY": "test-secret-key",
        "API_PREFIX": "/api/v1",
        "CORS_ORIGINS": "http://localhost:3000,http://localhost:8080",
        "DATABASE_URL": "sqlite:///./test.db",
        "***REMOVED***": "***REMOVED***test",
        "***REMOVED***": "test-key",
        "GOOGLE_API_KEY": "test-key",
        "VECTOR_DB_PATH": "./data/test_vector_db",
        "GOOGLE_SEARCH_API_KEY": "test-key",
        "GOOGLE_SEARCH_ENGINE_ID": "test-id"
    }):
        yield

@pytest.fixture
def mock_logger():
    """Fixture for mocking logger"""
    return MagicMock()

@pytest.fixture
def mock_llm_service():
    """Fixture for mocking LLM service"""
    mock = MagicMock()
    mock.generate_text.return_value = "Generated text"
    return mock

@pytest.fixture
def mock_vector_db_service():
    """Fixture for mocking Vector DB service"""
    mock = MagicMock()
    mock.search.return_value = [
        {"content": "Vector search result 1", "score": 0.95},
        {"content": "Vector search result 2", "score": 0.85}
    ]
    return mock

@pytest.fixture
def mock_search_service():
    """Fixture for mocking external search service"""
    mock = MagicMock()
    mock.search.return_value = [
        {"title": "Search result 1", "content": "External search content 1", "url": "http://example.com/1"},
        {"title": "Search result 2", "content": "External search content 2", "url": "http://example.com/2"}
    ]
    return mock

@pytest.fixture
def mock_db_service():
    """Fixture for mocking database service"""
    mock = MagicMock()
    mock.save.return_value = "record_id"
    mock.get.return_value = {"id": "record_id", "data": "test data"}
    return mock