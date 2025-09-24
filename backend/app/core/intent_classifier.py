"""
자연어 의도 분류기
사용자 입력을 분석하여 도메인별 에이전트로 라우팅
하이브리드 방식 지원: 키워드 기반 빠른 분류 + LLM 정확한 분류
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
import re
import json

from app.core.config import settings


class Intent(Enum):
    """의도 분류 열거형"""
    MEAL_PLANNING = "meal_planning"      # 식단 계획/레시피 관련
    RESTAURANT_SEARCH = "restaurant_search"  # 식당 찾기 관련
    BOTH = "both"                       # 두 기능 모두 필요
    GENERAL = "general"                 # 일반 대화


class IntentClassifier:
    """자연어 의도 분류기 - 하이브리드 방식"""
    
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
        
        # 키워드 정리 및 중복 제거
        # 1. 식단표 전용 키워드
        self.mealplan_keywords = [
            "식단표", "식단 만들", "식단 생성", "식단 짜",
            "일주일치", "하루치", "이틀치", "3일치", "사흘치",
            "주간 식단", "메뉴 계획", "meal plan", "weekly menu"
        ]
        
        # 2. 레시피 전용 키워드
        self.recipe_keywords = [
            "레시피", "조리법", "만드는 법", "어떻게 만들",
            "요리 방법", "조리 방법", "recipe", "how to make",
            "요리법", "쿠킹", "만들어줘", "해먹"
        ]
        
        # 3. 일반 식사 키워드 (중복 제거)
        self.meal_general_keywords = [
            "키토", "저탄수", "다이어트", "칼로리", "영양",
            "단백질", "탄수화물", "지방",
            "아침", "점심", "저녁", "간식", "브런치", "디너"
        ]
        
        # 4. 식당 관련 키워드
        self.restaurant_keywords = [
            "식당", "맛집", "음식점", "카페", "레스토랑",
            "근처", "주변", "찾아", "추천", "배달", "포장",
            "예약", "위치", "거리", "갈만한", "먹을만한",
            "가게", "점포", "어디", "장소"
        ]
        
        # Intent 매핑 테이블 (안전한 파싱용)
        self.intent_mapping = {
            "MEAL_PLANNING": Intent.MEAL_PLANNING,
            "meal_planning": Intent.MEAL_PLANNING,
            "RESTAURANT_SEARCH": Intent.RESTAURANT_SEARCH,
            "restaurant_search": Intent.RESTAURANT_SEARCH,
            "BOTH": Intent.BOTH,
            "both": Intent.BOTH,
            "GENERAL": Intent.GENERAL,
            "general": Intent.GENERAL
        }
    
    def _parse_intent_safely(self, intent_str: str) -> Intent:
        """안전한 Intent 파싱"""
        # 대소문자 변형 처리
        intent_str = intent_str.strip()
        
        # 직접 매핑 확인
        if intent_str in self.intent_mapping:
            return self.intent_mapping[intent_str]
        
        # 대소문자 무시 매핑
        intent_upper = intent_str.upper()
        if intent_upper in self.intent_mapping:
            return self.intent_mapping[intent_upper]
        
        intent_lower = intent_str.lower()
        if intent_lower in self.intent_mapping:
            return self.intent_mapping[intent_lower]
        
        # 기본값
        print(f"  ⚠️ 알 수 없는 Intent: {intent_str} → GENERAL로 처리")
        return Intent.GENERAL
    
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
        
        # 높은 확신도면 바로 반환
        if quick_result["confidence"] >= 0.8:
            return quick_result
        
        # 2단계: LLM이 없거나 중간 확신도일 때
        if not self.llm:
            # LLM 없으면 키워드 결과 그대로 사용
            return quick_result
        
        # 중간 확신도(0.5-0.8)면 키워드 결과 사용
        if 0.5 <= quick_result["confidence"] < 0.8:
            print(f"  📊 중간 확신도 ({quick_result['confidence']:.2f}) → 키워드 결과 사용")
            return quick_result
        
        # 3단계: 낮은 확신도일 때만 LLM 사용
        llm_result = await self._llm_classify(user_input, context)
        
        # 결과 조합
        return self._combine_results(quick_result, llm_result)
    
    def _quick_classify(self, user_input: str) -> Dict[str, Any]:
        """키워드 기반 빠른 분류 (개선된 버전)"""
        
        text = user_input.lower()
        
        # 키워드 매칭 카운트
        mealplan_count = sum(1 for keyword in self.mealplan_keywords if keyword in text)
        recipe_count = sum(1 for keyword in self.recipe_keywords if keyword in text)
        meal_general_count = sum(1 for keyword in self.meal_general_keywords if keyword in text)
        restaurant_count = sum(1 for keyword in self.restaurant_keywords if keyword in text)
        
        # 일수 패턴 확인
        has_days_pattern = bool(re.search(r'\d+일|일주일|하루|이틀|사흘|나흘|닷새|엿새|한주|한 주', text))
        
        # 디버깅 정보
        print(f"  🔍 키워드 매칭: 식단표={mealplan_count}, 레시피={recipe_count}, "
              f"식사일반={meal_general_count}, 식당={restaurant_count}, 일수패턴={has_days_pattern}")
        
        # 의도 결정 로직 (우선순위 기반)
        intent = Intent.GENERAL
        confidence = 0.3
        subtype = None
        
        # 1. 명확한 식단표 요청
        if mealplan_count > 0 or (has_days_pattern and "식단" in text):
            intent = Intent.MEAL_PLANNING
            # 개선된 확신도 계산
            base_confidence = 0.8
            keyword_bonus = min(0.15, mealplan_count * 0.05)
            confidence = min(0.95, base_confidence + keyword_bonus)
            subtype = "mealplan"
            
        # 2. 명확한 레시피 요청
        elif recipe_count > 0:
            intent = Intent.MEAL_PLANNING
            base_confidence = 0.75
            keyword_bonus = min(0.2, recipe_count * 0.05)
            confidence = min(0.95, base_confidence + keyword_bonus)
            subtype = "recipe"
            
        # 3. 식당과 음식 둘 다
        elif (meal_general_count > 0 or recipe_count > 0) and restaurant_count > 0:
            intent = Intent.BOTH
            total_count = meal_general_count + recipe_count + restaurant_count
            confidence = min(0.9, 0.6 + total_count * 0.05)
            
        # 4. 식당만
        elif restaurant_count > 0:
            intent = Intent.RESTAURANT_SEARCH
            base_confidence = 0.7
            keyword_bonus = min(0.2, restaurant_count * 0.05)
            confidence = min(0.9, base_confidence + keyword_bonus)
            
        # 5. 음식 관련 일반
        elif meal_general_count > 0:
            intent = Intent.MEAL_PLANNING
            confidence = min(0.6, 0.4 + meal_general_count * 0.05)
            # 추가 분석으로 subtype 결정
            subtype = self._determine_meal_subtype(text)
        
        return {
            "intent": intent,
            "confidence": confidence,
            "method": "keyword",
            "subtype": subtype,
            "keywords_found": {
                "mealplan": mealplan_count,
                "recipe": recipe_count,
                "meal": meal_general_count,
                "restaurant": restaurant_count,
                "has_days": has_days_pattern
            }
        }
    
    def _determine_meal_subtype(self, text: str) -> str:
        """MEAL_PLANNING의 세부 타입 결정"""
        
        # 일수 관련 패턴 (개선)
        days_patterns = [
            r'\d+일', r'하루', r'이틀', r'사흘', r'나흘', r'닷새', r'엿새',
            r'일주일', r'한주', r'한 주', r'이번주', r'다음주', r'주간'
        ]
        
        has_days = any(re.search(pattern, text) for pattern in days_patterns)
        
        # 식단표 명시적 언급
        has_mealplan_word = any(word in text for word in ["식단표", "식단", "메뉴 계획", "meal plan"])
        
        # 레시피 명시적 언급
        has_recipe_word = any(word in text for word in ["레시피", "조리법", "만드는 법", "요리 방법"])
        
        if has_mealplan_word or has_days:
            return "mealplan"
        elif has_recipe_word:
            return "recipe"
        else:
            # 기본값은 recipe
            return "recipe"
    
    async def _llm_classify(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """LLM 기반 정확한 분류"""
        
        prompt = f"""
