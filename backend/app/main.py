from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.v1.api import api_router
from app.core.exceptions import APIException

# FastAPI 앱 생성
app = FastAPI(
    title="KetoHelper API",
    description="키토제닉 다이어트 추천 및 관리 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 미들웨어
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # 프로덕션에서는 특정 도메인으로 제한
)

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")

# 전역 예외 핸들러
@app.exception_handler(APIException)
async def api_exception_handler(request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

# 앱 이벤트 핸들러
@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행되는 함수"""
    try:
        await connect_to_mongo()
        print("✅ MongoDB Atlas 연결 완료")
    except Exception as e:
        print(f"⚠️ MongoDB Atlas 연결 실패: {e}")
        print("💡 .env 파일에서 MONGODB_URL을 확인해주세요")
    
    print("🚀 KetoHelper API 서버가 시작되었습니다!")

@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 실행되는 함수"""
    await close_mongo_connection()
    print("📴 서버 종료")

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "message": "KetoHelper API is running!",
        "version": "1.0.0"
    }

# 루트 엔드포인트
@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "Welcome to KetoHelper API! 🥑",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
