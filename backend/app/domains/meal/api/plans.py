"""
식단 계획 API 엔드포인트
캘린더/플래너 기능 및 식단표 생성
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import List, Optional
from datetime import date, timedelta, datetime
from supabase import create_client, Client
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.shared.models.schemas import (
    PlanCreate, PlanUpdate, PlanResponse, MealPlanRequest, 
    MealPlanResponse, StatsSummary
)
# database_models.py 삭제로 인해 직접 Supabase 테이블 사용
from app.agents.meal_planner import MealPlannerAgent, DEFAULT_MEAL_PLAN_DAYS
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
        print(f"🔍 [DEBUG] plans/range API 호출: user_id={user_id}, start={start}, end={end}")
        response = supabase.table('meal_log').select('*').eq('user_id', str(user_id)).gte('date', start.isoformat()).lte('date', end.isoformat()).order('date').execute()

        meal_logs = response.data
        print(f"🔍 [DEBUG] meal_log 조회 결과: {len(meal_logs)}개 레코드")
        for i, log in enumerate(meal_logs[:3]):  # 처음 3개만 로그
            print(f"🔍 [DEBUG] meal_log[{i}]: {log}")

        # meal_log 데이터를 PlanResponse 형태로 변환
        plans = []
        for log in meal_logs:
            # URL 가져오기 시도
            recipe_url = None
            meal_title = log.get("note", "")
            
            # 방법 1: mealplan_id를 통한 조회
            if log.get("mealplan_id"):
                try:
                    # meal_plan_item에서 recipe_blob_id 찾기
                    plan_item_response = supabase.table('meal_plan_item').select('recipe_blob_id').eq('mealplan_id', log["mealplan_id"]).eq('meal_type', log["meal_type"]).eq('planned_date', log["date"]).limit(1).execute()
                    
                    if plan_item_response.data and len(plan_item_response.data) > 0:
                        recipe_blob_id = plan_item_response.data[0].get('recipe_blob_id')
                        
                        if recipe_blob_id:
                            # recipe_blob_emb에서 URL 찾기
                            recipe_response = supabase.table('recipe_blob_emb').select('url').eq('id', recipe_blob_id).limit(1).execute()
                            
                            if recipe_response.data and len(recipe_response.data) > 0:
                                recipe_url = recipe_response.data[0].get('url')
                except Exception:
                    pass
            
            # 방법 2: 제목으로 직접 검색 (mealplan_id가 없거나 방법 1 실패 시)
            if not recipe_url and meal_title:
                try:
                    # recipe_blob_emb에서 제목으로 직접 검색
                    title_response = supabase.table('recipe_blob_emb').select('url').eq('title', meal_title).limit(1).execute()
                    
                    if title_response.data and len(title_response.data) > 0:
                        recipe_url = title_response.data[0].get('url')
                except Exception:
                    pass
            
            plan = {
                "id": str(log["id"]),
                "user_id": log["user_id"],
                "date": log["date"],
                "slot": log["meal_type"],  # meal_type을 slot으로 매핑
                "type": "recipe",  # 기본값
                "ref_id": str(log.get("mealplan_id", "")),
                "title": log.get("note", "식단 기록"),
                "url": recipe_url,  # ✅ URL 추가
                "location": None,
                "macros": None,
                "notes": log.get("note"),
                "status": "done" if log["eaten"] else "planned",
                "created_at": log["created_at"],
                "updated_at": log["updated_at"]
            }
            plans.append(plan)

        print(f"🔍 [DEBUG] 변환된 plans: {len(plans)}개")
        for i, plan in enumerate(plans[:3]):  # 처음 3개만 로그
            print(f"🔍 [DEBUG] plan[{i}]: {plan}")
        
        return plans

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식단 계획 조회 중 오류 발생: {str(e)}"
        )

@router.get("/status")
async def get_save_status(
    user_id: str = Query(..., description="사용자 ID"),
    start: date = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    duration_days: int = Query(..., ge=1, le=365, description="기간(일)"),
):
    """간단 버전 저장 상태 확인: 기간 내 `meal_log` 존재 여부로 처리.

    - 존재하면 status=done
    - 없으면 status=processing
    """
    try:
        end = start + timedelta(days=duration_days)

        resp = supabase.table('meal_log') \
            .select('id,date') \
            .eq('user_id', str(user_id)) \
            .gte('date', start.isoformat()) \
            .lt('date', end.isoformat()) \
            .execute()

        rows = resp.data or []
        # 날짜별 최소 1건씩 저장되었는지 확인 (하루만 먼저 저장되는 상황 방지)
        distinct_days = {r.get('date') for r in rows if r.get('date')}
        done = len(distinct_days) >= duration_days
        return {
            "status": "done" if done else "processing",
            "found_count": len(rows),
            "distinct_days": len(distinct_days),
            "expected_days": duration_days,
            "range": {"start": start.isoformat(), "end": end.isoformat()}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 조회 중 오류: {str(e)}")

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
        # 사전 차단 로직 제거 - 부분 저장 로직으로 대체됨
        print("✅ plans.py 차단 로직 제거됨 - 부분 저장 로직 사용")

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

@router.delete("/all")
async def delete_all_plans(
    user_id: str = Query(..., description="사용자 ID")
):
    """사용자의 모든 식단 계획 삭제 (meal_log 테이블)"""
    try:
        print(f"🗑️ [DEBUG] 전체 삭제 요청: user_id={user_id}")
        
        # 기존 데이터 확인
        existing_response = supabase.table('meal_log').select('*').eq('user_id', str(user_id)).execute()
        existing_count = len(existing_response.data) if existing_response.data else 0
        
        print(f"🗑️ [DEBUG] 기존 데이터 개수: {existing_count}")
        
        if existing_count == 0:
            return {"message": "삭제할 식단 계획이 없습니다", "deleted_count": 0}

        # 모든 식단 계획 삭제
        delete_response = supabase.table('meal_log').delete().eq('user_id', str(user_id)).execute()
        
        print(f"🗑️ [DEBUG] 삭제 완료: {delete_response}")
        
        return {
            "message": f"모든 식단 계획이 삭제되었습니다 ({existing_count}개)",
            "deleted_count": existing_count
        }

    except Exception as e:
        print(f"❌ [ERROR] 전체 삭제 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"식단 계획 전체 삭제 중 오류 발생: {str(e)}"
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
    days: int = Query(DEFAULT_MEAL_PLAN_DAYS, description="생성할 일수"),
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
    days: int = Query(DEFAULT_MEAL_PLAN_DAYS, description="생성할 일수"),
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
        duration_days = max(1, len(meal_plan.days) if hasattr(meal_plan.days, '__len__') else 1)
        end_date = start_date + timedelta(days=duration_days - 1)
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
            "end_date": end_date,
            "duration_days": duration_days
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식단표 저장 중 오류 발생: {str(e)}"
        )

# 캘린더 페이지에서 입력한 텍스트를 식단으로 추가 (기존 생성 로직 재사용)
@router.post("/calendar/add_meal", response_model=PlanResponse)
async def add_meal_to_calendar(
    plan: PlanCreate,
    user_id: str = Query(..., description="사용자 ID")
):
    """
    캘린더 입력창에서 받은 단일 식단을 저장합니다.
    같은 날짜·끼니·user_id가 있으면 덮어쓰기(업서트),
    없으면 새로 추가합니다.
    """
    normalized_note = (plan.title or plan.notes or "").strip()
    if not normalized_note:
        raise HTTPException(status_code=400, detail="빈 입력은 저장할 수 없습니다")

    try:
        return await create_or_update_plan(plan=plan, user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"식단 저장 중 오류 발생: {str(e)}")
