"""
키토 식단 추천 웹앱 메인 애플리케이션
대화형 키토 식단 레시피 추천 + 주변 키토 친화 식당 찾기
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import uvicorn
import os, re
from dotenv import load_dotenv
import asyncio

from app.api import chat, places, plans
from app.api import auth as auth_api
from app.core.config import settings
from app.core.database import init_db

# 환경 변수 로드
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 함수"""
    # 시작 시
    print("🚀 키토 코치 API 서버 시작")
    
    # 데이터베이스 초기화
    await init_db()
    
    yield
    
    # 종료 시
    print("⏹️ 키토 코치 API 서버 종료")

# FastAPI 앱 생성
app = FastAPI(
    title="키토 코치 API",
    description="대화형 한국형 키토 식단 레시피 추천 + 주변 키토 친화 식당 찾기",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat.router, prefix="/api/v1")
app.include_router(places.router, prefix="/api/v1") 
app.include_router(plans.router, prefix="/api/v1")
app.include_router(auth_api.router, prefix="/api/v1")

@app.get("/")
async def root():
    """루트 엔드포인트 - 서비스 상태 확인"""
    return {
        "message": "키토 코치 API 서버가 실행 중입니다 🥑",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "ok", "service": "keto-coach-api"}

if __name__ == "__main__":
    print("🚀 직접 실행으로 서버를 시작합니다...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
