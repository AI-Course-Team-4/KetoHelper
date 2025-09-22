"""
자연어 의도 분류기
사용자 입력을 분석하여 도메인별 에이전트로 라우팅
"""

from enum import Enum
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
import re

from app.core.config import settings


class Intent(Enum):
    """의도 분류 열거형"""
    MEAL_PLANNING = "meal_planning"      # 식단 계획/레시피 관련
    RESTAURANT_SEARCH = "restaurant_search"  # 식당 찾기 관련
    BOTH = "both"                       # 두 기능 모두 필요
    GENERAL = "general"                 # 일반 대화


class IntentClassifier:
    """자연어 의도 분류기"""
    
    def __init__(self):
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=settings.gemini_temperature
            )
        except Exception as e:
            print(f"Gemini AI 초기화 실패: {e}")
            self.llm = None
        
        # 키워드 기반 빠른 분류 규칙
        self.meal_keywords = [
            "레시피", "요리", "식단", "메뉴", "만들기", "조리법", "재료",
            "키토", "저탄수", "다이어트", "칼로리", "영양", "단백질", "탄수화물",
            "아침", "점심", "저녁", "간식", "식사", "해먹", "요리해"
        ]
        
        self.restaurant_keywords = [
            "식당", "맛집", "음식점", "카페", "레스토랑", "근처", "주변",
            "찾아", "추천", "배달", "포장", "예약", "위치", "거리",
            "갈만한", "먹을만한", "가게", "점포"
        ]
    
    async def classify_intent(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """
        사용자 입력의 의도를 분류
        
        Args:
            user_input: 사용자 입력 텍스트
            context: 이전 대화 맥락 (선택사항)
            
        Returns:
            의도 분류 결과와 확신도
        """
        
        # 1단계: 키워드 기반 빠른 분류
        quick_result = self._quick_classify(user_input)
        if quick_result["confidence"] > 0.8:
            return quick_result
        
        # 2단계: LLM 기반 정확한 분류
        llm_result = await self._llm_classify(user_input, context)
        
        # 결과 조합
        return self._combine_results(quick_result, llm_result)
    
    def _quick_classify(self, user_input: str) -> Dict[str, Any]:
        """키워드 기반 빠른 분류"""
        
        text = user_input.lower()
        
        # 키워드 카운트
        meal_count = sum(1 for keyword in self.meal_keywords if keyword in text)
        restaurant_count = sum(1 for keyword in self.restaurant_keywords if keyword in text)
        
        # 의도 결정
        if meal_count > 0 and restaurant_count > 0:
            intent = Intent.BOTH
            confidence = min(0.9, (meal_count + restaurant_count) * 0.3)
        elif meal_count > restaurant_count and meal_count > 0:
            intent = Intent.MEAL_PLANNING
            confidence = min(0.9, meal_count * 0.4)
        elif restaurant_count > meal_count and restaurant_count > 0:
            intent = Intent.RESTAURANT_SEARCH
            confidence = min(0.9, restaurant_count * 0.4)
        else:
            intent = Intent.GENERAL
            confidence = 0.3
        
        return {
            "intent": intent,
            "confidence": confidence,
            "method": "keyword",
            "keywords_found": {
                "meal": meal_count,
                "restaurant": restaurant_count
            }
        }
    
    async def _llm_classify(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """LLM 기반 정확한 분류"""
        
        prompt = f"""
사용자의 입력을 분석하여 다음 4가지 의도 중 하나로 분류해주세요:

1. MEAL_PLANNING: 키토 식단 계획, 레시피, 요리법, 영양 정보 관련
2. RESTAURANT_SEARCH: 주변 식당, 맛집 찾기, 음식점 추천 관련  
3. BOTH: 식단과 식당 정보 모두 필요한 경우
4. GENERAL: 위 카테고리에 해당하지 않는 일반 대화

이전 대화 맥락: {context}
사용자 입력: {user_input}

응답 형식 (JSON):
{{
    "intent": "MEAL_PLANNING|RESTAURANT_SEARCH|BOTH|GENERAL",
    "confidence": 0.0-1.0,
    "reasoning": "분류 근거"
}}
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            # JSON 파싱
            import json
            result = json.loads(response.content)
            
            return {
                "intent": Intent(result["intent"].lower()),
                "confidence": result["confidence"],
                "method": "llm",
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            # LLM 분류 실패 시 기본값 반환
            return {
                "intent": Intent.GENERAL,
                "confidence": 0.5,
                "method": "llm_fallback",
                "error": str(e)
            }
    
    def _combine_results(self, quick_result: Dict, llm_result: Dict) -> Dict[str, Any]:
        """키워드와 LLM 결과를 조합"""
        
        # 높은 확신도를 가진 결과 선택
        if quick_result["confidence"] > llm_result["confidence"]:
            primary = quick_result
            secondary = llm_result
        else:
            primary = llm_result
            secondary = quick_result
        
        return {
            "intent": primary["intent"],
            "confidence": primary["confidence"],
            "primary_method": primary["method"],
            "secondary_method": secondary["method"],
            "details": {
                "quick_classification": quick_result,
                "llm_classification": llm_result
            }
        }
    
    def extract_slots(self, user_input: str, intent: Intent) -> Dict[str, Any]:
        """의도별 슬롯 추출"""
        
        slots = {}
        
        if intent in [Intent.MEAL_PLANNING, Intent.BOTH]:
            slots.update(self._extract_meal_slots(user_input))
        
        if intent in [Intent.RESTAURANT_SEARCH, Intent.BOTH]:
            slots.update(self._extract_restaurant_slots(user_input))
        
        return slots
    
    def _extract_meal_slots(self, text: str) -> Dict[str, Any]:
        """식단 관련 슬롯 추출"""
        
        slots = {}
        
        # 시간대 추출
        time_patterns = {
            "아침": ["아침", "조식", "morning"],
            "점심": ["점심", "중식", "lunch"],
            "저녁": ["저녁", "석식", "dinner"],
            "간식": ["간식", "snack"]
        }
        
        for time_key, patterns in time_patterns.items():
            if any(pattern in text for pattern in patterns):
                slots["meal_time"] = time_key
                break
        
        # 칼로리 추출
        calorie_match = re.search(r'(\d+)\s*[칼킬]?[칼로리리]', text)
        if calorie_match:
            slots["target_calories"] = int(calorie_match.group(1))
        
        # 알레르기/제외 재료
        exclude_patterns = ["빼고", "제외", "없이", "알레르기"]
        if any(pattern in text for pattern in exclude_patterns):
            slots["has_restrictions"] = True
        
        return slots
    
    def _extract_restaurant_slots(self, text: str) -> Dict[str, Any]:
        """식당 관련 슬롯 추출"""
        
        slots = {}
        
        # 거리 추출
        distance_match = re.search(r'(\d+)\s*[킬미]?[미터로]', text)
        if distance_match:
            distance = int(distance_match.group(1))
            if "킬로" in text or "km" in text:
                slots["radius_km"] = distance
            else:
                slots["radius_km"] = distance / 1000
        
        # 지역 추출
        location_patterns = ["근처", "주변", "에서", "지역"]
        if any(pattern in text for pattern in location_patterns):
            slots["use_location"] = True
        
        # 음식 종류
        cuisine_patterns = {
            "한식": ["한식", "한국", "김치", "비빔밥"],
            "중식": ["중식", "중국", "짜장", "짬뽕"],
            "양식": ["양식", "서양", "스테이크", "파스타"],
            "일식": ["일식", "일본", "스시", "라멘"]
        }
        
        for cuisine, patterns in cuisine_patterns.items():
            if any(pattern in text for pattern in patterns):
                slots["cuisine_type"] = cuisine
                break
        
        return slots
