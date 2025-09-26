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
    CALENDAR_SAVE = "calendar_save"      # 캘린더 저장 관련 (새로 추가!)
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
        # 1. 식단표 생성 전용 키워드 (저장 관련 제거!)
        self.mealplan_keywords = [
            "식단표", "식단 만들", "식단 생성", "식단 짜",
            "일주일치", "하루치", "이틀치", "3일치", "사흘치", "4일치", "5일치", "6일치",
            "주간 식단", "메뉴 계획", "meal plan", "weekly menu",
            "식단 추천", "메뉴 추천", "식단표 만들", "식단 계획"
        ]
        
        # 2. 캘린더 저장 전용 키워드 (새로 추가!)
        self.calendar_save_keywords = [
            "캘린더에 저장", "저장해줘", "추가해줘", "등록해줘",
            "캘린더에 넣어", "일정에 추가", "일정에 저장", "일정 등록",
            "스케줄에 추가", "스케줄에 저장", "기록해줘",
            "캘린더 저장", "캘린더 추가", "달력에 저장", "달력에 추가"
        ]
        
        # 3. 레시피 전용 키워드
        self.recipe_keywords = [
            "레시피", "조리법", "만드는 법", "어떻게 만들",
            "요리 방법", "조리 방법", "recipe", "how to make",
            "요리법", "쿠킹", "만들어줘", "해먹"
        ]
        
        # 4. 일반 식사 키워드
        self.meal_general_keywords = [
            "키토", "저탄수", "다이어트", "칼로리", "영양",
            "단백질", "탄수화물", "지방",
            "아침", "점심", "저녁", "간식", "브런치", "디너"
        ]
        
        # 5. 식당/장소 관련 키워드
        self.place_keywords = [
            "식당", "맛집", "음식점", "카페", "레스토랑",
            "근처", "주변", "위치", "어디", "찾아",
            "배달", "포장", "테이크아웃", "매장",
            "영업", "예약", "웨이팅", "리뷰", "평점"
        ]
        
        # 6. 일반 대화 키워드
        self.general_keywords = [
            "안녕", "반가", "고마", "도움", "뭐야", "뭔가요",
            "설명", "알려", "어떻게", "왜", "언제", "누가",
            "좋아", "싫어", "맞아", "틀려", "그래", "아니",
            "ㅋㅋ", "ㅎㅎ", "ㅠㅠ", "헉", "와", "오",
            "이름", "기억", "잊어", "모르", "생각", "느낌"
        ]
    
    async def classify(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """
        사용자 입력 의도 분류 (하이브리드: 키워드 + LLM)
        
        Args:
            user_input: 사용자 입력 메시지
            context: 대화 컨텍스트 (선택)
            
        Returns:
            분류 결과 딕셔너리
        """
        
        text = user_input.lower().strip()
        
        # 0. 캘린더 저장 요청 우선 체크 (최우선 순위!)
        if self._has_calendar_save_intent(text):
            print(f"🗓️ 캘린더 저장 의도 감지: '{text}'")
            return {
                "intent": Intent.CALENDAR_SAVE,
                "confidence": 0.95,
                "method": "keyword",
                "details": {
                    "detected_keywords": [kw for kw in self.calendar_save_keywords if kw in text],
                    "message": "캘린더 저장 요청"
                }
            }
        
        # 1. 빠른 키워드 기반 분류 시도
        keyword_result = self._keyword_classify(text)
        
        # 2. 키워드로 명확한 경우 바로 반환
        if keyword_result["confidence"] >= 0.8:
            intent = self._validate_intent(text, keyword_result["intent"])
            keyword_result["intent"] = intent
            print(f"    ✅ 최종 의도: {intent.value}")
            return keyword_result
        
        # 3. 애매한 경우 LLM 분류 (비용 발생)
        if self.llm:
            try:
                llm_result = await self._llm_classify(text, context)
                print(f"    🤖 LLM 분류: {llm_result['intent'].value} (신뢰도: {llm_result['confidence']:.2f})")
                return llm_result
            except Exception as e:
                print(f"    ❌ LLM 분류 실패: {e}")
        
        # 4. LLM 실패시 키워드 결과 반환
        return keyword_result
    
    def _has_calendar_save_intent(self, text: str) -> bool:
        """캘린더 저장 의도 감지"""
        # 캘린더 저장 키워드 체크
        for keyword in self.calendar_save_keywords:
            if keyword in text:
                # 단, "식단 저장해줘" 같은 경우는 제외 (식단이 없으면 생성 요청일 수 있음)
                # 날짜 관련 키워드가 함께 있으면 저장 의도로 판단
                date_keywords = ["오늘", "내일", "모레", "다음주", "이번주", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
                if any(date_kw in text for date_kw in date_keywords):
                    return True
                # "캘린더" 자체가 언급되면 저장 의도
                if "캘린더" in text or "달력" in text or "일정" in text:
                    return True
        return False
    
    def _keyword_classify(self, text: str) -> Dict[str, Any]:
        """키워드 기반 빠른 분류"""
        
        scores = {
            Intent.MEAL_PLANNING: 0,
            Intent.RESTAURANT_SEARCH: 0,
            Intent.CALENDAR_SAVE: 0,
            Intent.GENERAL: 0,
            Intent.BOTH: 0
        }
        
        detected_keywords = []
        
        # 캘린더 저장 점수 (이미 위에서 체크했지만 여기서도 점수 계산)
        for keyword in self.calendar_save_keywords:
            if keyword in text:
                scores[Intent.CALENDAR_SAVE] += 2
                detected_keywords.append(keyword)
        
        # 식단표 관련 점수
        for keyword in self.mealplan_keywords:
            if keyword in text:
                scores[Intent.MEAL_PLANNING] += 2
                detected_keywords.append(keyword)
        
        # 레시피 관련 점수
        for keyword in self.recipe_keywords:
            if keyword in text:
                scores[Intent.MEAL_PLANNING] += 1.5
                detected_keywords.append(keyword)
        
        # 일반 식사 키워드
        for keyword in self.meal_general_keywords:
            if keyword in text:
                scores[Intent.MEAL_PLANNING] += 0.5
                detected_keywords.append(keyword)
        
        # 식당/장소 관련 점수
        for keyword in self.place_keywords:
            if keyword in text:
                scores[Intent.RESTAURANT_SEARCH] += 2
                detected_keywords.append(keyword)
        
        # 일반 대화 점수
        for keyword in self.general_keywords:
            if keyword in text:
                scores[Intent.GENERAL] += 1
                detected_keywords.append(keyword)
        
        # 질문 패턴 체크
        if self._is_question_pattern(text):
            scores[Intent.GENERAL] += 0.5
        
        # 최고 점수 의도 선택
        max_score = max(scores.values())
        
        if max_score == 0:
            # 키워드가 없으면 일반 대화
            intent = Intent.GENERAL
            confidence = 0.3
        else:
            # 최고 점수 의도 선택
            intent = max(scores, key=scores.get)
            
            # 복합 의도 체크 (식단과 식당 둘 다 높은 경우)
            if scores[Intent.MEAL_PLANNING] > 1 and scores[Intent.RESTAURANT_SEARCH] > 1:
                intent = Intent.BOTH
                confidence = 0.9
            else:
                # 신뢰도 계산
                total_score = sum(scores.values())
                confidence = min(max_score / max(total_score, 1) * 1.5, 1.0)
        
        print(f"🔍 키워드 분류: {text[:50]}...")
        print(f"    점수: MEAL={scores[Intent.MEAL_PLANNING]:.1f}, REST={scores[Intent.RESTAURANT_SEARCH]:.1f}, SAVE={scores[Intent.CALENDAR_SAVE]:.1f}, GEN={scores[Intent.GENERAL]:.1f}")
        print(f"    의도: {intent.value} (신뢰도: {confidence:.2f})")
        
        return {
            "intent": intent,
            "confidence": confidence,
            "method": "keyword",
            "scores": {k.value: v for k, v in scores.items()},
            "detected_keywords": detected_keywords[:10]  # 최대 10개만
        }
    
    def _is_question_pattern(self, text: str) -> bool:
        """질문 패턴 감지"""
        question_patterns = [
            r'\?', r'뭐야\?', r'뭔가요\?', r'뭐지\?', r'뭐야', r'뭔가', r'뭐지',
            r'어떻게\?', r'어떤\?', r'어떤가\?', r'어떻게', r'어떤', r'어떤가',
            r'왜\?', r'왜야\?', r'왜지\?', r'왜', r'왜야', r'왜지',
            r'도움\?', r'도움이\?', r'될까\?', r'도움', r'도움이', r'될까',
            r'대화', r'채팅', r'말해', r'알려줘', r'설명해', r'궁금해',
            r'기억해', r'기억하', r'뭐라고', r'뭐라고 했', r'방금', r'아까',
            r'이름', r'내 이름', r'제 이름', r'기억 못', r'기억 안'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in question_patterns)
    
    def _has_action_keyword(self, text: str) -> bool:
        """구체적인 액션 키워드 감지"""
        action_keywords = [
            "레시피", "식단", "만들", "찾아", "추천", "식당", "맛집", "음식점",
            "기억해", "기억하", "뭐라고", "뭐라고 했", "방금", "아까",
            "이름", "내 이름", "제 이름", "기억 못", "기억 안", "대화", "채팅",
            "저장", "추가", "등록", "캘린더"  # 저장 관련도 액션
        ]
        return any(word in text for word in action_keywords)
    
    def _validate_intent(self, text: str, initial_intent: Intent) -> Intent:
        """의도 검증 및 수정"""
        
        # 캘린더 저장이면 유지
        if initial_intent == Intent.CALENDAR_SAVE:
            return initial_intent
        
        # 대화 관련 질문은 GENERAL로 유지 (이름 기억, 이전 대화 내용 등)
        if any(keyword in text for keyword in [
            "기억해", "기억하", "뭐라고", "뭐라고 했", "방금", "아까",
            "이름", "내 이름", "제 이름", "기억 못", "기억 안", "대화", "채팅"
        ]):
            print(f"    🔍 검증: 대화 관련 질문 감지 → GENERAL 유지")
            return Intent.GENERAL
        
        # 질문형 패턴이 있지만 구체적인 액션 키워드가 없으면 GENERAL로 변경
        if self._is_question_pattern(text) and not self._has_action_keyword(text):
            print(f"    🔍 검증: 질문형 패턴 감지 → GENERAL로 변경")
            return Intent.GENERAL
        
        # 식단표 관련 명확한 키워드 우선 체크
        if any(keyword in text for keyword in [
            "하루치", "일주일치", "이틀치", "3일치", "사흘치",
            "식단표", "식단 만들", "식단 생성", "식단 짜",
            "메뉴 계획", "일주일 식단", "주간 식단", "다음주 식단",
            "이번주 식단", "한주 식단", "한 주 식단"
        ]):
            print(f"    🔍 검증: 식단표 키워드 감지 → MEAL_PLANNING 강제")
            return Intent.MEAL_PLANNING
        
        # 레시피 관련 명확한 키워드 체크
        if any(keyword in text for keyword in [
            "레시피", "조리법", "만드는 법", "어떻게 만들",
            "요리 방법", "조리 방법", "만들어줘", "만들어 줘"
        ]) and "식단" not in text:
            print(f"    🔍 검증: 레시피 키워드 감지 → MEAL_PLANNING 강제")
            return Intent.MEAL_PLANNING
        
        # 식당 관련 명확한 키워드 체크
        if any(keyword in text for keyword in [
            "식당", "맛집", "음식점", "카페", "레스토랑", "근처", "주변"
        ]):
            print(f"    🔍 검증: 식당 키워드 감지 → RESTAURANT_SEARCH 강제")
            return Intent.RESTAURANT_SEARCH
        
        return initial_intent
    
    async def _llm_classify(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """LLM 기반 정확한 분류"""
        
        prompt = f"""
사용자의 입력을 분석하여 다음 5가지 의도 중 하나로 분류해주세요:

1. MEAL_PLANNING: 키토 식단 계획, 레시피, 요리법, 영양 정보 관련
2. RESTAURANT_SEARCH: 주변 식당, 맛집 찾기, 음식점 추천 관련  
3. CALENDAR_SAVE: 이미 생성된 식단을 캘린더에 저장하는 요청
4. BOTH: 식단과 식당 정보 모두 필요한 경우
5. GENERAL: 일반적인 대화나 인사, 기타 질문

중요: "저장해줘", "캘린더에 추가" 등의 표현이 있으면 CALENDAR_SAVE로 분류하세요.

사용자 입력: "{user_input}"
{f"대화 맥락: {context}" if context else ""}

JSON 형식으로 응답:
{{
    "intent": "MEAL_PLANNING|RESTAURANT_SEARCH|CALENDAR_SAVE|BOTH|GENERAL",
    "confidence": 0.0-1.0,
    "reasoning": "분류 이유"
}}
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # JSON 파싱
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Intent Enum으로 변환
                intent_map = {
                    "MEAL_PLANNING": Intent.MEAL_PLANNING,
                    "RESTAURANT_SEARCH": Intent.RESTAURANT_SEARCH,
                    "CALENDAR_SAVE": Intent.CALENDAR_SAVE,
                    "BOTH": Intent.BOTH,
                    "GENERAL": Intent.GENERAL
                }
                
                intent = intent_map.get(result["intent"], Intent.GENERAL)
                
                return {
                    "intent": intent,
                    "confidence": result.get("confidence", 0.8),
                    "method": "llm",
                    "reasoning": result.get("reasoning", "")
                }
        except Exception as e:
            print(f"LLM 분류 오류: {e}")
        
        # 실패시 일반 대화로 분류
        return {
            "intent": Intent.GENERAL,
            "confidence": 0.5,
            "method": "llm_fallback",
            "reasoning": "LLM 분류 실패"
        }