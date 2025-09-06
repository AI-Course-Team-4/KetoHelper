"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging

from search_service import SearchService
from config import validate_config

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="벡터 검색 시스템 V0",
    description="OpenAI 임베딩과 Supabase pgvector를 사용한 메뉴 검색 API",
    version="0.1.0"
)

# 전역 서비스 인스턴스
search_service = None

# 요청/응답 모델
class SearchRequest(BaseModel):
    preference_text: str
    top_k: Optional[int] = 5

class MenuResult(BaseModel):
    restaurant_name: str
    menu_name: str
    address: str
    price: Optional[int]
    category: Optional[str]
    score: float

class SearchResponse(BaseModel):
    items: List[MenuResult]
    query: str
    total_results: int

class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    searchable_menus: int
    search_working: bool

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 초기화"""
    global search_service
    
    try:
        # 환경 변수 검증
        validate_config()
        logger.info("환경 설정 검증 완료")
        
        # 검색 서비스 초기화
        search_service = SearchService()
        logger.info("검색 서비스 초기화 완료")
        
        # 서비스 상태 확인
        health = search_service.health_check()
        if health['status'] != 'healthy':
            logger.warning(f"서비스 상태 확인: {health}")
        else:
            logger.info("서비스 정상 동작 확인")
            
    except Exception as e:
        logger.error(f"앱 초기화 실패: {e}")
        raise

@app.get("/", summary="API 정보")
async def root():
    """API 기본 정보"""
    return {
        "name": "벡터 검색 시스템 V0",
        "version": "0.1.0",
        "description": "OpenAI 임베딩 기반 메뉴 검색 API",
        "endpoints": {
            "search": "/search",
            "health": "/health",
            "stats": "/stats"
        }
    }

@app.get("/health", response_model=HealthResponse, summary="서비스 상태 확인")
async def health_check():
    """서비스 헬스체크"""
    if not search_service:
        raise HTTPException(status_code=503, detail="검색 서비스가 초기화되지 않았습니다")
    
    try:
        health = search_service.health_check()
        
        if health['status'] == 'error':
            raise HTTPException(status_code=503, detail=health.get('error', '알 수 없는 오류'))
        
        return HealthResponse(**health)
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/stats", summary="검색 통계")
async def get_stats():
    """검색 가능한 메뉴 통계"""
    if not search_service:
        raise HTTPException(status_code=503, detail="검색 서비스가 초기화되지 않았습니다")
    
    try:
        stats = search_service.get_search_stats()
        return stats
    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse, summary="메뉴 검색")
async def search_menus(request: SearchRequest):
    """
    사용자 선호도 텍스트로 메뉴 검색
    
    - **preference_text**: 검색할 선호도 텍스트 (예: "매운 음식", "따뜻한 국물")
    - **top_k**: 반환할 결과 개수 (기본값: 5)
    """
    if not search_service:
        raise HTTPException(status_code=503, detail="검색 서비스가 초기화되지 않았습니다")
    
    # 입력 검증
    if not request.preference_text.strip():
        raise HTTPException(status_code=400, detail="검색어를 입력해주세요")
    
    if request.top_k <= 0 or request.top_k > 20:
        raise HTTPException(status_code=400, detail="top_k는 1-20 사이의 값이어야 합니다")
    
    try:
        # 검색 수행
        results = search_service.search(request.preference_text, request.top_k)
        
        # 응답 포맷팅
        menu_results = [MenuResult(**result) for result in results]
        
        return SearchResponse(
            items=menu_results,
            query=request.preference_text,
            total_results=len(menu_results)
        )
        
    except Exception as e:
        logger.error(f"검색 실패: {e}")
        raise HTTPException(status_code=500, detail="검색 중 오류가 발생했습니다")

@app.get("/search", response_model=SearchResponse, summary="메뉴 검색 (GET)")
async def search_menus_get(
    preference_text: str = Query(..., description="검색할 선호도 텍스트"),
    top_k: int = Query(5, description="반환할 결과 개수", ge=1, le=20)
):
    """
    GET 방식으로 메뉴 검색 (테스트 편의용)
    """
    request = SearchRequest(preference_text=preference_text, top_k=top_k)
    return await search_menus(request)

if __name__ == "__main__":
    import uvicorn
    
    # 개발 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
