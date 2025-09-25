"""
식단 계획 API 엔드포인트
캘린더/플래너 기능 및 식단표 생성
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import List, Optional
from datetime import date, timedelta
from icalendar import Calendar, Event
from fastapi.responses import Response
import pytz
from datetime import datetime
from supabase import create_client, Client
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.shared.models.schemas import (
    PlanCreate, PlanUpdate, PlanResponse, MealPlanRequest, 
    MealPlanResponse, StatsSummary
)
# database_models.py 삭제로 인해 직접 Supabase 테이블 사용
from app.agents.meal_planner import MealPlannerAgent
from app.tools.shared.profile_tool import user_profile_tool

router = APIRouter(prefix="/plans", tags=["plans"])

# Supabase 클라이언트 초기화
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)

@router.get("/range", response_model=List[PlanResponse])
async def get_plans_range(
    start: date = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end: date = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    user_id: str = Query(..., description="사용자 ID")
):
    """
    특정 기간의 식단 계획 조회 (meal_log 테이블 사용)
    캘린더 UI에서 사용
    """
    try:
        response = supabase.table('meal_log').select('*').eq('user_id', str(user_id)).gte('date', start.isoformat()).lte('date', end.isoformat()).order('date').execute()

        meal_logs = response.data

        # meal_log 데이터를 PlanResponse 형태로 변환
        plans = []
        for log in meal_logs:
            plan = {
                "id": str(log["id"]),
                "user_id": log["user_id"],
                "date": log["date"],
                "slot": log["meal_type"],  # meal_type을 slot으로 매핑
                "type": "recipe",  # 기본값
                "ref_id": str(log.get("mealplan_id", "")),
                "title": log.get("note", "식단 기록"),
                "location": None,
                "macros": None,
                "notes": log.get("note"),
                "status": "done" if log["eaten"] else "planned",
                "created_at": log["created_at"],
                "updated_at": log["updated_at"]
            }
            plans.append(plan)

        return plans

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식단 계획 조회 중 오류 발생: {str(e)}"
        )

@router.post("/item", response_model=PlanResponse)
async def create_or_update_plan(
    plan: PlanCreate,
    user_id: str = Query(..., description="사용자 ID")
):
    """
    식단 계획 추가/수정 (meal_log 테이블 사용)
    동일한 날짜/슬롯이 있으면 업데이트 (upsert)
    """
    try:
        # 기존 계획 확인
        existing_response = supabase.table('meal_log').select('*').eq('user_id', str(user_id)).eq('date', plan.date.isoformat()).eq('meal_type', plan.slot).execute()

        meal_log_data = {
            "user_id": str(user_id),
            "date": plan.date.isoformat(),
            "meal_type": plan.slot,
            "eaten": False,  # 기본값
            "note": plan.title or plan.notes,
            "updated_at": datetime.utcnow().isoformat()
        }

        if existing_response.data:
            # 업데이트
            existing_id = existing_response.data[0]["id"]
            response = supabase.table('meal_log').update(meal_log_data).eq('id', existing_id).execute()
            updated_log = response.data[0]
        else:
            # 새로 생성
            meal_log_data["created_at"] = datetime.utcnow().isoformat()
            response = supabase.table('meal_log').insert(meal_log_data).execute()
            updated_log = response.data[0]

        # PlanResponse 형태로 변환
        plan_response = {
            "id": str(updated_log["id"]),
            "user_id": updated_log["user_id"],
            "date": updated_log["date"],
            "slot": updated_log["meal_type"],
            "type": "recipe",
            "ref_id": str(updated_log.get("mealplan_id", "")),
            "title": updated_log.get("note", "식단 기록"),
            "location": None,
            "macros": None,
            "notes": updated_log.get("note"),
            "status": "done" if updated_log["eaten"] else "planned",
            "created_at": updated_log["created_at"],
            "updated_at": updated_log["updated_at"]
        }

        return plan_response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식단 계획 저장 중 오류 발생: {str(e)}"
        )

@router.patch("/item/{plan_id}", response_model=PlanResponse)
async def update_plan_item(
    plan_id: str = Path(..., description="계획 ID"),
    update_data: PlanUpdate = None,
    user_id: str = Query(..., description="사용자 ID")
):
    """
    식단 계획 부분 업데이트 (meal_log 테이블 사용)
    주로 완료/스킵 상태 변경에 사용
    """
    try:
        # 기존 기록 확인
        existing_response = supabase.table('meal_log').select('*').eq('id', plan_id).eq('user_id', str(user_id)).execute()

        if not existing_response.data:
            raise HTTPException(status_code=404, detail="식단 계획을 찾을 수 없습니다")

        update_fields = {}
        if update_data.status:
            if update_data.status == "done":
                update_fields["eaten"] = True
            elif update_data.status in ["planned", "skipped"]:
                update_fields["eaten"] = False

        if update_data.notes:
            update_fields["note"] = update_data.notes

        update_fields["updated_at"] = datetime.utcnow().isoformat()

        response = supabase.table('meal_log').update(update_fields).eq('id', plan_id).execute()
        updated_log = response.data[0]

        # PlanResponse 형태로 변환
        plan_response = {
            "id": str(updated_log["id"]),
            "user_id": updated_log["user_id"],
            "date": updated_log["date"],
            "slot": updated_log["meal_type"],
            "type": "recipe",
            "ref_id": str(updated_log.get("mealplan_id", "")),
            "title": updated_log.get("note", "식단 기록"),
            "location": None,
            "macros": None,
            "notes": updated_log.get("note"),
            "status": "done" if updated_log["eaten"] else "planned",
            "created_at": updated_log["created_at"],
            "updated_at": updated_log["updated_at"]
        }

        return plan_response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식단 계획 업데이트 중 오류 발생: {str(e)}"
        )

@router.delete("/item/{plan_id}")
async def delete_plan_item(
    plan_id: str = Path(..., description="계획 ID"),
    user_id: str = Query(..., description="사용자 ID")
):
    """식단 계획 삭제 (meal_log 테이블)"""
    try:
        # 기존 기록 확인
        existing_response = supabase.table('meal_log').select('*').eq('id', plan_id).eq('user_id', str(user_id)).execute()

        if not existing_response.data:
            raise HTTPException(status_code=404, detail="식단 계획을 찾을 수 없습니다")

        supabase.table('meal_log').delete().eq('id', plan_id).execute()

        return {"message": "식단 계획이 삭제되었습니다"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식단 계획 삭제 중 오류 발생: {str(e)}"
        )

@router.post("/generate", response_model=MealPlanResponse)
async def generate_meal_plan(
    request: MealPlanRequest,
    user_id: str = Query(..., description="사용자 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    7일 식단표 자동 생성
    LangGraph 에이전트를 통한 AI 기반 계획 생성
    """
    try:
        meal_planner = MealPlannerAgent()
        
        # AI를 통한 식단표 생성
        meal_plan = await meal_planner.generate_meal_plan(
            days=request.days,
            kcal_target=request.kcal_target,
            carbs_max=request.carbs_max,
            allergies=request.allergies,
            dislikes=request.dislikes,
            user_id=user_id
        )
        
        return MealPlanResponse(**meal_plan)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식단표 생성 중 오류 발생: {str(e)}"
        )

