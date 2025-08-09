"""Application configuration settings."""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = Field(default="ReelsBot", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Security
    SECRET_KEY: str = Field(env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./reelsbot.db", env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # OpenAI
    OPENAI_API_KEY: str = Field(env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    OPENAI_TEMPERATURE: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    OPENAI_MAX_TOKENS: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    
    # External APIs
    SPOTIFY_CLIENT_ID: Optional[str] = Field(default=None, env="SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET: Optional[str] = Field(default=None, env="SPOTIFY_CLIENT_SECRET")
    YOUTUBE_API_KEY: Optional[str] = Field(default=None, env="YOUTUBE_API_KEY")
    TIKTOK_ACCESS_TOKEN: Optional[str] = Field(default=None, env="TIKTOK_ACCESS_TOKEN")
    
    # Monitoring
    WANDB_API_KEY: Optional[str] = Field(default=None, env="WANDB_API_KEY")
    WANDB_PROJECT: str = Field(default="reelsbot", env="WANDB_PROJECT")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=3600, env="RATE_LIMIT_WINDOW")
    
    # Cache
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Content Generation
    MAX_SCRIPT_LENGTH: int = Field(default=5000, env="MAX_SCRIPT_LENGTH")
    DEFAULT_PLATFORM: str = Field(default="instagram", env="DEFAULT_PLATFORM")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()