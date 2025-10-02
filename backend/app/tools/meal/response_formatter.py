"""
app/tools/meal/response_formatter.py
식단표와 레시피 응답 포맷팅 도구
Orchestrator의 포맷팅 로직을 이동
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class MealResponseFormatter:
    """식단표 및 레시피 응답 포맷터"""
    
    def __init__(self):
        self.slot_names = {
            "breakfast": "아침",
            "lunch": "점심", 
            "dinner": "저녁",
            "snack": "간식"
        }
    
    def format_meal_plan(self, meal_plan: Dict[str, Any], days: int) -> str:
        """
        식단표를 하루별로 분리된 HTML 테이블(그레이 톤)로 포맷팅
        
        Args:
            meal_plan (Dict): 생성된 식단표 데이터
            days (int): 요청된 일수
            
        Returns:
            str: 포맷된 응답 텍스트
        """
        if not meal_plan or not meal_plan.get("days"):
            return "죄송합니다. 식단표 생성에 실패했습니다. 다시 시도해주세요."
        
        # 일수 텍스트 생성
        day_text = "일" if days == 1 else f"{days}일"
        
        # 제목
        response_text = f"""<span style=\"font-weight: bold; color: #374151;\"><b>{day_text} 키토 식단표</b></span><br>"""
        
        # 요청된 일수만큼만 출력 (하루씩 개별 테이블)
        meal_days = meal_plan.get("days", [])[:days]
        
        for day_idx, day_meals in enumerate(meal_days, 1):
            # 섹션 타이틀 (1일차, 2일차 ...)
            response_text += f"""
<div style=\"font-weight: 700; color: #16a34a; margin-top: 10px;\">{day_idx}일차</div>
<table style=\"border-collapse: collapse; width: 100%; margin: 8px 0;\">"""
            
            # 각 끼니별 행
            for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                label = self.slot_names[slot]
                title = "-"
                if slot in day_meals and day_meals[slot]:
                    meal = day_meals[slot]
                    title = meal.get('title', '메뉴 없음') or '메뉴 없음'
                    
                    # 영양 정보 추가 (있을 경우)
                    nutrition_info = []
                    if meal.get('carbs'):
                        nutrition_info.append(f"탄수화물 {meal['carbs']}g")
                    if meal.get('calories'):
                        nutrition_info.append(f"{meal['calories']}kcal")
                    if nutrition_info:
                        title += f" ({', '.join(nutrition_info)})"
                
                response_text += f"""
  <tr>
    <td style=\"border: 1px solid #ddd; padding: 8px; background-color: #f8f9fa; font-weight: bold; width: 22%; color: #374151;\">{label}</td>
    <td style=\"border: 1px solid #ddd; padding: 8px; color: #111827;\">{title}</td>
  </tr>"""
            
            response_text += """
</table>"""
            
            # 일차별 추천 이유 추가 (AI가 생성한 이유 사용)
            day_reasons = meal_plan.get("day_reasons", [])
            
            if day_idx <= len(day_reasons):
                reason = day_reasons[day_idx - 1]
                response_text += f"""<div style=\"font-size: 0.9em; color: #6b7280; margin: 6px 0; padding: 8px; background-color: #f9fafb; border-radius: 4px;\"><strong>추천 이유:</strong> {reason}</div>"""
        
        # 핵심 조언 추가 (그레이 박스)
        notes = meal_plan.get("notes", [])
        if notes:
            response_text += """
<ul style=\"background-color: #f8f9fa; padding: 14px; border-radius: 8px; margin: 10px 0; color: #374151; display: flex; flex-direction: column; justify-content: center;\">\n<strong>키토 팁</strong><br>"""
            for note in notes[:3]:  # 최대 3개만
                response_text += f"<li>→ {note}</li>"
            response_text += """
</ul>"""
        
        # 총 영양 정보 (그레이 박스)
        if meal_plan.get("total_nutrition"):
            nutrition = meal_plan["total_nutrition"]
            response_text += """
<div style=\"background-color: #f8f9fa; padding: 14px; border-radius: 8px; margin: 10px 0; color: #374151; display: flex; flex-direction: column; justify-content: center;\">\n<strong>일일 평균 영양 정보</strong><br>"""
            if nutrition.get("calories"):
                response_text += f"• 칼로리: {nutrition['calories']}kcal<br>"
            if nutrition.get("carbs"):
                response_text += f"• 탄수화물: {nutrition['carbs']}g<br>"
            if nutrition.get("protein"):
                response_text += f"• 단백질: {nutrition['protein']}g<br>"
            if nutrition.get("fat"):
                response_text += f"• 지방: {nutrition['fat']}g<br>"
            response_text += """
</div>"""
        
        # 캘린더 저장 안내 (그레이 박스)
        response_text += """
<div style=\"background-color: #f8f9fa; padding: 14px; border-radius: 8px; margin: 10px 0; color: #374151; display: flex; flex-direction: column; justify-content: center;\"><strong>캘린더 저장</strong><br>이 식단표를 캘린더에 저장하시려면 캘린더에 저장해줘! 라고 말씀해주세요!</div>"""
        
        return response_text
    
    def format_recipe(self, recipe: str, query: str) -> str:
        """
        레시피를 사용자 친화적인 텍스트로 포맷팅
        
        Args:
            recipe (str): 생성된 레시피 텍스트
            query (str): 원래 요청 메시지
            
        Returns:
            str: 포맷된 응답 텍스트
        """
        if not recipe:
            return f"죄송합니다. '{query}' 레시피 생성에 실패했습니다. 다시 시도해주세요."
        
        # 레시피가 이미 잘 포맷되어 있으면 그대로 반환
        if recipe.startswith("##") or recipe.startswith("🍳"):
            return recipe
        
        # 기본 포맷 추가
        formatted = f"**{query} 레시피**\n\n"
        formatted += recipe
        
        # 추가 안내 문구
        if "재료" in recipe and "만드는 법" in recipe:
            formatted += "\n\n**키토 팁**: 탄수화물을 최소화하면서도 맛있게 즐기세요!"
        
        return formatted
    
    def format_calendar_data(self, meal_plan: Dict[str, Any], start_date: str) -> List[Dict[str, Any]]:
        """
        식단표를 캘린더 저장용 데이터로 변환
        
        Args:
            meal_plan (Dict): 식단표 데이터
            start_date (str): 시작 날짜 (YYYY-MM-DD)
            
        Returns:
            List[Dict]: 캘린더 저장용 데이터 리스트
        """
        calendar_data = []
        
        try:
            from datetime import datetime, timedelta
            start = datetime.strptime(start_date, "%Y-%m-%d")
            
            for day_idx, day_meals in enumerate(meal_plan.get("days", [])):
                current_date = start + timedelta(days=day_idx)
                date_str = current_date.strftime("%Y-%m-%d")
                
                for slot, meal in day_meals.items():
                    if slot in ['breakfast', 'lunch', 'dinner', 'snack'] and meal:
                        calendar_entry = {
                            "date": date_str,
                            "meal_type": slot,
                            "title": meal.get("title", ""),
                            "description": self._build_meal_description(meal),
                            "nutrition": {
                                "calories": meal.get("calories"),
                                "carbs": meal.get("carbs"),
                                "protein": meal.get("protein"),
                                "fat": meal.get("fat")
                            }
                        }
                        calendar_data.append(calendar_entry)
        
        except Exception as e:
            print(f"❌ 캘린더 데이터 변환 실패: {e}")
            return []
        
        return calendar_data
    
    def _build_meal_description(self, meal: Dict[str, Any]) -> str:
        """
        식사 상세 설명 생성
        
        Args:
            meal (Dict): 식사 데이터
            
        Returns:
            str: 설명 텍스트
        """
        parts = []
        
        if meal.get("description"):
            parts.append(meal["description"])
        
        if meal.get("ingredients"):
            if isinstance(meal["ingredients"], list):
                parts.append(f"재료: {', '.join(meal['ingredients'])}")
            else:
                parts.append(f"재료: {meal['ingredients']}")
        
        nutrition_info = []
        if meal.get("calories"):
            nutrition_info.append(f"{meal['calories']}kcal")
        if meal.get("carbs"):
            nutrition_info.append(f"탄수화물 {meal['carbs']}g")
        if meal.get("protein"):
            nutrition_info.append(f"단백질 {meal['protein']}g")
        if meal.get("fat"):
            nutrition_info.append(f"지방 {meal['fat']}g")
        
        if nutrition_info:
            parts.append(f"영양: {', '.join(nutrition_info)}")
        
        return " | ".join(parts) if parts else ""
    
    def format_error_response(self, error_type: str, context: Dict[str, Any] = None) -> str:
        """
        에러 상황에 맞는 응답 생성
        
        Args:
            error_type (str): 에러 타입
            context (Dict): 추가 컨텍스트
            
        Returns:
            str: 에러 응답 텍스트
        """
        error_responses = {
            "no_days": "몇 일치 식단표를 원하시는지 구체적으로 말씀해주세요. (예: 5일치, 일주일치, 3일치)",
            "generation_failed": "죄송합니다. 식단표 생성 중 오류가 발생했습니다. 다시 시도해주세요.",
            "recipe_failed": "죄송합니다. 레시피 생성 중 오류가 발생했습니다. 다시 시도해주세요.",
            "profile_not_found": "사용자 프로필을 찾을 수 없습니다. 프로필을 먼저 설정해주세요.",
            "access_denied": "식단 생성 권한이 없습니다. 구독이 필요합니다.",
            "invalid_request": "올바르지 않은 요청입니다. 다시 시도해주세요."
        }
        
        base_response = error_responses.get(error_type, "죄송합니다. 요청을 처리할 수 없습니다.")
        
        # 컨텍스트 추가
        if context:
            if context.get("suggestion"):
                base_response += f"\n**제안**: {context['suggestion']}"
            if context.get("help_text"):
                base_response += f"\n도움말: {context['help_text']}"
        
        return base_response