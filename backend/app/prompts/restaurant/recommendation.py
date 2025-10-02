"""
식당 추천용 프롬프트
팀원들이 복사하여 개인화할 수 있는 템플릿
"""

RESTAURANT_RECOMMENDATION_PROMPT = """
키토 식당을 추천해주세요.

사용자 요청: "{message}"
식당 목록:
{restaurants}

사용자 프로필: {profile}

추천 가이드라인:
1. 각 식당의 키토 친화도와 그 이유 설명
2. 키토 식단에 적합한 메뉴나 주문 팁 제공
3. 사용자 프로필(알레르기, 비선호 음식)을 고려한 개인화 조언
4. 식당별로 키토 관점에서의 장점과 주의사항 명시
5. 친근하고 실용적인 톤으로 작성

응답 형식:
🍽️ **추천 식당 TOP 3**

**1. [식당명]**
- 🥩 추천 메뉴: [메뉴명]
- 💡 주문 팁: [팁]

**2. [식당명]**
- 🥩 추천 메뉴: [메뉴명]
- 💡 주문 팁: [팁]

**3. [식당명]**
- 🥩 추천 메뉴: [메뉴명]
- 💡 주문 팁: [팁]

🎯 **개인 맞춤 조언**
[추가 조언]

실용적이고 친근한 톤으로 작성해주세요.
"""

# Restaurant Agent에서 분리된 기본 프롬프트
DEFAULT_RECOMMENDATION_PROMPT = """
검색된 식당들을 바탕으로 개인화된 추천을 생성하세요.

사용자 요청: "{message}"
식당 목록: {restaurants}
사용자 프로필: {profile}

키토 관점에서 각 식당의 장점과 주문 팁을 포함한 추천을 제공해주세요.
"""

# 대안 접근용
RECOMMENDATION_PROMPT = RESTAURANT_RECOMMENDATION_PROMPT
PROMPT = RESTAURANT_RECOMMENDATION_PROMPT
