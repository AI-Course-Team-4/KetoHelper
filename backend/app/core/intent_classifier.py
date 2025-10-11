"""
자연어 의도 분류기
사용자 입력을 분석하여 도메인별 에이전트로 라우팅
하이브리드 방식 지원: 키워드 기반 빠른 분류 + LLM 정확한 분류
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from langchain.schema import HumanMessage
import re
import json

from app.core.config import settings
from app.prompts.chat.intent_classification import get_intent_prompt
from app.core.llm_factory import create_chat_llm


class Intent(Enum):
    """의도 분류 열거형"""
    RECIPE_SEARCH = "recipe_search"      # 레시피 검색 관련
    MEAL_PLAN = "meal_plan"              # 식단표 생성 관련
    PLACE_SEARCH = "place_search"        # 식당 찾기 관련
    CALENDAR_SAVE = "calendar_save"      # 캘린더 저장 관련
    BOTH = "both"                       # 두 기능 모두 필요
    GENERAL = "general"                 # 일반 대화


class IntentClassifier:
    """자연어 의도 분류기 - LLM 우선 방식"""
    
    # LLM 우선 처리를 위한 임계값 조정
    KEYWORD_HIGH_CONFIDENCE = 0.9   # 키워드만으로 확정할 임계값 (낮춤)
    LLM_MIN_CONFIDENCE = 0.5        # LLM 사용 최소 임계값 (적절한 수준)
    
    def __init__(self):
        try:
            self.llm = create_chat_llm()
            print(f"[OK] LLM 초기화 성공: {settings.llm_provider}::{settings.llm_model}")
        except Exception as e:
            print(f"[ERROR] LLM 초기화 실패: {str(e)}")
            print(f"   - 공급자: {settings.llm_provider}")
            print(f"   - 모델: {settings.llm_model}")
            print(f"   - 온도: {settings.llm_temperature}")
            self.llm = None
        
        # 최소한의 핵심 키워드만 유지 - LLM이 90% 담당
        self.critical_keywords = {
            "calendar_save": ["캘린더에 저장", "캘린더에 저장해줘", "저장해줘", "일정 등록", "캘린더 추가", "캘린더에", "저장", "넣어줘", "넣어", "추가해줘", "추가해"],
            "recipe_search": ["레시피", "조리법", "만들어줘"],
            "meal_plan": ["식단표", "식단 계획", "일주일", "7일"],
            "place_search": ["맛집", "식당", "근처"]
        }
    
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
        
        # 1. LLM 분류 우선 시도 (90% 담당)
        if self.llm:
            try:
                print(f"🔍 LLM 분류 시도: '{text}'")
                llm_result = await self._llm_classify(text, context)
                print(f"    [LLM] LLM 분류: {llm_result['intent'].value} (신뢰도: {llm_result['confidence']:.2f})")
                
                # LLM 결과가 최소 신뢰도 이상이면 바로 반환
                if llm_result["confidence"] >= self.LLM_MIN_CONFIDENCE:
                    print(f"✅ LLM 분류 성공: {llm_result['intent'].value}")
                    return llm_result
                else:
                    print(f"❌ LLM 신뢰도 부족: {llm_result['confidence']:.2f} < {self.LLM_MIN_CONFIDENCE}")
                    
            except Exception as e:
                print(f"    [ERROR] LLM 분류 실패: {str(e)}")
        else:
            print("❌ LLM이 초기화되지 않음")
        
        # 2. LLM 실패시에만 최소한의 키워드 분류 사용 (10% 담당)
        keyword_result = self._minimal_keyword_classify(text)
        print(f"    [KEYWORD] 키워드 분류: {keyword_result['intent'].value} (신뢰도: {keyword_result['confidence']:.2f})")
        return keyword_result
    
    def _minimal_keyword_classify(self, text: str) -> Dict[str, Any]:
        """최소한의 키워드만으로 분류 - LLM 실패시에만 사용"""
        
        print(f"🔍 키워드 분류 시작: '{text}'")
        
        # 매우 명확한 경우만 키워드로 처리
        for intent_name, keywords in self.critical_keywords.items():
            print(f"🔍 {intent_name} 키워드 검사: {keywords}")
            matched_keywords = [kw for kw in keywords if kw in text]
            if matched_keywords:
                print(f"✅ {intent_name} 매칭됨: {matched_keywords}")
                intent_map = {
                    "calendar_save": Intent.CALENDAR_SAVE,
                    "recipe_search": Intent.RECIPE_SEARCH,
                    "meal_plan": Intent.MEAL_PLAN,
                    "place_search": Intent.PLACE_SEARCH
                }
                return {
                    "intent": intent_map[intent_name],
                    "confidence": 0.7,
                    "method": "minimal_keyword",
                    "detected_keywords": matched_keywords
                }
        
        print("❌ 키워드 매칭 실패 - GENERAL로 폴백")
        # 나머지는 모두 LLM이 판단하도록 GENERAL로 폴백
        return {
            "intent": Intent.GENERAL,
            "confidence": 0.5,
            "method": "fallback"
        }
    
    
    def _validate_intent(self, text: str, initial_intent: Intent) -> Intent:
        """의도 검증 및 수정 - 간소화"""
        # LLM 우선 방식에서는 검증 로직을 최소화
        return initial_intent
    
    async def _llm_classify(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """LLM 기반 정확한 분류 - 프롬프트 파일 사용"""
        
        # intent_classification.py의 프롬프트 사용
        prompt = get_intent_prompt(user_input)
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # JSON 파싱
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # Intent Enum으로 변환
                intent_map = {
                    "recipe_search": Intent.RECIPE_SEARCH,
                    "meal_plan": Intent.MEAL_PLAN,
                    "place_search": Intent.PLACE_SEARCH,
                    "calendar_save": Intent.CALENDAR_SAVE,
                    "general": Intent.GENERAL
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
    
