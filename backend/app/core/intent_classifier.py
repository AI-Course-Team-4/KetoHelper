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
    """자연어 의도 분류기 - LLM 우선 방식"""
    
    # LLM 우선 처리를 위한 임계값 조정
    KEYWORD_HIGH_CONFIDENCE = 0.95  # 키워드만으로 확정할 임계값 (매우 높게 설정)
    LLM_MIN_CONFIDENCE = 0.4        # LLM 사용 최소 임계값 (낮게 설정하여 적극 활용)
    
    def __init__(self):
        try:
            if not settings.google_api_key:
                raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다")
            
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=settings.gemini_temperature
            )
            print(f"[OK] Gemini LLM 초기화 성공: {settings.llm_model}")
        except Exception as e:
            print(f"[ERROR] Gemini AI 초기화 실패: {str(e)}")
            print(f"   - API Key 존재: {'예' if settings.google_api_key else '아니오'}")
            print(f"   - 모델: {settings.llm_model}")
            print(f"   - 온도: {settings.gemini_temperature}")
            self.llm = None
        
        # 키워드 규칙 개선 - LLM 보조용으로 적절한 수준 유지
        # 1. 캘린더 저장 - 최우선 처리
        self.calendar_save_keywords = [
            "캘린더에 저장", "캘린더에 넣어", "캘린더 저장", "캘린더 추가",
            "일정에 저장", "일정 등록", "일정에 추가", "일정으로", "캘린더",
            "일정 추가", "일정 업데이트", "캘린더 기록", "캘린더로 동기화"
        ]
        
        # 2. 식단 계획 - 식단표와 레시피 모두 포함
        self.mealplan_keywords = [
            # 식단표 관련
            "식단표", "식단 만들", "식단 생성", "식단 짜", "식단표 만들", "식단표 생성", "식단표 짜",
            "일주일 식단", "주간 식단", "식단 계획", "메뉴 계획", "하루치", "이틀치", "3일치", "7일",
            "일주일", "주간", "이번주", "다음주", "한 주", "이틀", "3일", "사흘", "구성해",
            # 레시피 관련
            "레시피", "조리법", "만드는법", "만드는 법", "요리법", "만들어", "어떻게 만들",
            "요리 방법", "조리 방법", "만들어줘", "비법", "굽는법", "만드는 방법"
        ]
        
        # 3. 장소 검색 - 식당/맛집 관련
        self.place_keywords = [
            "맛집", "식당", "음식점", "카페", "레스토랑", "찾아", "근처", "주변",
            "어디", "위치", "가까운", "근방", "포장", "배달", "테이크아웃", "잘하는 곳"
        ]
        
        # 4. 일반 대화 - 인사, 감사, 질문 등
        self.general_keywords = [
            "안녕", "고마워", "감사", "도움말", "뭐해", "반가워", "하이", "헬로",
            "기억해", "알레르기", "싫어해", "못 먹어", "기분", "누구", "설명", "예시",
            "좋은 하루"  # "좋은 하루야" 같은 인사말 처리
        ]
    
    async def classify(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """
        사용자 입력 의도 분류 (LLM 우선 방식)
        
        Args:
            user_input: 사용자 입력 메시지
            context: 대화 컨텍스트 (선택)
            
        Returns:
            분류 결과 딕셔너리
        """
        
        text = user_input.lower().strip()
        
        # 0. 캘린더 저장 요청 최우선 체크 (매우 명확한 경우만)
        if self._has_calendar_save_intent(text):
            print(f"[CALENDAR] 캘린더 저장 의도 감지: '{text}'")
            return {
                "intent": Intent.CALENDAR_SAVE,
                "confidence": 0.95,
                "method": "keyword",
                "details": {
                    "detected_keywords": [kw for kw in self.calendar_save_keywords if kw in text],
                    "message": "캘린더 저장 요청"
                }
            }
        
        # 1. LLM 분류 우선 시도 (LLM이 있으면 바로 사용)
        if self.llm:
            try:
                llm_result = await self._llm_classify(text, context)
                print(f"    [LLM] LLM 분류: {llm_result['intent'].value} (신뢰도: {llm_result['confidence']:.2f})")
                
                # LLM 결과가 최소 신뢰도 이상이면 바로 반환
                if llm_result["confidence"] >= self.LLM_MIN_CONFIDENCE:
                    return llm_result
                    
            except Exception as e:
                print(f"    [ERROR] LLM 분류 실패: {str(e)}")
        
        # 2. LLM 실패 또는 낮은 신뢰도일 때만 키워드 분류 사용
        keyword_result = self._keyword_classify(text)
        
        # 3. 키워드로도 명확하지 않으면 LLM 결과라도 반환 (LLM이 있었다면)
        if self.llm and keyword_result["confidence"] < self.KEYWORD_HIGH_CONFIDENCE:
            try:
                # LLM 재시도 (더 상세한 프롬프트로)
                llm_result = await self._llm_classify_detailed(text, context)
                print(f"    [LLM] LLM 재분류: {llm_result['intent'].value} (신뢰도: {llm_result['confidence']:.2f})")
                return llm_result
            except Exception as e:
                print(f"    [ERROR] LLM 재분류 실패: {str(e)}")
        
        # 4. 최종 폴백: 키워드 결과 반환
        intent = self._validate_intent(text, keyword_result["intent"])
        keyword_result["intent"] = intent
        print(f"    [OK] 최종 의도 (키워드): {intent.value}")
        return keyword_result
    
    def _has_calendar_save_intent(self, text: str) -> bool:
        """캘린더 저장 의도 감지 - 매우 명확한 경우만"""
        # 명확한 캘린더 저장 키워드만 체크
        return any(keyword in text for keyword in self.calendar_save_keywords)
    
    def _keyword_classify(self, text: str) -> Dict[str, Any]:
        """키워드 기반 분류 - 개선된 점수 계산"""
        
        scores = {
            Intent.MEAL_PLANNING: 0,
            Intent.RESTAURANT_SEARCH: 0,
            Intent.CALENDAR_SAVE: 0,
            Intent.GENERAL: 0
        }
        
        detected_keywords = []
        
        # 식단 계획 관련 점수 계산
        for keyword in self.mealplan_keywords:
            if keyword in text:
                if keyword in ["식단표", "레시피", "조리법", "만드는법", "요리법"]:
                    scores[Intent.MEAL_PLANNING] += 2.0  # 높은 가중치
                elif keyword in ["일주일", "주간", "하루치", "이틀치", "3일치"]:
                    scores[Intent.MEAL_PLANNING] += 1.5  # 중간 가중치
                else:
                    scores[Intent.MEAL_PLANNING] += 1.0  # 기본 가중치
                detected_keywords.append(keyword)
        
        # 장소 검색 관련 점수 계산
        for keyword in self.place_keywords:
            if keyword in text:
                if keyword in ["맛집", "식당", "음식점", "카페", "레스토랑"]:
                    scores[Intent.RESTAURANT_SEARCH] += 2.0
                elif keyword in ["근처", "주변", "찾아"]:
                    scores[Intent.RESTAURANT_SEARCH] += 1.5
                else:
                    scores[Intent.RESTAURANT_SEARCH] += 1.0
                detected_keywords.append(keyword)
        
        # "추천" 키워드 특별 처리 - 맥락에 따라 다르게 처리
        if "추천" in text:
            if any(place_kw in text for place_kw in ["맛집", "식당", "음식점", "카페", "레스토랑", "근처", "주변"]):
                scores[Intent.RESTAURANT_SEARCH] += 1.5  # 장소 관련 추천
            elif any(meal_kw in text for meal_kw in ["식단", "메뉴", "레시피"]):
                scores[Intent.MEAL_PLANNING] += 1.0  # 식단 관련 추천
            detected_keywords.append("추천")
        
        # 캘린더 저장 관련 점수 계산 (이미 위에서 처리되지만 추가 점수)
        for keyword in self.calendar_save_keywords:
            if keyword in text:
                scores[Intent.CALENDAR_SAVE] += 2.0
                detected_keywords.append(keyword)
        
        # 일반 대화 관련 점수 계산
        for keyword in self.general_keywords:
            if keyword in text:
                scores[Intent.GENERAL] += 1.0
                detected_keywords.append(keyword)
        
        # 최고 점수 의도 선택
        max_score = max(scores.values())
        
        if max_score == 0:
            intent = Intent.GENERAL
            confidence = 0.3
        else:
            intent = max(scores, key=scores.get)
            # 신뢰도 계산 (점수에 따라 조정)
            if max_score >= 2.0:
                confidence = 0.8
            elif max_score >= 1.5:
                confidence = 0.7
            elif max_score >= 1.0:
                confidence = 0.6
            else:
                confidence = 0.4
        
        print(f"[KEYWORD] 키워드 분류: {text[:50]}...")
        print(f"    점수: MEAL={scores[Intent.MEAL_PLANNING]:.1f}, REST={scores[Intent.RESTAURANT_SEARCH]:.1f}, SAVE={scores[Intent.CALENDAR_SAVE]:.1f}, GEN={scores[Intent.GENERAL]:.1f}")
        print(f"    의도: {intent.value} (신뢰도: {confidence:.2f})")
        
        return {
            "intent": intent,
            "confidence": confidence,
            "method": "keyword",
            "detected_keywords": detected_keywords[:5]  # 최대 5개만
        }
    
    def _validate_intent(self, text: str, initial_intent: Intent) -> Intent:
        """의도 검증 및 수정 - 간소화"""
        # LLM 우선 방식에서는 검증 로직을 최소화
        return initial_intent
    
    async def _llm_classify(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """LLM 기반 정확한 분류 - 개선된 프롬프트"""
        
        prompt = f"""사용자의 입력을 분석하여 다음 5가지 의도 중 하나로 정확히 분류해주세요:

1. MEAL_PLANNING: 
   - 식단표 만들기, 식단 계획, 주간/일주일 식단
   - 레시피, 조리법, 요리 방법
   - 키토/저탄수 식단, 영양 정보
   - 예: "일주일 식단 짜줘", "삼겹살 레시피", "키토 식단 추천"

2. RESTAURANT_SEARCH:
   - 식당, 맛집, 음식점, 카페 찾기
   - 주변, 근처 장소 검색
   - 예: "근처 맛집", "강남 식당 추천", "카페 어디있어?"

3. CALENDAR_SAVE:
   - 이미 만든 식단을 캘린더에 저장
   - 일정 등록, 캘린더 추가
   - 예: "캘린더에 저장해줘", "일정으로 등록"

4. BOTH:
   - 식단과 식당 정보 모두 필요
   - 예: "키토 식단 짜고 근처 맛집도 알려줘"

5. GENERAL:
   - 인사, 감사, 일반 대화
   - 기억해달라는 요청 (알레르기, 선호도)
   - 도움말, 설명 요청
   - 예: "안녕", "고마워", "브로콜리 싫어해", "도움말"

사용자 입력: "{user_input}"
{f"대화 맥락: {context}" if context else ""}

반드시 JSON 형식으로만 응답하세요:
{{
    "intent": "MEAL_PLANNING|RESTAURANT_SEARCH|CALENDAR_SAVE|BOTH|GENERAL",
    "confidence": 0.0-1.0,
    "reasoning": "분류 이유를 한 문장으로"
}}"""
        
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
                confidence = max(0.5, min(1.0, result.get("confidence", 0.8)))  # 0.5~1.0 범위로 제한
                
                return {
                    "intent": intent,
                    "confidence": confidence,
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
    
    async def _llm_classify_detailed(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """LLM 기반 상세 분류 - 재시도용"""
        
        prompt = f"""다음 사용자 입력을 매우 신중하게 분석하여 의도를 분류해주세요.

사용자 입력: "{user_input}"
{f"대화 맥락: {context}" if context else ""}

분류 기준:
- MEAL_PLANNING: 식단, 레시피, 요리 관련 (식단표, 조리법, 영양 정보 등)
- RESTAURANT_SEARCH: 장소 찾기 관련 (식당, 맛집, 근처, 주변 등)
- CALENDAR_SAVE: 캘린더 저장 관련 (저장, 등록, 일정 추가 등)
- BOTH: 식단과 장소 모두 필요
- GENERAL: 일반 대화 (인사, 감사, 기억 요청, 도움말 등)

특별 고려사항:
1. "기억해줘", "알레르기", "싫어해" → GENERAL
2. "일주일", "식단표", "레시피" → MEAL_PLANNING  
3. "근처", "맛집", "식당" → RESTAURANT_SEARCH
4. "저장", "캘린더", "일정" → CALENDAR_SAVE

JSON으로만 응답:
{{
    "intent": "분류결과",
    "confidence": 0.6-1.0,
    "reasoning": "상세한 분류 이유"
}}"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                intent_map = {
                    "MEAL_PLANNING": Intent.MEAL_PLANNING,
                    "RESTAURANT_SEARCH": Intent.RESTAURANT_SEARCH,
                    "CALENDAR_SAVE": Intent.CALENDAR_SAVE,
                    "BOTH": Intent.BOTH,
                    "GENERAL": Intent.GENERAL
                }
                
                intent = intent_map.get(result["intent"], Intent.GENERAL)
                confidence = max(0.6, min(1.0, result.get("confidence", 0.8)))
                
                return {
                    "intent": intent,
                    "confidence": confidence,
                    "method": "llm_detailed",
                    "reasoning": result.get("reasoning", "")
                }
        except Exception as e:
            print(f"LLM 상세 분류 오류: {e}")
        
        return {
            "intent": Intent.GENERAL,
            "confidence": 0.6,
            "method": "llm_detailed_fallback",
            "reasoning": "LLM 상세 분류 실패"
        }