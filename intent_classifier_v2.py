"""
IntentClassifier — keyword-first hybrid router with LLM fallback.

Features
- 5-way internal intents: mealplan, recipe, place, calendar_save, general_chat
- Normalization (NFKC), boundary-aware keyword matching
- Thresholded decision: HIGH_TH → skip LLM (speed), MID_TH → LLM verify
- Safe enum mapping: maps to app.core.types.Intent if members exist, else graceful fallbacks
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import re
import unicodedata

# 프로젝트 타입(열거형) — 기존 Enum을 그대로 사용.
# 일부 멤버(RECIPE, GENERAL_CHAT)가 없을 수 있어 안전 접근합니다.
from enum import Enum
class Intent(Enum):
    MEAL_PLANNING = "mealplan"
    RESTAURANT_SEARCH = "place"
    CALENDAR_SAVE = "calendar_save"
    GENERAL = "general"
    # 선택적 멤버 (없을 수도 있음)
    RECIPE = "recipe"
    GENERAL_CHAT = "general_chat"

# 하위 호환성을 위한 별칭
_Intent = Intent


class IntentClassifier:
    # ── 조절 가능한 임계값 ───────────────────────────────────────────────
    HIGH_TH = 2.0          # 키워드만으로 확정(LLM 스킵) - 더 높게 설정
    MID_TH = 0.3           # LLM 검증 구간 하한 - 더 낮게 설정
    LLM_CONFIRM_TH = 0.6   # LLM이 확정으로 받아들일 최소 confidence

    def __init__(self, llm: Optional[Any] = None):
        """
        llm: async callable or client with .invoke(...) alike, 사용처는 _llm_classify
        """
        if llm is None:
            # LLM이 제공되지 않으면 Gemini API 자동 연결 시도
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                import os
                from dotenv import load_dotenv
                
                # .env 파일 로드
                load_dotenv()
                
                # 환경 변수에서 직접 읽기
                google_api_key = os.getenv("GOOGLE_API_KEY", "")
                llm_model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
                
                if not google_api_key:
                    raise ValueError("GOOGLE_API_KEY not found in environment variables")
                
                self.llm = ChatGoogleGenerativeAI(
                    model=llm_model,
                    google_api_key=google_api_key,
                    temperature=0.1
                )
            except Exception as e:
                self.llm = None
        else:
            self.llm = llm

        # ── 의도명 통일: place 사용(restaurant → place) ────────────────
        # 더 일반적이고 견고한 키워드 규칙
        self.keyword_rules: Dict[str, Dict[str, List[str]]] = {
            "mealplan": {
                "high_priority": ["식단표", "일주일", "주간", "계획"],
                "medium_priority": ["식단", "메뉴"],
                "context_keywords": ["만들어", "생성", "짜줘"],
            },
            "recipe": {
                "high_priority": ["레시피", "조리법", "만드는법", "요리법"],
                "context_keywords": ["어떻게", "방법", "만들어"],
            },
            "place": {
                "high_priority": ["식당", "맛집", "음식점", "카페", "레스토랑"],
                "location_keywords": ["근처", "주변", "어디", "위치"],
            },
            "calendar_save": {
                "high_priority": ["캘린더", "일정", "저장", "등록"],
            },
            "general_chat": {
                "greetings": ["안녕", "하이", "헬로", "반가워"],
                "thanks": ["고마워", "감사", "고맙"],
                "help": ["도움", "help", "뭐해"],
                "memory_keywords": ["기억해", "외워", "알레르기", "싫어하는"],  # memory를 general_chat으로 이동
            },
        }

        # 편의 키워드 묶음(로그/검증용)
        self.calendar_save_keywords = ["캘린더", "일정", "저장", "등록"]

    # ── 전처리: NFKC + 소문자 + 특수문자/다중공백 정리 ────────────────
    def _normalize(self, s: str) -> str:
        s = unicodedata.normalize("NFKC", s).lower()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"[^\w\s가-힣]", " ", s)
        return s.strip()

    # ── 단어 경계 기반 키워드 매칭 (부분문자열 오탐 방지) ────────────────
    def _has_kw(self, text: str, kw: str) -> bool:
        return re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", text) is not None

    # ── 캘린더 저장 의도: 최우선 감지(두 단어 이상 동시 등장 가산점) ─────
    def _has_calendar_save_intent(self, text: str) -> bool:
        hits = sum(1 for kw in self.calendar_save_keywords if self._has_kw(text, kw))
        return hits >= 2 or any(self._has_kw(text, kw) for kw in self.calendar_save_keywords)

    # ── 키워드 점수 계산(가중치 테이블) ────────────────────────────────
    def _calculate_keyword_score(self, text: str, intent: str) -> float:
        score = 0.0
        rules = self.keyword_rules.get(intent, {})

        for kw in rules.get("high_priority", []):
            if self._has_kw(text, kw):
                score += 2.0  # 높은 가중치
        for kw in rules.get("medium_priority", []):
            if self._has_kw(text, kw):
                score += 1.0
        for kw in rules.get("context_keywords", []):
            if self._has_kw(text, kw):
                score += 0.3  # 낮은 가중치
        for kw in rules.get("location_keywords", []):
            if self._has_kw(text, kw):
                score += 1.5
        for kw in rules.get("food_keywords", []):
            if self._has_kw(text, kw):
                score += 1.2
        for kw in rules.get("greetings", []):
            if self._has_kw(text, kw):
                score += 2.0
        for kw in rules.get("thanks", []):
            if self._has_kw(text, kw):
                score += 2.0
        for kw in rules.get("help", []):
            if self._has_kw(text, kw):
                score += 1.5
        for kw in rules.get("memory_keywords", []):
            if self._has_kw(text, kw):
                score += 1.5  # memory 키워드를 general_chat으로 처리
        # 특수 가산점: calendar_save는 2개 이상 동시 등장 시 +0.5
        if intent == "calendar_save":
            hits = sum(1 for kw in self.calendar_save_keywords if self._has_kw(text, kw))
            if hits >= 2:
                score += 0.5
        return score

    # ── 키워드 기반 1차 분류 ──────────────────────────────────────────
    def _keyword_classify(self, text: str) -> Dict[str, Any]:
        intents = ["mealplan", "recipe", "place", "calendar_save", "general_chat"]
        scores: Dict[str, float] = {it: 0.0 for it in intents}
        detected: List[str] = []

        for it in intents:
            add = self._calculate_keyword_score(text, it)
            scores[it] += add
            if add > 0:
                # 어떤 규칙에 걸렸는지 간단 로깅용
                detected.append(it)

        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]

        # 키워드 스코어를 0~1로 정규화(상한 4.0 가정)
        confidence = min(max_score / 4.0, 1.0)

        return {
            "intent": best_intent,              # 내부 문자열
            "confidence": confidence,           # 0~1
            "method": "keyword",
            "debug": {"scores": scores, "detected": detected},
        }

    # ── LLM 분류 (프로젝트의 프롬프트/클라이언트 규약에 맞춰 구현) ─────
    async def _llm_classify(self, user_input: str, context: str = "") -> Dict[str, Any]:
        """
        LLM이 다음 JSON 형식으로 반환한다고 가정:
        {"intent": "<mealplan|recipe|place|calendar_save|memory|general_chat>", "confidence": 0~1, "reasoning": "..."}
        """
        if self.llm is None:
            # LLM 미연결일 때의 안전 폴백: 키워드 결과로 대체
            kw = self._keyword_classify(self._normalize(user_input))
            kw["method"] = "keyword_fallback_no_llm"
            return self._finalize_keyword_result(kw)

        # 실제 LLM 프롬프트 생성
        prompt = f"""사용자의 입력을 분석하여 다음 5가지 의도 중 하나로 분류해주세요:

