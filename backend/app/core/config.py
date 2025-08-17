from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "FlowPlane Trading Platform"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://frontend:3000"
    ]
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://flowplane:flowplane_dev_password@postgres:5432/flowplane"  # Use 'postgres' as hostname for Docker
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")  # Use 'redis' as hostname for Docker
    
    # Market Data Providers
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY", "")
    POLYGON_WS_URL: str = "wss://socket.polygon.io"
    POLYGON_REST_URL: str = "https://api.polygon.io"
    
    # Trading Platform
    ALPACA_API_KEY: str = os.getenv("ALPACA_API_KEY", "")
    ALPACA_SECRET_KEY: str = os.getenv("ALPACA_SECRET_KEY", "")
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"  # Paper trading by default
    ALPACA_DATA_URL: str = "https://data.alpaca.markets"
    
    # AI Services
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")  # Use 'redis' as hostname for Docker
    CELERY_RESULT_BACKEND: str = os.getenv("REDIS_URL", "redis://redis:6379")  # Use 'redis' as hostname for Docker
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Market Scanning
    SCAN_INTERVAL_MINUTES: int = 5
    MAX_SYMBOLS_PER_SCAN: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()