사용자의 입력을 분석하여 다음 4가지 의도 중 하나로 분류해주세요:

1. MEAL_PLANNING: 키토 식단 계획, 레시피, 요리법, 영양 정보 관련
2. RESTAURANT_SEARCH: 주변 식당, 맛집 찾기, 음식점 추천 관련  
3. BOTH: 식단과 식당 정보 모두 필요한 경우
4. GENERAL: 위 카테고리에 해당하지 않는 일반 대화

추가로 MEAL_PLANNING인 경우 세부 타입도 분류해주세요:
- recipe: 개별 레시피나 요리법
- mealplan: 여러 일의 식단표나 메뉴 계획

이전 대화 맥락: {context}
사용자 입력: {user_input}

응답 형식 (JSON):
{{
    "intent": "MEAL_PLANNING|RESTAURANT_SEARCH|BOTH|GENERAL",
    "subtype": "recipe|mealplan|null",
    "confidence": 0.0-1.0,
    "reasoning": "분류 근거"
}}
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            # JSON 파싱 (안전하게)
            content = response.content.strip()
            
            # JSON 부분만 추출
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                raise ValueError("JSON 형식을 찾을 수 없습니다")
            
            result = json.loads(json_match.group())
            
            # 안전한 Intent 파싱
            intent = self._parse_intent_safely(result.get("intent", "GENERAL"))
            
            return {
                "intent": intent,
                "confidence": float(result.get("confidence", 0.5)),
                "method": "llm",
                "subtype": result.get("subtype"),
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            print(f"  ❌ LLM 분류 오류: {e}")
            # LLM 분류 실패 시 기본값 반환
            return {
                "intent": Intent.GENERAL,
                "confidence": 0.5,
                "method": "llm_fallback",
                "subtype": None,
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
        
        # subtype이 없으면 다른 결과에서 가져오기
        if not primary.get("subtype") and secondary.get("subtype"):
            primary["subtype"] = secondary["subtype"]
        
        return {
            "intent": primary["intent"],
            "confidence": primary["confidence"],
            "primary_method": primary["method"],
            "secondary_method": secondary["method"],
            "subtype": primary.get("subtype"),
            "details": {
                "quick_classification": quick_result,
                "llm_classification": llm_result
            }
        }
    
    def extract_slots(self, user_input: str, intent: Intent) -> Dict[str, Any]:
        """의도별 슬롯 추출 (개선된 버전)"""
        
        slots = {}
        
        if intent in [Intent.MEAL_PLANNING, Intent.BOTH]:
            slots.update(self._extract_meal_slots(user_input))
        
        if intent in [Intent.RESTAURANT_SEARCH, Intent.BOTH]:
            slots.update(self._extract_restaurant_slots(user_input))
        
        return slots
    
    def _extract_meal_slots(self, text: str) -> Dict[str, Any]:
        """식단 관련 슬롯 추출 (개선)"""
        
        slots = {}
        
        # 일수 추출 (개선)
        days_mapping = {
            "하루": 1, "하루치": 1, "1일": 1, "일일": 1,
            "이틀": 2, "이틀치": 2, "2일": 2, "양일": 2,
            "사흘": 3, "사흘치": 3, "3일": 3, "삼일": 3,
            "나흘": 4, "나흘치": 4, "4일": 4,
            "닷새": 5, "닷새치": 5, "5일": 5,
            "엿새": 6, "엿새치": 6, "6일": 6,
            "일주일": 7, "일주일치": 7, "7일": 7, "한주": 7, "한 주": 7,
            "이번주": 7, "다음주": 7, "주간": 7
        }
        
        for keyword, days in days_mapping.items():
            if keyword in text:
                slots["days"] = days
                print(f"    📅 일수 슬롯 추출: {keyword} → {days}일")
                break
        
        # 숫자 + "일" 패턴 처리 (정규식 개선)
        if "days" not in slots:
            days_match = re.search(r'(\d+)\s*일', text)
            if days_match:
                try:
                    days_num = int(days_match.group(1))
                    if 1 <= days_num <= 30:  # 합리적인 범위 체크
                        slots["days"] = days_num
                        print(f"    📅 일수 슬롯 추출: {days_match.group(0)} → {days_num}일")
                except ValueError:
                    pass
        
        # 시간대 추출
        time_patterns = {
            "아침": ["아침", "조식", "morning", "브렉퍼스트", "breakfast"],
            "점심": ["점심", "중식", "lunch", "런치"],
            "저녁": ["저녁", "석식", "dinner", "디너"],
            "간식": ["간식", "snack", "스낵"]
        }
        
        for time_key, patterns in time_patterns.items():
            if any(pattern in text for pattern in patterns):
                slots["meal_time"] = time_key
                break
        
        # 칼로리 추출 (정규식 개선)
        calorie_match = re.search(r'(\d+)\s*(?:칼로리|kcal|cal)', text)
        if calorie_match:
            try:
                calories = int(calorie_match.group(1))
                if 100 <= calories <= 5000:  # 합리적인 범위
                    slots["target_calories"] = calories
            except ValueError:
                pass
        
        # 탄수화물 제한 추출 (정규식 개선)
        carb_match = re.search(r'탄수화물?\s*(\d+)\s*(?:g|그램|gram)', text)
        if carb_match:
            try:
                carbs = int(carb_match.group(1))
                if 0 <= carbs <= 200:  # 합리적인 범위
                    slots["max_carbs"] = carbs
            except ValueError:
                pass
        
        # 알레르기/제외 재료
        exclude_patterns = ["빼고", "제외", "없이", "알레르기", "싫어", "안먹", "못먹"]
        if any(pattern in text for pattern in exclude_patterns):
            slots["has_restrictions"] = True
        
        return slots
    
    def _extract_restaurant_slots(self, text: str) -> Dict[str, Any]:
        """식당 관련 슬롯 추출 (개선)"""
        
        slots = {}
        
        # 거리 추출 (정규식 수정)
        # 킬로미터 패턴
        km_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:킬로미터|킬로|km)', text)
        if km_match:
            try:
                km = float(km_match.group(1))
                if 0.1 <= km <= 50:  # 합리적인 범위
                    slots["radius_km"] = km
            except ValueError:
                pass
        
        # 미터 패턴
        if "radius_km" not in slots:
            m_match = re.search(r'(\d+)\s*(?:미터|m)(?!.*킬로)', text)
            if m_match:
                try:
                    meters = int(m_match.group(1))
                    if 10 <= meters <= 50000:  # 합리적인 범위
                        slots["radius_km"] = meters / 1000
                except ValueError:
                    pass
        
        # 도보 시간으로 거리 추정
        walk_match = re.search(r'도보\s*(\d+)\s*분', text)
        if walk_match and "radius_km" not in slots:
            try:
                minutes = int(walk_match.group(1))
                # 도보 속도 약 4km/h로 계산
                slots["radius_km"] = round((minutes * 4 / 60), 1)
            except ValueError:
                pass
        
        # 지역 추출
        location_patterns = ["근처", "주변", "에서", "지역", "역", "동", "부근"]
        if any(pattern in text for pattern in location_patterns):
            slots["use_location"] = True
        
        # 음식 종류
        cuisine_patterns = {
            "한식": ["한식", "한국", "김치", "비빔밥", "국밥", "찌개", "삼겹살"],
            "중식": ["중식", "중국", "짜장", "짬뽕", "마라", "탕수육"],
            "양식": ["양식", "서양", "스테이크", "파스타", "피자", "버거"],
            "일식": ["일식", "일본", "스시", "라멘", "돈카츠", "우동"]
        }
        
        for cuisine, patterns in cuisine_patterns.items():
            if any(pattern in text for pattern in patterns):
                slots["cuisine_type"] = cuisine
                break
        
        # 키토 친화도 요청
        if any(word in text for word in ["키토", "저탄수", "저탄수화물", "keto", "로우카브"]):
            slots["keto_friendly"] = True
        
        return slots
    
    def get_intent_details(self, intent: Intent) -> Dict[str, Any]:
        """의도별 상세 정보 제공"""
        
        details = {
            Intent.MEAL_PLANNING: {
                "name": "식단/레시피 계획",
                "description": "키토 식단표 생성, 레시피 검색, 영양 정보 제공",
                "required_slots": [],
                "optional_slots": ["days", "meal_time", "target_calories", "max_carbs", "has_restrictions"]
            },
            Intent.RESTAURANT_SEARCH: {
                "name": "식당 검색",
                "description": "주변 키토 친화적 식당 찾기 및 추천",
                "required_slots": [],
                "optional_slots": ["radius_km", "use_location", "cuisine_type", "keto_friendly"]
            },
            Intent.BOTH: {
                "name": "통합 검색",
                "description": "식단 정보와 식당 정보 모두 제공",
                "required_slots": [],
                "optional_slots": ["meal_time", "use_location", "radius_km"]
            },
            Intent.GENERAL: {
                "name": "일반 대화",
                "description": "키토 관련 일반적인 질문과 상담",
                "required_slots": [],
                "optional_slots": []
            }
        }
        
        return details.get(intent, {})