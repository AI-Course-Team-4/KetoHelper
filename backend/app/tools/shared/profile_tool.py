"""
사용자 프로필 조회 도구
식단, 레스토랑, 채팅 에이전트에서 사용자 개인화 정보를 가져오는 공용 도구
"""

import asyncio
from typing import Dict, Any, List, Optional
from app.core.database import supabase_admin
import logging

logger = logging.getLogger(__name__)

class UserProfileTool:
    """사용자 프로필 조회 및 관리 도구"""
    
    def __init__(self):
        """초기화"""
        self.client = supabase_admin
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 전체 프로필 정보 조회 (알레르기, 비선호 재료, 목표 포함)
        
        Args:
            user_id (str): 사용자 ID
            
        Returns:
            Dict[str, Any]: 프로필 정보
            {
                "success": bool,
                "profile": {
                    "id": str,
                    "nickname": str,
                    "email": str,
                    "goals_kcal": int,
                    "goals_carbs_g": int,
                    "selected_allergy_ids": List[int],
                    "selected_dislike_ids": List[int], 
                    "allergy_names": List[str],
                    "dislike_names": List[str],
                    "trial_end_at": str,
                    "access_state": str
                },
                "error": str (only if success=False)
            }
        """
        logger.info(f"🔧 사용자 프로필 조회 시작: {user_id}")
        
        try:
            # 뷰를 사용하여 조인된 정보 조회
            response = self.client.table("user_profile_detailed").select("*").eq("id", user_id).execute()
            
            if not response.data:
                logger.warning(f"⚠️ 사용자를 찾을 수 없음: {user_id}")
                return {
                    "success": False,
                    "error": "사용자를 찾을 수 없습니다"
                }
            
            user_data = response.data[0]
            
            # null 값 처리
            user_data["selected_allergy_ids"] = user_data.get("selected_allergy_ids") or []
            user_data["selected_dislike_ids"] = user_data.get("selected_dislike_ids") or []
            user_data["allergy_names"] = user_data.get("allergy_names") or []
            user_data["dislike_names"] = user_data.get("dislike_names") or []
            
            logger.info(f"✅ 프로필 조회 완료: {user_data.get('nickname', '이름없음')}")
            
            return {
                "success": True,
                "profile": user_data
            }
            
        except Exception as e:
            logger.error(f"❌ 프로필 조회 실패: {e}")
            return {
                "success": False,
                "error": f"프로필 조회 중 오류 발생: {str(e)}"
            }
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 식단 선호도 정보만 조회 (식단 에이전트 최적화)
        
        Args:
            user_id (str): 사용자 ID
            
        Returns:
            Dict[str, Any]: 식단 선호도 정보
            {
                "success": bool,
                "preferences": {
                    "goals_kcal": int,
                    "goals_carbs_g": int,
                    "allergies": List[str],
                    "dislikes": List[str],
                    "allergy_ids": List[int],
                    "dislike_ids": List[int]
                },
                "error": str (only if success=False)
            }
        """
        logger.info(f"🔧 사용자 식단 선호도 조회 시작: {user_id}")
        
        try:
            # 먼저 뷰를 통한 조회 시도
            try:
                response = self.client.table("user_profile_detailed").select(
                    "goals_kcal, goals_carbs_g, selected_allergy_ids, selected_dislike_ids, allergy_names, dislike_names"
                ).eq("id", user_id).execute()
                
                if response.data:
                    data = response.data[0]
                    
                    # 디버깅 로그 추가
                    logger.info(f"🔍 뷰 조회 결과: allergy_ids={data.get('selected_allergy_ids')}, "
                               f"dislike_ids={data.get('selected_dislike_ids')}, "
                               f"allergy_names={data.get('allergy_names')}, "
                               f"dislike_names={data.get('dislike_names')}")
                    
                    preferences = {
                        "goals_kcal": data.get("goals_kcal"),
                        "goals_carbs_g": data.get("goals_carbs_g"),
                        "allergies": data.get("allergy_names") or [],
                        "dislikes": data.get("dislike_names") or [],
                        "allergy_ids": data.get("selected_allergy_ids") or [],
                        "dislike_ids": data.get("selected_dislike_ids") or []
                    }
                    
                    # 알레르기/비선호 정보가 비어있으면 직접 조회 시도
                    if not preferences["allergies"] and preferences["allergy_ids"]:
                        logger.warning(f"⚠️ 뷰에서 알레르기 이름을 가져오지 못함, 직접 조회 시도")
                        preferences["allergies"] = await self._get_allergy_names_by_ids(preferences["allergy_ids"])
                    
                    if not preferences["dislikes"] and preferences["dislike_ids"]:
                        logger.warning(f"⚠️ 뷰에서 비선호 이름을 가져오지 못함, 직접 조회 시도")
                        preferences["dislikes"] = await self._get_dislike_names_by_ids(preferences["dislike_ids"])
                    
                    logger.info(f"✅ 식단 선호도 조회 완료: 알레르기 {len(preferences['allergies'])}개, 비선호 {len(preferences['dislikes'])}개")
                    
                    return {
                        "success": True, 
                        "preferences": preferences
                    }
                
            except Exception as view_error:
                logger.warning(f"⚠️ 뷰 조회 실패, 직접 조회로 폴백: {view_error}")
            
            # 뷰 조회 실패 시 직접 조회
            logger.info(f"🔄 직접 조회로 폴백: {user_id}")
            
            # 사용자 기본 정보 조회
            user_response = self.client.table("users").select(
                "goals_kcal, goals_carbs_g, selected_allergy_ids, selected_dislike_ids"
            ).eq("id", user_id).execute()
            
            if not user_response.data:
                logger.warning(f"⚠️ 사용자를 찾을 수 없음: {user_id}")
                return {
                    "success": False,
                    "error": "사용자를 찾을 수 없습니다"
                }
            
            user_data = user_response.data[0]
            allergy_ids = user_data.get("selected_allergy_ids") or []
            dislike_ids = user_data.get("selected_dislike_ids") or []
            
            # 알레르기와 비선호 이름 직접 조회
            allergies = await self._get_allergy_names_by_ids(allergy_ids)
            dislikes = await self._get_dislike_names_by_ids(dislike_ids)
            
            preferences = {
                "goals_kcal": user_data.get("goals_kcal"),
                "goals_carbs_g": user_data.get("goals_carbs_g"),
                "allergies": allergies,
                "dislikes": dislikes,
                "allergy_ids": allergy_ids,
                "dislike_ids": dislike_ids
            }
            
            logger.info(f"✅ 직접 조회 완료: 알레르기 {len(preferences['allergies'])}개, 비선호 {len(preferences['dislikes'])}개")
            
            return {
                "success": True, 
                "preferences": preferences
            }
            
        except Exception as e:
            logger.error(f"❌ 식단 선호도 조회 실패: {e}")
            return {
                "success": False,
                "error": f"식단 선호도 조회 중 오류 발생: {str(e)}"
            }
    
    async def get_user_goals(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 목표 정보만 조회 (빠른 조회)
        
        Args:
            user_id (str): 사용자 ID
            
        Returns:
            Dict[str, Any]: 목표 정보
            {
                "success": bool,
                "goals": {
                    "kcal": int,
                    "carbs_g": int
                },
                "error": str (only if success=False)
            }
        """
        logger.info(f"🔧 사용자 목표 조회 시작: {user_id}")
        
        try:
            response = self.client.table("users").select("goals_kcal, goals_carbs_g").eq("id", user_id).execute()
            
            if not response.data:
                return {
                    "success": False,
                    "error": "사용자를 찾을 수 없습니다"
                }
            
            data = response.data[0]
            goals = {
                "kcal": data.get("goals_kcal"),
                "carbs_g": data.get("goals_carbs_g")
            }
            
            logger.info(f"✅ 목표 조회 완료: {goals['kcal']}kcal, {goals['carbs_g']}g 탄수화물")
            
            return {
                "success": True,
                "goals": goals
            }
            
        except Exception as e:
            logger.error(f"❌ 목표 조회 실패: {e}")
            return {
                "success": False,
                "error": f"목표 조회 중 오류 발생: {str(e)}"
            }
    
    async def get_user_restrictions(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 제한사항 정보만 조회 (알레르기, 비선호)
        
        Args:
            user_id (str): 사용자 ID
            
        Returns:
            Dict[str, Any]: 제한사항 정보
            {
                "success": bool,
                "restrictions": {
                    "allergies": List[str],
                    "dislikes": List[str]
                },
                "error": str (only if success=False)
            }
        """
        logger.info(f"🔧 사용자 제한사항 조회 시작: {user_id}")
        
        try:
            response = self.client.table("user_profile_detailed").select(
                "allergy_names, dislike_names"
            ).eq("id", user_id).execute()
            
            if not response.data:
                return {
                    "success": False,
                    "error": "사용자를 찾을 수 없습니다"
                }
            
            data = response.data[0]
            restrictions = {
                "allergies": data.get("allergy_names") or [],
                "dislikes": data.get("dislike_names") or []
            }
            
            logger.info(f"✅ 제한사항 조회 완료: 알레르기 {len(restrictions['allergies'])}개, 비선호 {len(restrictions['dislikes'])}개")
            
            return {
                "success": True,
                "restrictions": restrictions
            }
            
        except Exception as e:
            logger.error(f"❌ 제한사항 조회 실패: {e}")
            return {
                "success": False,
                "error": f"제한사항 조회 중 오류 발생: {str(e)}"
            }
    
    async def check_user_access(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 접근 권한 확인 (구독 상태, 체험 기간 등)
        
        Args:
            user_id (str): 사용자 ID
            
        Returns:
            Dict[str, Any]: 접근 권한 정보
            {
                "success": bool,
                "access": {
                    "state": str,  # trial, active, expired
                    "trial_end_at": str,
                    "paid_until": str,
                    "has_access": bool
                },
                "error": str (only if success=False)
            }
        """
        logger.info(f"🔧 사용자 접근 권한 확인 시작: {user_id}")
        
        try:
            response = self.client.table("users").select(
                "access_state, trial_end_at, paid_until"
            ).eq("id", user_id).execute()
            
            if not response.data:
                return {
                    "success": False,
                    "error": "사용자를 찾을 수 없습니다"
                }
            
            data = response.data[0]
            access = {
                "state": data.get("access_state", "trial"),
                "trial_end_at": data.get("trial_end_at"),
                "paid_until": data.get("paid_until"),
                "has_access": data.get("access_state") in ["trial", "active"]
            }
            
            logger.info(f"✅ 접근 권한 확인 완료: {access['state']} (접근가능: {access['has_access']})")
            
            return {
                "success": True,
                "access": access
            }
            
        except Exception as e:
            logger.error(f"❌ 접근 권한 확인 실패: {e}")
            return {
                "success": False,
                "error": f"접근 권한 확인 중 오류 발생: {str(e)}"
            }
    
    def format_preferences_for_prompt(self, preferences: Dict[str, Any]) -> str:
        """
        프롬프트용 선호도 텍스트 포맷팅
        
        Args:
            preferences (Dict[str, Any]): get_user_preferences 결과
            
        Returns:
            str: 프롬프트에 사용할 텍스트
        """
        if not preferences.get("success"):
            return "사용자 선호도 정보를 가져올 수 없습니다."
        
        prefs = preferences["preferences"]
        
        parts = []
        
        # 목표 칼로리/탄수화물
        if prefs.get("goals_kcal"):
            parts.append(f"목표 칼로리: {prefs['goals_kcal']}kcal")
        if prefs.get("goals_carbs_g"):
            parts.append(f"목표 탄수화물: {prefs['goals_carbs_g']}g")
        
        # 알레르기
        if prefs.get("allergies"):
            parts.append(f"알레르기: {', '.join(prefs['allergies'])}")
        else:
            parts.append("알레르기: 없음")
        
        # 비선호 재료
        if prefs.get("dislikes"):
            parts.append(f"비선호 재료: {', '.join(prefs['dislikes'])}")
        else:
            parts.append("비선호 재료: 없음")
        
        return " | ".join(parts)
    
    def filter_recipes_by_preferences(self, recipes: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        사용자 선호도에 따라 레시피 필터링
        
        Args:
            recipes (List[Dict[str, Any]]): 레시피 목록
            user_preferences (Dict[str, Any]): 사용자 선호도 정보
            
        Returns:
            List[Dict[str, Any]]: 필터링된 레시피 목록
        """
        if not user_preferences.get("success"):
            return recipes
        
        prefs = user_preferences["preferences"]
        user_allergies = set(prefs.get("allergies", []))
        user_dislikes = set(prefs.get("dislikes", []))
        
        filtered_recipes = []
        
        for recipe in recipes:
            # 알레르기 체크
            recipe_allergens = set(recipe.get("allergens", []))
            if user_allergies and recipe_allergens.intersection(user_allergies):
                logger.info(f"🚫 알레르기로 인해 제외: {recipe.get('title', 'Unknown')} - {recipe_allergens.intersection(user_allergies)}")
                continue
            
            # 비선호 재료 체크
            ingredients_data = recipe.get("ingredients", [])
            
            # ingredients가 문자열인 경우 JSON 파싱
            if isinstance(ingredients_data, str):
                try:
                    import json
                    ingredients_data = json.loads(ingredients_data)
                except (json.JSONDecodeError, ValueError):
                    logger.warning(f"⚠️ ingredients 파싱 실패: {recipe.get('title', 'Unknown')} - {ingredients_data}")
                    ingredients_data = []
            
            recipe_ingredients = set(ingredients_data)
            if user_dislikes and recipe_ingredients.intersection(user_dislikes):
                logger.info(f"🚫 비선호 재료로 인해 제외: {recipe.get('title', 'Unknown')} - {recipe_ingredients.intersection(user_dislikes)}")
                continue
            
            # 필터링 통과
            filtered_recipes.append(recipe)
        
        logger.info(f"✅ 레시피 필터링 완료: {len(recipes)}개 → {len(filtered_recipes)}개")
        return filtered_recipes
    
    def get_recipe_exclusion_reasons(self, recipe: Dict[str, Any], user_preferences: Dict[str, Any]) -> List[str]:
        """
        레시피가 제외된 이유 반환
        
        Args:
            recipe (Dict[str, Any]): 레시피 정보
            user_preferences (Dict[str, Any]): 사용자 선호도 정보
            
        Returns:
            List[str]: 제외 이유 목록
        """
        if not user_preferences.get("success"):
            return []
        
        prefs = user_preferences["preferences"]
        user_allergies = set(prefs.get("allergies", []))
        user_dislikes = set(prefs.get("dislikes", []))
        
        reasons = []
        
        # 알레르기 체크
        recipe_allergens = set(recipe.get("allergens", []))
        allergy_conflicts = recipe_allergens.intersection(user_allergies)
        if allergy_conflicts:
            reasons.append(f"알레르기 성분 포함: {', '.join(allergy_conflicts)}")
        
        # 비선호 재료 체크
        recipe_ingredients = set(recipe.get("ingredients", []))
        dislike_conflicts = recipe_ingredients.intersection(user_dislikes)
        if dislike_conflicts:
            reasons.append(f"비선호 재료 포함: {', '.join(dislike_conflicts)}")
        
        return reasons
    
    async def _get_allergy_names_by_ids(self, allergy_ids: List[int]) -> List[str]:
        """
        알레르기 ID 목록으로부터 이름 목록 조회
        
        Args:
            allergy_ids (List[int]): 알레르기 ID 목록
            
        Returns:
            List[str]: 알레르기 이름 목록
        """
        if not allergy_ids:
            return []
        
        try:
            response = self.client.table("allergy_master").select("name").in_("id", allergy_ids).execute()
            
            if response.data:
                names = [item["name"] for item in response.data]
                logger.info(f"🔍 알레르기 이름 직접 조회 성공: {names}")
                return names
            else:
                logger.warning(f"⚠️ 알레르기 ID에 해당하는 이름을 찾을 수 없음: {allergy_ids}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 알레르기 이름 조회 실패: {e}")
            return []
    
    async def _get_dislike_names_by_ids(self, dislike_ids: List[int]) -> List[str]:
        """
        비선호 재료 ID 목록으로부터 이름 목록 조회
        
        Args:
            dislike_ids (List[int]): 비선호 재료 ID 목록
            
        Returns:
            List[str]: 비선호 재료 이름 목록
        """
        if not dislike_ids:
            return []
        
        try:
            response = self.client.table("dislike_ingredient_master").select("name").in_("id", dislike_ids).execute()
            
            if response.data:
                names = [item["name"] for item in response.data]
                logger.info(f"🔍 비선호 재료 이름 직접 조회 성공: {names}")
                return names
            else:
                logger.warning(f"⚠️ 비선호 재료 ID에 해당하는 이름을 찾을 수 없음: {dislike_ids}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 비선호 재료 이름 조회 실패: {e}")
            return []

# 전역 인스턴스
user_profile_tool = UserProfileTool()
