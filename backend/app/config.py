import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "postgresql://neondb_owner:npg_Gl3iHDhC8oar@ep-gentle-shadow-a1l92x53-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    
    # Cerebras API Configuration
    cerebras_api_key: str = "csk-j45pxjxj3y6wkmexnxmk5vd48ypdy4npd35t695hkvn6jrvf"
    
    # Redis Configuration
    redis_url: str = "redis://redis:6379"
    
    # Application Configuration
    secret_key: str = "your-secret-key-change-in-production"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # File Upload Configuration
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB
    
    # Code Execution Configuration
    sandbox_timeout: int = 30  # 30 seconds
    
    # Security
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields


settings = Settings()