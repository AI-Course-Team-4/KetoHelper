"""
레시피 검색 결과 응답 생성 프롬프트
검색된 레시피 정보를 바탕으로 사용자에게 친근하고 도움이 되는 응답 생성
"""

from app.prompts.shared.common_templates import create_standard_prompt

# 레시피 검색 결과 응답 생성 프롬프트 (공통 템플릿 사용)
_base_recipe_prompt = """
사용자의 레시피 요청에 답변해주세요.

사용자 요청: {message}

사용자 프로필: {profile_context}

검색된 레시피 정보:
{context}

다음 형식으로 답변해주세요:

## 🍽️ 추천 키토 레시피

위에서 검색된 레시피들을 바탕으로 키토 식단에 적합한 레시피를 추천드립니다.

### 💡 키토 팁
검색된 레시피와 관련된 실용적인 키토 식단 조언을 2~3가지만 간단하게 작성해주세요.

더 자세한 정보가 필요하시면 언제든 말씀해주세요!
"""

RECIPE_RESPONSE_GENERATION_PROMPT = create_standard_prompt(_base_recipe_prompt)

# 레시피 검색 실패 시 폴백 프롬프트 (공통 템플릿 사용)
_base_failure_recipe_prompt = """
사용자의 레시피 요청에 답변해주세요.

사용자 요청: {message}

사용자 프로필: {profile_context}

죄송하지만 요청하신 레시피를 찾을 수 없습니다. 대신 키토 식단에 적합한 기본 레시피를 추천드립니다.

## 🍽️ 키토 기본 레시피

### 💡 키토 식단 기본 원칙
- **탄수화물**: 하루 20-50g 이하
- **단백질**: 적정량 섭취 (체중 1kg당 1-1.5g)
- **지방**: 총 칼로리의 70-80%

### 🥑 추천 식품
**섭취 권장:**
- 고기, 생선, 계란
- 아보카도, 견과류
- 녹색 채소, 브로콜리

**피해야 할 식품:**
- 곡류, 과일 (소량 베리류 제외)
- 설탕, 가공식품
- 감자, 당근 등 뿌리채소

더 구체적인 레시피가 필요하시면 다른 키워드로 다시 검색해보세요!
"""

RECIPE_SEARCH_FAILURE_PROMPT = create_standard_prompt(_base_failure_recipe_prompt)

# 레시피 상세 정보 응답 프롬프트
RECIPE_DETAIL_RESPONSE_PROMPT = """
키토 식단 전문가로서 레시피 상세 정보를 제공해주세요.

사용자 요청: {message}

레시피 정보:
{recipe_details}

다음 형식으로 상세 정보를 제공해주세요:

## 🍽️ {recipe_title}

### 📋 재료 (2인분)
{ingredients}

### 👨‍🍳 조리법
{steps}

### 📊 영양 정보 (1인분 기준)
- 칼로리: {calories}kcal
- 탄수화물: {carbs}g
- 단백질: {protein}g
- 지방: {fat}g

### 💡 키토 성공 팁
이 레시피와 관련된 실용적인 키토 식단 조언을 2가지만 간단하게 작성해주세요.
"""
