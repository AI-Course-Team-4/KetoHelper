#!/usr/bin/env python3
"""
키토 레시피 추천 시스템 웹 애플리케이션
"""

import sys
sys.path.append('src')

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import asyncio
from typing import List, Optional
import os

from hybrid_search_engine import HybridSearchEngine

# FastAPI 앱 초기화
app = FastAPI(title="키토 레시피 추천 시스템", version="1.0.0")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 검색 엔진 초기화
search_engine = HybridSearchEngine()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """메인 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/search", response_class=HTMLResponse)
async def search_recipes(
    request: Request,
    query: str = Form(...),
    disliked_ingredients: str = Form(""),
    allergies: str = Form(""),
    search_type: str = Form("hybrid")
):
    """레시피 검색"""
    try:
        # 입력 데이터 처리
        disliked_list = [x.strip() for x in disliked_ingredients.split(",") if x.strip()]
        allergies_list = [x.strip() for x in allergies.split(",") if x.strip()]
        
        # 검색 실행
        results = await search_engine.hybrid_search(
            query=query,
            disliked_ingredients=disliked_list,
            allergies=allergies_list,
            search_type=search_type,
            limit=10
        )
        
        # 결과 처리
        processed_results = []
        for recipe in results:
            search_scores = recipe.get("_search_scores", {})
            processed_results.append({
                "id": recipe.get("id"),
                "title": recipe.get("title", "제목 없음"),
                "author": recipe.get("author", "작성자 없음"),
                "rating": recipe.get("rating", 0),
                "views": recipe.get("views", 0),
                "cook_time": recipe.get("cook_time", "시간 미정"),
                "difficulty": recipe.get("difficulty", "난이도 미정"),
                "servings": recipe.get("servings", "인분 미정"),
                "summary": recipe.get("summary", "요약 없음"),
                "ingredients": recipe.get("ingredients", []),
                "steps": recipe.get("steps", []),
                "tags": recipe.get("tags", []),
                "search_scores": search_scores
            })
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "query": query,
            "disliked_ingredients": disliked_ingredients,
            "allergies": allergies,
            "search_type": search_type,
            "results": processed_results,
            "result_count": len(processed_results)
        })
        
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/api/search")
async def api_search(
    query: str,
    disliked_ingredients: str = "",
    allergies: str = "",
    search_type: str = "hybrid",
    limit: int = 10
):
    """API 엔드포인트"""
    try:
        disliked_list = [x.strip() for x in disliked_ingredients.split(",") if x.strip()]
        allergies_list = [x.strip() for x in allergies.split(",") if x.strip()]
        
        results = await search_engine.hybrid_search(
            query=query,
            disliked_ingredients=disliked_list,
            allergies=allergies_list,
            search_type=search_type,
            limit=limit
        )
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
