from typing import Optional
from pydantic import BaseSettings
import secrets


class Settings(BaseSettings):
    PROJECT_NAME: str = "Shared Whiteboard"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    SQLITE_DATABASE_URL: str = "sqlite:///./whiteboard.db"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Room Settings
    ROOM_CLEANUP_MINUTES: int = 5
    MAX_ROOMS_PER_IP: int = 10
    DRAWING_BATCH_INTERVAL_MS: int = 100
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings() 