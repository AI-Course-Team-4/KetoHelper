"""
캘린더 저장 관련 프롬프트들
"""

# 캘린더 저장 확인 프롬프트
CALENDAR_SAVE_CONFIRMATION_PROMPT = """
사용자가 식단을 캘린더에 저장하고 싶어합니다.

사용자 요청: "{message}"
저장 정보:
- 시작 날짜: {start_date}
- 기간: {duration_days}일
- 저장된 식단 개수: {meal_count}개

다음 사항을 포함하여 친근하고 확신에 찬 응답을 생성해주세요:
1. 저장 완료 확인
2. 저장된 기간과 내용 요약
3. 캘린더 확인 안내
4. 추가 도움 제안

응답은 따뜻하고 친근한 톤으로 작성해주세요.
"""

# 캘린더 저장 실패 프롬프트
CALENDAR_SAVE_FAILURE_PROMPT = """
사용자가 식단을 캘린더에 저장하려 했지만 실패했습니다.

사용자 요청: "{message}"
실패 이유: {error_reason}

다음 사항을 포함하여 응답해주세요:
1. 저장 실패에 대한 사과
2. 구체적인 실패 이유 설명
3. 해결 방법 제안
4. 다시 시도할 수 있는 방법 안내

응답은 이해하기 쉽고 도움이 되는 톤으로 작성해주세요.
"""

# 캘린더 저장 전 식단 데이터 확인 프롬프트
CALENDAR_MEAL_PLAN_VALIDATION_PROMPT = """
사용자가 캘린더에 저장하려는 식단 데이터를 검증해주세요.

식단 데이터:
{meal_plan_data}

다음 사항을 확인하고 JSON 형태로 응답해주세요:
1. 식단 데이터의 완성도 (complete/incomplete)
2. 누락된 정보가 있는지 (missing_info: [])
3. 저장 가능 여부 (saveable: true/false)
4. 사용자에게 전달할 메시지 (message)

응답 형태:
{{
    "complete": true/false,
    "missing_info": [],
    "saveable": true/false,
    "message": "사용자에게 전달할 메시지"
}}
"""

# 식당 캘린더 저장 프롬프트 (추후 확장용)
RESTAURANT_CALENDAR_SAVE_PROMPT = """
사용자가 식당 정보를 캘린더에 저장하고 싶어합니다.

사용자 요청: "{message}"
식당 정보:
- 이름: {restaurant_name}
- 주소: {restaurant_address}
- 카테고리: {restaurant_category}
- 키토 점수: {keto_score}

저장 일정:
- 날짜: {target_date}
- 시간: {meal_time}

식당 방문 일정이 캘린더에 저장되었음을 친근하게 안내하고,
키토 다이어트 팁을 함께 제공해주세요.
"""