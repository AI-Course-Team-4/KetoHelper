# main.py
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Diet Planner API", version="1.0.0")

class Prefs(BaseModel):
    hard_ban: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    dislike: Optional[List[str]] = []

class PlanRequest(BaseModel):
    start_date: str  # "YYYY-MM-DD"
    end_date: str
    strictness: str  # "easy"|"standard"|"strict"|"ultra"
    meals_per_day: int = 3
    prefs: Optional[Prefs] = None

@app.get("/v1/healthz")
def healthz():
    return {"ok": True}

@app.get("/v1/locations/nearby")
def nearby(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: int = 100,
    limit: int = 10,
    min_score: int = 70,
):
    # 일단 더미 데이터(서버 열기용)
    return {
        "items": [{
            "restaurant_id": "r_001",
            "restaurant_name": "김가네",
            "distance_m": 85,
            "menu": {"menu_id": "m_101", "name": "두부제육", "keto_score": 78, "allergen_flags": []},
            "address": "서울시 강남구 ...",
            "coords": {"lat": lat, "lng": lng}
        }],
        "meta": {"fallback": "none", "items_found": 1}
    }

@app.post("/v1/plans/generate")
def generate_plan(req: PlanRequest):
    # 일단 더미 응답(서버 열기용)
    return {
        "data": {
            "meta": {
                "days": 7,
                "strictness": req.strictness,
                "targets": {"net_carbs_g_per_day": 20}
            },
            "plan": [{
                "date": req.start_date,
                "meals": [
                    {"name": "연두부 샐러드", "keto_score": 86, "net_carbs_g": 6, "alt": "훈제오리 샐러드"},
                    {"name": "삼겹 구이 + 채소", "keto_score": 90, "net_carbs_g": 4},
                    {"name": "버섯계란 스크램블", "keto_score": 82, "net_carbs_g": 5}
                ],
                "compliance": {"net_carbs_total_g": 15, "violations": []}
            }],
            "shopping_list": [
                {"category": "Meat", "item": "삼겹살", "qty": "1.2kg"},
                {"category": "Vegetable", "item": "양상추", "qty": "4"}
            ]
        }
    }
