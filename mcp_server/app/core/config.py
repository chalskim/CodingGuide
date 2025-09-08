from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    # 프로젝트 정보
    PROJECT_NAME: str = "MCP Server"
    PROJECT_DESCRIPTION: str = "Universal MCP Framework 기반 지능형 AI 백엔드 서버"
    VERSION: str = "0.1.0"
    
    # API 문서 URL
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    
    # CORS 설정
    CORS_ORIGINS: List[str] = ["*"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # 데이터베이스 설정
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # LLM API 설정
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    
    # 벡터 데이터베이스 설정
    VECTOR_DB_PATH: str = Field("./data/vector_db", env="VECTOR_DB_PATH")
    
    # 검색 API 설정
    GOOGLE_SEARCH_API_KEY: Optional[str] = Field(None, env="GOOGLE_SEARCH_API_KEY")
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = Field(None, env="GOOGLE_SEARCH_ENGINE_ID")
    PERPLEXITY_API_KEY: Optional[str] = Field(None, env="PERPLEXITY_API_KEY")
    PERPLEXITY_API_URL: str = Field("https://api.perplexity.ai/chat/completions", env="PERPLEXITY_API_URL")
    SEARCH_PROVIDER: str = Field("google", env="SEARCH_PROVIDER")  # google, bing, duckduckgo, perplexity
    
    # 로깅 설정
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(None, env="LOG_FILE")
    
    # 토큰 설정
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Universal Prompt 템플릿 설정
    UNIVERSAL_PROMPT_TEMPLATE_PATH: str = Field(
        "./data/templates/universal_prompt.txt", 
        env="UNIVERSAL_PROMPT_TEMPLATE_PATH"
    )
    
    # 기본 LLM 설정
    DEFAULT_LLM_PROVIDER: str = Field("openai", env="DEFAULT_LLM_PROVIDER")
    DEFAULT_LLM_MODEL: str = Field("gpt-4", env="DEFAULT_LLM_MODEL")
    
    # 임베딩 모델 설정
    EMBEDDING_MODEL: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2", 
        env="EMBEDDING_MODEL"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> str:
        if not v:
            return "sqlite:///./data/mcp_server.db"
        return v

# 설정 인스턴스 생성
settings = Settings()