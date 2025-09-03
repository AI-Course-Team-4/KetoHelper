from fastapi import APIRouter
from app.api.v1.endpoints import auth, recipes, restaurants, users

# API v1 라우터
api_router = APIRouter()

# 각 엔드포인트 라우터 등록
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(users.router, prefix="/users", tags=["사용자"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["레시피"])
api_router.include_router(restaurants.router, prefix="/restaurants", tags=["식당"])
