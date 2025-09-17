"""
식단 계획 API 엔드포인트
캘린더/플래너 기능 및 식단표 생성
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import date, timedelta
from icalendar import Calendar, Event
from fastapi.responses import Response
import pytz
from datetime import datetime

from app.core.database import get_db
from app.models.schemas import (
    PlanCreate, PlanUpdate, PlanResponse, MealPlanRequest, 
    MealPlanResponse, StatsSummary
)
from app.models.database_models import Plan, Recipe
from app.agents.meal_planner import MealPlannerAgent

router = APIRouter(prefix="/plans", tags=["plans"])

@router.get("/range", response_model=List[PlanResponse])
async def get_plans_range(
    start: date = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end: date = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    user_id: str = Query(..., description="사용자 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    특정 기간의 식단 계획 조회
    캘린더 UI에서 사용
    """
    try:
        result = await db.execute(
            select(Plan)
            .where(
                and_(
                    Plan.user_id == user_id,
                    Plan.date >= start,
                    Plan.date <= end
                )
            )
            .order_by(Plan.date, Plan.slot)
        )
        plans = result.scalars().all()
        
        return [PlanResponse.from_orm(plan) for plan in plans]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식단 계획 조회 중 오류 발생: {str(e)}"
        )

@router.post("/item", response_model=PlanResponse)
async def create_or_update_plan(
    plan: PlanCreate,
    user_id: str = Query(..., description="사용자 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    식단 계획 추가/수정
    동일한 날짜/슬롯이 있으면 업데이트 (upsert)
    """
    try:
        # 기존 계획 확인
        existing_result = await db.execute(
            select(Plan)
            .where(
                and_(
                    Plan.user_id == user_id,
                    Plan.date == plan.date,
                    Plan.slot == plan.slot
                )
            )
        )
        existing_plan = existing_result.scalar_one_or_none()
        
        if existing_plan:
            # 업데이트
            for field, value in plan.dict(exclude_unset=True).items():
                setattr(existing_plan, field, value)
            existing_plan.updated_at = datetime.now()
            
            await db.commit()
            await db.refresh(existing_plan)
            return PlanResponse.from_orm(existing_plan)
        else:
            # 새로 생성
            new_plan = Plan(
                user_id=user_id,
                **plan.dict()
            )
            db.add(new_plan)
            await db.commit()
            await db.refresh(new_plan)
            return PlanResponse.from_orm(new_plan)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"식단 계획 저장 중 오류 발생: {str(e)}"
        )

@router.patch("/item/{plan_id}", response_model=PlanResponse)
async def update_plan_item(
    plan_id: str = Path(..., description="계획 ID"),
    update_data: PlanUpdate = None,
    user_id: str = Query(..., description="사용자 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    식단 계획 부분 업데이트
    주로 완료/스킵 상태 변경에 사용
    """
    try:
        result = await db.execute(
            select(Plan)
            .where(
                and_(
                    Plan.id == plan_id,
                    Plan.user_id == user_id
                )
            )
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="식단 계획을 찾을 수 없습니다")
        
        # 업데이트할 필드들 적용
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(plan, field, value)
        
        plan.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(plan)
        
        return PlanResponse.from_orm(plan)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"식단 계획 업데이트 중 오류 발생: {str(e)}"
        )

@router.delete("/item/{plan_id}")
async def delete_plan_item(
    plan_id: str = Path(..., description="계획 ID"),
    user_id: str = Query(..., description="사용자 ID"),
    db: AsyncSession = Depends(get_db)
):
    """식단 계획 삭제"""
    try:
        result = await db.execute(
            select(Plan)
            .where(
                and_(
                    Plan.id == plan_id,
                    Plan.user_id == user_id
                )
            )
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="식단 계획을 찾을 수 없습니다")
        
        await db.delete(plan)
        await db.commit()
        
        return {"message": "식단 계획이 삭제되었습니다"}
        
    except Exception as e:
        await db.rollback()
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

@router.post("/commit")
async def commit_meal_plan(
    meal_plan: MealPlanResponse,
    user_id: str = Query(..., description="사용자 ID"),
    start_date: date = Query(..., description="시작 날짜"),
    db: AsyncSession = Depends(get_db)
):
    """
    생성된 식단표를 캘린더에 일괄 저장
    """
    try:
        plans_to_create = []
        
        for day_idx, day_plan in enumerate(meal_plan.days):
            plan_date = start_date + timedelta(days=day_idx)
            
            for slot, item in day_plan.items():
                if item and slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                    plan = Plan(
                        user_id=user_id,
                        date=plan_date,
                        slot=slot,
                        type=item.get('type', 'recipe'),
                        ref_id=item.get('id', ''),
                        title=item.get('title', ''),
                        macros=item.get('macros'),
                        location=item.get('location')
                    )
                    plans_to_create.append(plan)
        
        # 기존 계획들 삭제 (충돌 방지)
        end_date = start_date + timedelta(days=len(meal_plan.days) - 1)
        await db.execute(
            select(Plan).where(
                and_(
                    Plan.user_id == user_id,
                    Plan.date >= start_date,
                    Plan.date <= end_date
                )
            ).delete()
        )
        
        # 새 계획들 저장
        db.add_all(plans_to_create)
        await db.commit()
        
        return {
            "message": f"{len(plans_to_create)}개의 식단 계획이 저장되었습니다",
            "start_date": start_date,
            "end_date": end_date
        }
        
    except Exception as e:
        await db.rollback()
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
