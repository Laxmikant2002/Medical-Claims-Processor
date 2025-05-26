from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_TITLE: str = "Medical Claims Processing API"
    API_DESCRIPTION: str = "Process medical claims using AI-powered document analysis"
    API_VERSION: str = "1.0.0"
    
    # Google API Configuration
    GOOGLE_API_KEY: str
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: set = {"application/pdf"}

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Initialize settings
settings = get_settings() 