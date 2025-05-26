from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Medical Claims Processor"
    
    # Security
    GOOGLE_API_KEY: str
    
    # Redis Configuration
    # Local Docker Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Redis Cloud Configuration
    REDIS_HOST: str = "redis-12125.c16.us-east-1-2.ec2.redns.redis-cloud.com"
    REDIS_PORT: int = 12125
    REDIS_USERNAME: str = "default"
    REDIS_PASSWORD: str = "U03Az0sQsGWdOX6oV9Yc216uMZuVgVb1"
    USE_REDIS_CLOUD: bool = True  # Set to True to use Redis Cloud, False for local Docker
    
    # File Processing
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_FILE_TYPES: set = {"pdf"}
    
    # Vector Search
    VECTOR_DIMENSION: int = 768
    VECTOR_SIMILARITY_METRIC: str = "COSINE"
    
    # Model Configuration
    MODEL_NAME: str = "gemini-pro"
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    
    # Tesseract Configuration
    TESSERACT_CMD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Initialize settings instance
settings = get_settings() 