@router.post("/generate/personalized", response_model=MealPlanResponse)
async def generate_personalized_meal_plan(
    user_id: str = Query(..., description="사용자 ID"),
    days: int = Query(7, description="생성할 일수"),
    db: AsyncSession = Depends(get_db)
):
    """
    개인화된 7일 식단표 자동 생성
    사용자 프로필(알레르기, 비선호, 목표)을 자동으로 반영
    """
    try:
        meal_planner = MealPlannerAgent()
        
        # 개인화된 식단표 생성 (프로필 자동 적용)
        meal_plan = await meal_planner.generate_personalized_meal_plan(
            user_id=user_id,
            days=days
        )
        
        return MealPlanResponse(**meal_plan)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"개인화 식단표 생성 중 오류 발생: {str(e)}"
        )

@router.post("/generate/with-access-check", response_model=dict)
async def generate_meal_plan_with_access_check(
    user_id: str = Query(..., description="사용자 ID"),
    days: int = Query(7, description="생성할 일수"),
    db: AsyncSession = Depends(get_db)
):
    """
    접근 권한 확인 후 개인화된 식단표 생성
    구독/체험 상태를 확인하고 권한이 있는 경우에만 생성
    """
    try:
        meal_planner = MealPlannerAgent()
        
        # 접근 권한 확인 및 식단표 생성
        result = await meal_planner.check_user_access_and_generate(
            user_id=user_id,
            request_type="meal_plan",
            days=days
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=403,
                detail=result["error"]
            )
        
        return {
            "success": True,
            "meal_plan": result["data"],
            "access_info": result["access_info"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"권한 확인 식단표 생성 중 오류 발생: {str(e)}"
        )

@router.post("/commit")
async def commit_meal_plan(
    meal_plan: MealPlanResponse,
    user_id: str = Query(..., description="사용자 ID"),
    start_date: date = Query(..., description="시작 날짜")
):
    """
    생성된 식단표를 캘린더에 일괄 저장 (meal_log 테이블 사용)
    """
    try:
        print(f"🔍 [DEBUG] commit_meal_plan 호출됨")
        print(f"🔍 [DEBUG] user_id: {user_id}")
        print(f"🔍 [DEBUG] start_date: {start_date}")
        print(f"🔍 [DEBUG] meal_plan 타입: {type(meal_plan)}")
        print(f"🔍 [DEBUG] meal_plan.days 타입: {type(meal_plan.days)}")
        print(f"🔍 [DEBUG] meal_plan.days 길이: {len(meal_plan.days) if hasattr(meal_plan.days, '__len__') else 'N/A'}")

        meal_logs_to_create = []

        for day_idx, day_plan in enumerate(meal_plan.days):
            plan_date = start_date + timedelta(days=day_idx)
            print(f"🔍 [DEBUG] Day {day_idx + 1} ({plan_date}): {type(day_plan)} = {day_plan}")

            try:
                for slot, item in day_plan.items():
                    print(f"🔍 [DEBUG] 처리 중 슬롯: '{slot}', 아이템: {item}")

                    if item and slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                        print(f"🔍 [DEBUG] 슬롯 '{slot}' 아이템 타입: {type(item)}, 값: {item}")

                        # item이 문자열인지 딕셔너리인지 확인 후 처리
                        if isinstance(item, str):
                            meal_title = item
                        elif isinstance(item, dict):
                            meal_title = item.get('title', '') or str(item)
                        else:
                            meal_title = str(item) if item else ''

                        print(f"🔍 [DEBUG] 최종 meal_title: '{meal_title}'")

                        meal_log = {
                            "user_id": str(user_id),
                            "date": plan_date.isoformat(),
                            "meal_type": slot,
                            "eaten": False,  # 기본값
                            "note": meal_title,
                            "created_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                        meal_logs_to_create.append(meal_log)
                        print(f"🔍 [DEBUG] meal_log 추가됨: {meal_log}")
                    else:
                        print(f"🔍 [DEBUG] 슬롯 '{slot}' 건너뜀 - 아이템: {item}")

            except Exception as day_error:
                print(f"❌ [ERROR] Day {day_idx + 1} 처리 중 오류: {day_error}")
                raise day_error

        print(f"🔍 [DEBUG] 생성된 meal_logs_to_create 개수: {len(meal_logs_to_create)}")
        for i, log in enumerate(meal_logs_to_create):
            print(f"🔍 [DEBUG] meal_log[{i}]: {log}")

        # 기존 계획들 삭제 (충돌 방지)
        end_date = start_date + timedelta(days=len(meal_plan.days) - 1)
        print(f"🔍 [DEBUG] 기존 데이터 삭제: {start_date} ~ {end_date}")
        supabase.table('meal_log').delete().eq('user_id', str(user_id)).gte('date', start_date.isoformat()).lte('date', end_date.isoformat()).execute()

        # 새 계획들 저장
        if meal_logs_to_create:
            print(f"🔍 [DEBUG] Supabase에 {len(meal_logs_to_create)}개 데이터 저장 시도")
            result = supabase.table('meal_log').insert(meal_logs_to_create).execute()
            print(f"🔍 [DEBUG] Supabase 저장 결과: {result}")

        return {
            "message": f"{len(meal_logs_to_create)}개의 식단 계획이 저장되었습니다",
            "start_date": start_date,
            "end_date": end_date
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식단표 저장 중 오류 발생: {str(e)}"
        )

@router.get("/week/{start_date}/export.ics")
async def export_week_ics(
    start_date: date = Path(..., description="주 시작 날짜"),
    user_id: str = Query(..., description="사용자 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    한 주 식단 계획을 ICS 파일로 내보내기
    Google/Naver 캘린더에 가져오기 가능
    """
    try:
        end_date = start_date + timedelta(days=6)
        
        # 해당 주의 계획들 조회
        result = await db.execute(
            select(Plan)
            .where(
                and_(
                    Plan.user_id == user_id,
                    Plan.date >= start_date,
                    Plan.date <= end_date
                )
            )
            .order_by(Plan.date, Plan.slot)
        )
        plans = result.scalars().all()
        
        # ICS 캘린더 생성
        cal = Calendar()
        cal.add('prodid', '-//키토 코치//키토 식단 계획//KR')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        
        seoul = pytz.timezone('Asia/Seoul')
        
        for plan in plans:
            event = Event()
            
            # 제목 설정
            title = f"[키토] {plan.slot} - {plan.title}"
            event.add('summary', title)
            
            # 시간 설정 (슬롯별 기본 시간)
            slot_times = {
                'breakfast': 8,
                'lunch': 12,
                'dinner': 18,
                'snack': 15
            }
            
            start_time = seoul.localize(
                datetime.combine(plan.date, datetime.min.time()).replace(
                    hour=slot_times.get(plan.slot, 12)
                )
            )
            end_time = start_time + timedelta(hours=1)
            
            event.add('dtstart', start_time)
            event.add('dtend', end_time)
            
            # 설명 추가
            description = f"타입: {plan.type}\n"
            if plan.macros:
                description += f"칼로리: {plan.macros.get('kcal', 0)}kcal\n"
                description += f"탄수화물: {plan.macros.get('carb', 0)}g\n"
            if plan.notes:
                description += f"메모: {plan.notes}\n"
            
            event.add('description', description)
            
            # 위치 설정 (식당인 경우)
            if plan.location and plan.location.get('address'):
                event.add('location', plan.location['address'])
            
            cal.add_component(event)
        
        # ICS 파일 응답
        ics_content = cal.to_ical()
        
        return Response(
            content=ics_content,
            media_type='text/calendar',
            headers={
                'Content-Disposition': f'attachment; filename="keto_meal_plan_{start_date}.ics"'
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ICS 내보내기 중 오류 발생: {str(e)}"
        )

@router.get("/week/{start_date}/shopping-list")
async def get_shopping_list(
    start_date: date = Path(..., description="주 시작 날짜"),
    user_id: str = Query(..., description="사용자 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    한 주 레시피의 재료를 집계한 쇼핑리스트 생성
    """
    try:
        end_date = start_date + timedelta(days=6)
        
        # 레시피 타입의 계획들 조회
        result = await db.execute(
            select(Plan)
            .where(
                and_(
                    Plan.user_id == user_id,
                    Plan.date >= start_date,
                    Plan.date <= end_date,
                    Plan.type == 'recipe'
                )
            )
        )
        recipe_plans = result.scalars().all()
        
        # 레시피 정보 조회
        recipe_ids = [plan.ref_id for plan in recipe_plans]
        recipe_result = await db.execute(
            select(Recipe)
            .where(Recipe.id.in_(recipe_ids))
        )
        recipes = {str(recipe.id): recipe for recipe in recipe_result.scalars().all()}
        
        # 재료 집계
        ingredient_summary = {}
        
        for plan in recipe_plans:
            recipe = recipes.get(plan.ref_id)
            if recipe and recipe.ingredients:
                for ingredient in recipe.ingredients:
                    name = ingredient.get('name', '')
                    amount = ingredient.get('amount', 0)
                    unit = ingredient.get('unit', '')
                    
                    key = f"{name}_{unit}"
                    if key in ingredient_summary:
                        ingredient_summary[key]['amount'] += amount
                    else:
                        ingredient_summary[key] = {
                            'name': name,
                            'amount': amount,
                            'unit': unit,
                            'category': _categorize_ingredient(name)
                        }
        
        # 카테고리별 정렬
        categorized = {}
        for ingredient in ingredient_summary.values():
            category = ingredient['category']
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(ingredient)
        
        return {
            "week_start": start_date,
            "week_end": end_date,
            "total_recipes": len(recipe_plans),
            "shopping_list": categorized,
            "summary": {
                "total_items": len(ingredient_summary),
                "categories": list(categorized.keys())
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"쇼핑리스트 생성 중 오류 발생: {str(e)}"
        )

@router.get("/stats/{start_date}/{end_date}", response_model=StatsSummary)
async def get_plan_statistics(
    start_date: date = Path(..., description="시작 날짜"),
    end_date: date = Path(..., description="종료 날짜"),
    user_id: str = Query(..., description="사용자 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    식단 계획 실행 통계
    이행률, 평균 탄수화물, 외식 비중 등
    """
    try:
        result = await db.execute(
            select(Plan)
            .where(
                and_(
                    Plan.user_id == user_id,
                    Plan.date >= start_date,
                    Plan.date <= end_date
                )
            )
        )
        plans = result.scalars().all()
        
        if not plans:
            return StatsSummary(
                compliance_rate=0.0,
                avg_carbs=0.0,
                dining_out_ratio=0.0,
                total_days=0
            )
        
        # 통계 계산
        total_plans = len(plans)
        completed_plans = len([p for p in plans if p.status == 'done'])
        dining_out_plans = len([p for p in plans if p.type == 'place'])
        
        # 평균 탄수화물 계산
        total_carbs = 0
        carb_count = 0
        for plan in plans:
            if plan.status == 'done' and plan.macros and 'carb' in plan.macros:
                total_carbs += plan.macros['carb']
                carb_count += 1
        
        avg_carbs = total_carbs / carb_count if carb_count > 0 else 0
        
        return StatsSummary(
            compliance_rate=round((completed_plans / total_plans) * 100, 1),
            avg_carbs=round(avg_carbs, 1),
            dining_out_ratio=round((dining_out_plans / total_plans) * 100, 1),
            total_days=(end_date - start_date).days + 1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"통계 조회 중 오류 발생: {str(e)}"
        )

def _categorize_ingredient(name: str) -> str:
    """재료를 카테고리별로 분류"""
    meat_keywords = ['고기', '돼지', '소', '닭', '양', '오리', '삼겹살', '목살', '등심']
    vegetable_keywords = ['양파', '마늘', '생강', '배추', '상추', '시금치', '브로콜리', '양배추']
    seafood_keywords = ['생선', '연어', '참치', '새우', '조개', '오징어', '문어', '회']
    dairy_keywords = ['치즈', '버터', '우유', '요거트', '크림']
    seasoning_keywords = ['소금', '후추', '간장', '고추장', '된장', '참기름', '올리브오일']
    
    name_lower = name.lower()
    
    for keyword in meat_keywords:
        if keyword in name_lower:
            return '육류'
    
    for keyword in seafood_keywords:
        if keyword in name_lower:
            return '해산물'
    
    for keyword in vegetable_keywords:
        if keyword in name_lower:
            return '채소'
    
    for keyword in dairy_keywords:
        if keyword in name_lower:
            return '유제품'
    
    for keyword in seasoning_keywords:
        if keyword in name_lower:
            return '양념/조미료'
    
    return '기타'
