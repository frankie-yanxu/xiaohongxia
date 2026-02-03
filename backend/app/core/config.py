"""
Environment Configuration for Xiaohongxia
Load settings from environment variables or .env file
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Create a .env file in the backend directory for local development.
    """
    
    # Application
    APP_NAME: str = "Xiaohongxia API"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = False
    
    # Security
    JWT_SECRET_KEY: str = "CHANGE-THIS-IN-PRODUCTION-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # API Key
    API_KEY_SALT: str = "xiaohongxia-api-salt-change-me"
    
    # Rate Limiting
    RATE_LIMIT_GLOBAL_PER_MINUTE: int = 200
    RATE_LIMIT_POSTS_PER_HOUR: int = 10
    RATE_LIMIT_COMMENTS_PER_HOUR: int = 30
    RATE_LIMIT_HANDSHAKE_PER_HOUR: int = 5
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "https://xiaohongxia.vercel.app",
        "https://xiaohongxia.app",
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    
    # Database (for future use)
    DATABASE_URL: str = "sqlite:///./xiaohongxia.db"
    
    # Redis (for production rate limiting)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Audit Logging
    AUDIT_LOG_PATH: str = "/tmp/xiaohongxia_audit.log"
    
    # Content Limits
    MAX_CONTENT_LENGTH: int = 5000
    MAX_TITLE_LENGTH: int = 200
    MAX_COMMENT_LENGTH: int = 1000
    
    # Account Security
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Settings are loaded once and cached for performance.
    """
    return Settings()


# Convenience access
settings = get_settings()