1. mealplan: 식단표, 일주일 계획, 주간 메뉴 등 식단 계획 관련
2. recipe: 레시피, 조리법, 요리법, 특정 음식 만드는 방법
3. place: 식당, 맛집, 음식점, 카페 등 장소 검색 관련
4. calendar_save: 캘린더 저장, 일정 등록, 캘린더 관련
5. general_chat: 인사, 감사, 도움말, 기억해달라는 요청 등 일반 대화

사용자 입력: "{user_input}"
{f"대화 맥락: {context}" if context else ""}

JSON 형식으로 응답:
{{
    "intent": "mealplan|recipe|place|calendar_save|general_chat",
    "confidence": 0.0-1.0,
    "reasoning": "분류 이유"
}}"""

        try:
            from langchain.schema import HumanMessage
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # JSON 파싱
            import json
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                return {
                    "intent": self._map_to_intent_enum(result["intent"]),
                    "confidence": result.get("confidence", 0.8),
                    "method": "llm",
                    "reasoning": result.get("reasoning", "")
                }
        except Exception as e:
            print(f"LLM 분류 오류: {e}")
        
        # 실패시 키워드 결과 반환
        kw = self._keyword_classify(self._normalize(user_input))
        return {
            "intent": self._map_to_intent_enum(kw["intent"]),
            "confidence": min(kw["confidence"], 0.65),
            "method": "llm_fallback",
            "reasoning": "LLM 분류 실패, 키워드 결과 사용",
        }

    # ── 의도 검증/보정(경계 키워드로 간단히 sanity-check) ───────────────
    def _validate_intent(self, text: str, best_intent: str):
        # 캘린더 저장 의도 강화
        if any(self._has_kw(text, kw) for kw in ["캘린더", "저장", "일정", "등록"]):
            if any(self._has_kw(text, kw) for kw in ["식단", "일주일", "만든"]):
                return self._map_to_intent_enum("calendar_save")
        
        # 메모리 관련 키워드는 일반 대화로 처리
        if any(self._has_kw(text, kw) for kw in ["기억해", "외워", "알레르기", "싫어하는"]):
            return self._map_to_intent_enum("general_chat")
        
        # 일반 대화 의도 강화
        if any(self._has_kw(text, kw) for kw in ["안녕", "고마워", "도움", "뭐해", "반가워"]):
            return self._map_to_intent_enum("general_chat")
        
        # 장소 검색 의도 강화
        if any(self._has_kw(text, kw) for kw in ["근처", "주변", "어디", "뭐가", "맛있는"]):
            if not any(self._has_kw(text, kw) for kw in ["식단표", "일주일", "레시피", "조리법"]):
                return self._map_to_intent_enum("place")
        
        # recipe vs mealplan 구분 강화
        if best_intent == "recipe":
            if any(self._has_kw(text, kw) for kw in ["일주일", "주간", "식단표", "3일치", "아침", "점심", "저녁", "간식"]):
                best_intent = "mealplan"
        elif best_intent == "mealplan":
            if any(self._has_kw(text, kw) for kw in ["레시피", "조리법", "만드는법", "요리법"]):
                # 구체 음식명 & 레시피 성향이 강하면 recipe로 보정
                if any(self._has_kw(text, kw) for kw in self.keyword_rules["recipe"].get("food_keywords", [])):
                    best_intent = "recipe"

        return self._map_to_intent_enum(best_intent)

    # ── 최종 결과(키워드) 정리: enum 매핑/신뢰도 조정 ───────────────────
    def _finalize_keyword_result(self, kw: Dict[str, Any]) -> Dict[str, Any]:
        mapped = self._map_to_intent_enum(kw["intent"])
        return {**kw, "intent": mapped}

    # ── 외부 공개: 하이브리드 분류 ─────────────────────────────────────
    async def classify(self, user_input: str, context: str = "") -> Dict[str, Any]:
        text = self._normalize(user_input)

        # 0) 캘린더 저장: 최우선 처리
        if self._has_calendar_save_intent(text):
            return {
                "intent": self._safe_enum("CALENDAR_SAVE"),
                "confidence": 0.95,
                "method": "keyword",
                "details": {
                    "detected_keywords": [kw for kw in self.calendar_save_keywords if self._has_kw(text, kw)],
                    "message": "캘린더 저장 요청",
                },
            }

        # 1) 키워드 1차 분류
        keyword_result = self._keyword_classify(text)
        best_intent = keyword_result["intent"]
        max_conf = keyword_result["confidence"]

        # 2) HIGH_TH 이상은 즉시 확정(LLM 스킵 → 속도↑)
        if max_conf >= self.HIGH_TH:
            intent = self._validate_intent(text, best_intent)
            keyword_result["intent"] = intent
            return keyword_result

        # 3) LLM이 있으면 더 적극적으로 활용
        if self.llm:
            llm_result = await self._llm_classify(user_input, context)
            if llm_result.get("confidence", 0.0) > self.LLM_CONFIRM_TH:
                return llm_result
            # LLM이 확신을 못 주면 키워드 결과 사용(보정 포함)
            intent = self._validate_intent(text, best_intent)
            keyword_result["intent"] = intent
            keyword_result["method"] = "keyword_fallback"
            return keyword_result

        # 4) LLM이 없을 때 키워드 결과라도 enum으로 매핑해서 반환
        return self._finalize_keyword_result(keyword_result)

    # ── 문자열 의도를 프로젝트 Enum으로 안전 매핑 ─────────────────────
    def _map_to_intent_enum(self, intent_str: str):
        """
        프로젝트의 app.core.types.Intent에 다음 멤버가 있을 수도/없을 수도 있음:
        - RECIPE, GENERAL_CHAT
        없으면 다음과 같이 안전 폴백:
        - RECIPE    → MEAL_PLANNING
        - GENERAL_CHAT → GENERAL
        기타: place→RESTAURANT_SEARCH, calendar_save→CALENDAR_SAVE, mealplan→MEAL_PLANNING
        """
        if intent_str == "mealplan":
            return self._safe_enum("MEAL_PLANNING")
        if intent_str == "recipe":
            return self._safe_enum("RECIPE", fallback="MEAL_PLANNING")
        if intent_str == "place":
            return self._safe_enum("RESTAURANT_SEARCH")
        if intent_str == "calendar_save":
            return self._safe_enum("CALENDAR_SAVE", fallback="GENERAL")
        if intent_str == "general_chat":
            return self._safe_enum("GENERAL_CHAT", fallback="GENERAL")
        return self._safe_enum("GENERAL")

    # ── 안전 Enum 접근 헬퍼 ────────────────────────────────────────────
    def _safe_enum(self, name: str, fallback: Optional[str] = None):
        """
        _Intent에 name 멤버가 없으면 fallback → GENERAL 순으로 폴백
        """
        if hasattr(_Intent, name):
            return getattr(_Intent, name)
        if fallback and hasattr(_Intent, fallback):
            return getattr(_Intent, fallback)
        return getattr(_Intent, "GENERAL")
