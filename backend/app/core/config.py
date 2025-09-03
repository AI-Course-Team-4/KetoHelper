from typing import List, Optional
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    PROJECT_NAME: str = "KetoHelper"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 데이터베이스 설정
    MONGODB_URL: str = "mongodb+srv://soohwan225_db_user:GUsZ5grTUglOZjyL@cluster0.ysh90y4.mongodb.net/ketohelper?retryWrites=true&w=majority&appName=Cluster0"
    MONGODB_DATABASE: str = "ketohelper"
    
    # JWT 설정
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google OAuth 설정
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # OpenAI API 설정
    OPENAI_API_KEY: Optional[str] = None
    
    # Pinecone 설정
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    
    # CORS 설정 - 고정값으로 설정
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"]
    
    # 외부 API 키
    KAKAO_REST_API_KEY: Optional[str] = None
    NAVER_CLIENT_ID: Optional[str] = None
    NAVER_CLIENT_SECRET: Optional[str] = None
    
    # Redis 설정 (선택사항)
    REDIS_URL: Optional[str] = None
    
    # 로그 레벨
    LOG_LEVEL: str = "INFO"
    
    class Config:
        # .env 파일 사용하지 않음 - 오류 방지
        case_sensitive = True

# 설정 인스턴스 생성
settings = Settings()