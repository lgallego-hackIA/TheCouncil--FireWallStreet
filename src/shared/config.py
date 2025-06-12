"""
Configuration settings for theCouncil API system.
"""
import os
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    APP_NAME: str = "theCouncil"
    DEBUG: bool = False
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Authentication settings
    SECRET_KEY: str = "change_this_in_production"
    AUTH_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database settings - these would be used for the central configuration database
    DATABASE_URL: Optional[str] = None
    
    # Storage settings
    AUTOMATION_STORAGE_DIR: str = "data/automations"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Model settings (for pydantic)
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Create settings instance
settings = Settings()

# Storage directories are expected to exist as part of the deployment package.


def get_settings() -> Settings:
    """Return the settings instance."""
    return settings
