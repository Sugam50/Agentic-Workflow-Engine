"""Configuration management for the Agentic Workflow Engine."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    
    # Database Configuration
    database_url: Optional[str] = None
    
    # Redis Configuration
    redis_url: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    # Workflow Configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    workflow_timeout: int = 3600  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
