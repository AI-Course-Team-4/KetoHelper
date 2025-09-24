"""
가드레일 검증 로직
사용자 입력 검증, 보정, 정규화 함수들
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from ..models.guard_models import (
    ErrorCode, IntentType, GuardConfig, StockMessages
)


def clamp(value: int, min_val: int, max_val: int) -> int:
    """값을 지정된 범위로 제한"""
    return max(min_val, min(value, max_val))


def sanitize_str_list(values: List[str]) -> List[str]:
    """문자열 리스트 정리 (이모지, 공백, 제어문자 제거)"""
    if not values:
        return []
    
    # 간단한 정규식으로 이모지, 특수문자, 공백 제거
    pattern = re.compile(r'[^\w\s가-힣]', re.UNICODE)
    sanitized = []
    
    for value in values[:GuardConfig.MAX_ALLERGIES]:  # 최대 개수 제한
        if value and isinstance(value, str):
            # 기본 정리
            cleaned = value.strip()
            if cleaned:
                # 이모지와 특수문자 제거
                cleaned = pattern.sub('', cleaned)
                if cleaned.strip():  # 남은 내용이 있으면
                    sanitized.append(cleaned.strip())
    
    return sanitized


def detect_safety(utterance: str) -> bool:
    """안전성 위반 키워드 탐지"""
    utterance_lower = utterance.lower()
    
    for keyword in GuardConfig.FORBIDDEN_KEYWORDS:
        if keyword in utterance_lower:
            return True
    
    return False


def detect_off_topic(utterance: str) -> bool:
    """오프토픽 키워드 탐지"""
    utterance_lower = utterance.lower()
    
    # 키토/식단 관련 키워드가 있는지 확인
    keto_keywords = ["키토", "저탄고지", "식단", "레시피", "식당", "맛집", "음식", "요리"]
    has_keto_keyword = any(keyword in utterance_lower for keyword in keto_keywords)
    
    if has_keto_keyword:
        return False  # 키토 관련이면 오프토픽 아님
    
    # 오프토픽 키워드 확인
    for keyword in GuardConfig.OFF_TOPIC_KEYWORDS:
        if keyword in utterance_lower:
            return True
    
    return False


def detect_injection(utterance: str) -> bool:
    """프롬프트 인젝션 패턴 탐지"""
    utterance_lower = utterance.lower()
    
    for pattern in GuardConfig.INJECTION_PATTERNS:
        if pattern in utterance_lower:
            return True
    
    return False


def fill_defaults(slots: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """기본값 채우기 및 범위 보정"""
    normalized = {}
    auto_corrections = {}
    
    # 위치 기본값 설정
    location = slots.get("location", "")
    if not location or location.strip() == "":
        normalized["location"] = GuardConfig.DEFAULT_LOCATION
        auto_corrections["location"] = GuardConfig.DEFAULT_LOCATION
    else:
        normalized["location"] = location.strip()
    
    # 거리 보정
    distance = slots.get("distance_m")
    if distance is None:
        normalized["distance_m"] = GuardConfig.DEFAULT_DISTANCE_M
        auto_corrections["distance_m"] = GuardConfig.DEFAULT_DISTANCE_M
    else:
        try:
            distance_int = int(distance)
            corrected = clamp(distance_int, GuardConfig.DISTANCE_MIN, GuardConfig.DISTANCE_MAX)
            normalized["distance_m"] = corrected
            if corrected != distance_int:
                auto_corrections["distance_m"] = corrected
        except (ValueError, TypeError):
            normalized["distance_m"] = GuardConfig.DEFAULT_DISTANCE_M
            auto_corrections["distance_m"] = GuardConfig.DEFAULT_DISTANCE_M
    
    # 예산 보정
    budget = slots.get("budget_krw")
    if budget is None:
        normalized["budget_krw"] = GuardConfig.DEFAULT_BUDGET_KRW
        auto_corrections["budget_krw"] = GuardConfig.DEFAULT_BUDGET_KRW
    else:
        try:
            budget_int = int(budget)
            corrected = clamp(budget_int, GuardConfig.BUDGET_MIN, GuardConfig.BUDGET_MAX)
            normalized["budget_krw"] = corrected
            if corrected != budget_int:
                auto_corrections["budget_krw"] = corrected
        except (ValueError, TypeError):
            normalized["budget_krw"] = GuardConfig.DEFAULT_BUDGET_KRW
            auto_corrections["budget_krw"] = GuardConfig.DEFAULT_BUDGET_KRW
    
    # 탄수화물 한도 보정
    carb_limit = slots.get("carb_limit_g")
    if carb_limit is None:
        normalized["carb_limit_g"] = GuardConfig.DEFAULT_CARB_LIMIT_G
        auto_corrections["carb_limit_g"] = GuardConfig.DEFAULT_CARB_LIMIT_G
    else:
        try:
            carb_int = int(carb_limit)
            corrected = clamp(carb_int, GuardConfig.CARB_MIN, GuardConfig.CARB_MAX)
            normalized["carb_limit_g"] = corrected
            if corrected != carb_int:
                auto_corrections["carb_limit_g"] = corrected
        except (ValueError, TypeError):
            normalized["carb_limit_g"] = GuardConfig.DEFAULT_CARB_LIMIT_G
            auto_corrections["carb_limit_g"] = GuardConfig.DEFAULT_CARB_LIMIT_G
    
    # 칼로리 한도 보정
    kcal_limit = slots.get("kcal_limit")
    if kcal_limit is None:
        normalized["kcal_limit"] = GuardConfig.DEFAULT_KCAL_LIMIT
        auto_corrections["kcal_limit"] = GuardConfig.DEFAULT_KCAL_LIMIT
    else:
        try:
            kcal_int = int(kcal_limit)
            corrected = clamp(kcal_int, GuardConfig.KCAL_MIN, GuardConfig.KCAL_MAX)
            normalized["kcal_limit"] = corrected
            if corrected != kcal_int:
                auto_corrections["kcal_limit"] = corrected
        except (ValueError, TypeError):
            normalized["kcal_limit"] = GuardConfig.DEFAULT_KCAL_LIMIT
            auto_corrections["kcal_limit"] = GuardConfig.DEFAULT_KCAL_LIMIT
    
    # 리스트 필드 정리
    allergies = slots.get("allergies", [])
    if allergies:
        normalized["allergies"] = sanitize_str_list(allergies)
    else:
        normalized["allergies"] = []
    
    dislikes = slots.get("dislikes", [])
    if dislikes:
        normalized["dislikes"] = sanitize_str_list(dislikes)
    else:
        normalized["dislikes"] = []
    
    # 기타 필드들
    for key in ["time_of_day", "spice_level", "open_now"]:
        if key in slots:
            normalized[key] = slots[key]
        else:
            normalized[key] = None
    
    return normalized, auto_corrections


def check_required(intent: Optional[str], slots: Dict[str, Any]) -> List[str]:
    """의도별 필수 슬롯 확인"""
    missing = []
    
    if not intent:
        return missing
    
    # MEAL_PLANNING 의도 체크
    if intent in [IntentType.MEAL_PLANNING, IntentType.BOTH]:
        if not slots.get("time_of_day") and not slots.get("carb_limit_g"):
            missing.extend(["time_of_day", "carb_limit_g"])
    
    # RESTAURANT_SEARCH 의도 체크
    if intent in [IntentType.RESTAURANT_SEARCH, IntentType.BOTH]:
        if not slots.get("distance_m") and not slots.get("budget_krw"):
            missing.extend(["distance_m", "budget_krw"])
    
    return missing


def validate_and_normalize(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Dict[str, Any], str, List[str]]:
    """
    전체 검증 및 정규화
    
    Returns:
        (ok, normalized_slots, auto_corrections, error_code, missing_slots)
    """
    utterance = payload.get("utterance", "")
    expected_intent = payload.get("expected_intent")
    slots = payload.get("slots", {})
    
    # 1. 안전성 검사
    if detect_safety(utterance):
        return False, {}, {}, ErrorCode.SAFETY, []
    
    # 2. 인젝션 검사
    if detect_injection(utterance):
        return False, {}, {}, ErrorCode.INJECTION, []
    
    # 3. 오프토픽 검사
    if detect_off_topic(utterance):
        return False, {}, {}, ErrorCode.OFF_TOPIC, []
    
    # 4. 기본값 채우기 및 보정
    normalized_slots, auto_corrections = fill_defaults(slots)
    
    # 5. 필수 슬롯 확인
    missing_slots = check_required(expected_intent, normalized_slots)
    if missing_slots:
        return False, normalized_slots, auto_corrections, ErrorCode.MISSING_SLOT, missing_slots
    
    # 6. 성공
    return True, normalized_slots, auto_corrections, "", []
