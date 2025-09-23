from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import supabase_admin
from app.core.jwt_utils import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])

# ==========================================
# Pydantic 모델들
# ==========================================

class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    goals_kcal: Optional[int] = None
    goals_carbs_g: Optional[int] = None
    selected_allergy_ids: Optional[List[int]] = None
    selected_dislike_ids: Optional[List[int]] = None

class UserProfileResponse(BaseModel):
    id: str
    email: str
    nickname: Optional[str]
    profile_image_url: Optional[str]
    goals_kcal: Optional[int]
    goals_carbs_g: Optional[int]
    selected_allergy_ids: List[int]
    selected_dislike_ids: List[int]
    allergy_names: List[str]
    dislike_names: List[str]

class AllergyMaster(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    severity_level: int

class DislikeMaster(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]

# ==========================================
# API 엔드포인트들
# ==========================================

@router.get("/master/allergies", response_model=List[AllergyMaster])
async def get_allergy_master():
    """사전 정의된 알레르기 목록 조회"""
    try:
        response = supabase_admin.table("allergy_master").select("*").order("category, name").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알레르기 목록 조회 실패: {str(e)}")

@router.get("/master/dislikes", response_model=List[DislikeMaster])
async def get_dislike_master():
    """사전 정의된 비선호 재료 목록 조회"""
    try:
        response = supabase_admin.table("dislike_ingredient_master").select("*").order("category, name").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비선호 재료 목록 조회 실패: {str(e)}")

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    """사용자 프로필 조회 (알레르기/비선호 정보 포함)"""
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    
    try:
        # 뷰를 사용하여 조인된 정보 조회
        response = supabase_admin.table("user_profile_detailed").select("*").eq("id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        user_data = response.data[0]
        
        # null 값 처리
        user_data["selected_allergy_ids"] = user_data.get("selected_allergy_ids") or []
        user_data["selected_dislike_ids"] = user_data.get("selected_dislike_ids") or []
        user_data["allergy_names"] = user_data.get("allergy_names") or []
        user_data["dislike_names"] = user_data.get("dislike_names") or []
        
        return UserProfileResponse(**user_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 조회 중 오류 발생: {str(e)}")

@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: str, 
    profile_update: UserProfileUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """사용자 프로필 업데이트"""
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    
    try:
        # 업데이트할 데이터 준비
        update_data = {}
        
        if profile_update.nickname is not None:
            update_data["nickname"] = profile_update.nickname
        if profile_update.goals_kcal is not None:
            update_data["goals_kcal"] = profile_update.goals_kcal
        if profile_update.goals_carbs_g is not None:
            update_data["goals_carbs_g"] = profile_update.goals_carbs_g
        if profile_update.selected_allergy_ids is not None:
            update_data["selected_allergy_ids"] = profile_update.selected_allergy_ids
        if profile_update.selected_dislike_ids is not None:
            update_data["selected_dislike_ids"] = profile_update.selected_dislike_ids
        
        if not update_data:
            raise HTTPException(status_code=400, detail="업데이트할 데이터가 없습니다")
        
        # 업데이트 실행
        update_response = supabase_admin.table("users").update(update_data).eq("id", user_id).execute()
        
        if not update_response.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 업데이트된 프로필 조회
        return await get_user_profile(user_id, current_user)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 업데이트 중 오류 발생: {str(e)}")

@router.post("/{user_id}/allergies/{allergy_id}")
async def add_allergy(user_id: str, allergy_id: int, current_user: dict = Depends(get_current_user)):
    """알레르기 추가"""
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    
    try:
        # 현재 사용자 정보 조회
        user_response = supabase_admin.table("users").select("selected_allergy_ids").eq("id", user_id).execute()
        
        if not user_response.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        current_allergies = user_response.data[0].get("selected_allergy_ids") or []
        
        # 이미 있는지 확인
        if allergy_id not in current_allergies:
            current_allergies.append(allergy_id)
            
            # 업데이트
            supabase_admin.table("users").update({
                "selected_allergy_ids": current_allergies
            }).eq("id", user_id).execute()
        
        return {"message": "알레르기가 추가되었습니다"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알레르기 추가 중 오류 발생: {str(e)}")

@router.delete("/{user_id}/allergies/{allergy_id}")
async def remove_allergy(user_id: str, allergy_id: int, current_user: dict = Depends(get_current_user)):
    """알레르기 제거"""
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    
    try:
        # 현재 사용자 정보 조회
        user_response = supabase_admin.table("users").select("selected_allergy_ids").eq("id", user_id).execute()
        
        if not user_response.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        current_allergies = user_response.data[0].get("selected_allergy_ids") or []
        
        # 제거
        if allergy_id in current_allergies:
            current_allergies.remove(allergy_id)
            
            # 업데이트
            supabase_admin.table("users").update({
                "selected_allergy_ids": current_allergies
            }).eq("id", user_id).execute()
        
        return {"message": "알레르기가 제거되었습니다"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알레르기 제거 중 오류 발생: {str(e)}")

@router.post("/{user_id}/dislikes/{dislike_id}")
async def add_dislike(user_id: str, dislike_id: int, current_user: dict = Depends(get_current_user)):
    """비선호 재료 추가"""
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    
    try:
        # 현재 사용자 정보 조회
        user_response = supabase_admin.table("users").select("selected_dislike_ids").eq("id", user_id).execute()
        
        if not user_response.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        current_dislikes = user_response.data[0].get("selected_dislike_ids") or []
        
        # 이미 있는지 확인
        if dislike_id not in current_dislikes:
            current_dislikes.append(dislike_id)
            
            # 업데이트
            supabase_admin.table("users").update({
                "selected_dislike_ids": current_dislikes
            }).eq("id", user_id).execute()
        
        return {"message": "비선호 재료가 추가되었습니다"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비선호 재료 추가 중 오류 발생: {str(e)}")

@router.delete("/{user_id}/dislikes/{dislike_id}")
async def remove_dislike(user_id: str, dislike_id: int, current_user: dict = Depends(get_current_user)):
    """비선호 재료 제거"""
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    
    try:
        # 현재 사용자 정보 조회
        user_response = supabase_admin.table("users").select("selected_dislike_ids").eq("id", user_id).execute()
        
        if not user_response.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        current_dislikes = user_response.data[0].get("selected_dislike_ids") or []
        
        # 제거
        if dislike_id in current_dislikes:
            current_dislikes.remove(dislike_id)
            
            # 업데이트
            supabase_admin.table("users").update({
                "selected_dislike_ids": current_dislikes
            }).eq("id", user_id).execute()
        
        return {"message": "비선호 재료가 제거되었습니다"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비선호 재료 제거 중 오류 발생: {str(e)}")
