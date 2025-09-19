"""
AI 기반 키토 레시피 생성 에이전트
사용자 요청에 맞는 새로운 키토 레시피를 생성
"""

from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

from app.core.config import settings

class RecipeGeneratorAgent:
    """AI 기반 키토 레시피 생성 에이전트"""
    
    def __init__(self):
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=settings.gemini_temperature,
                max_tokens=settings.gemini_max_tokens
            )
        except Exception as e:
            print(f"Gemini AI 초기화 실패: {e}")
            self.llm = None
    
    async def generate_recipe(self, message: str, profile_context: str = "") -> str:
        """Gemini를 사용하여 새로운 키토 레시피 생성"""
        
        if not self.llm:
            return self._get_fallback_response(message)
        
        try:
            # Gemini에 맞게 최적화된 프롬프트
            prompt = f"""당신은 키토 식단 전문가입니다. '{message}'에 대한 맞춤 키토 레시피를 생성해주세요.

사용자 정보: {profile_context if profile_context else '특별한 제약사항 없음'}

다음 형식을 정확히 따라 답변해주세요:

## ✨ {message} (키토 버전)

### 📋 재료 (2인분)
**주재료:**
- [구체적인 재료와 정확한 분량]

**부재료:**
- [구체적인 재료와 정확한 분량]

**키토 대체재:**
- [일반 재료 → 키토 재료로 변경 설명]

### 👨‍🍳 조리법
1. [첫 번째 단계 - 구체적이고 명확하게]
2. [두 번째 단계 - 구체적이고 명확하게]
3. [세 번째 단계 - 구체적이고 명확하게]
4. [완성 및 마무리 단계]

### 📊 영양 정보 (1인분 기준)
- 칼로리: 000kcal
- 탄수화물: 0g
- 단백질: 00g
- 지방: 00g

### 💡 키토 성공 팁
- [키토 식단에 맞는 구체적 조언]
- [조리 시 주의사항]
- [보관 및 활용법]

**중요 지침**: 
아래 영양 기준을 내부적으로만 사용하여 정확한 영양소 계산을 하되, 이 기준 자체는 사용자에게 보여주지 마세요:
- 1인분 탄수화물: 5-10g 유지
- 1인분 단백질: 20-30g 
- 1인분 지방: 30-40g
- 총 칼로리: 400-600kcal 범위  
- 매크로 비율: 탄수화물 5-10%, 단백질 15-25%, 지방 70-80%

친근하고 실용적인 톤으로 작성하되, 위 영양 기준을 철저히 준수해주세요. 구분선(---)이나 내부 기준은 절대 출력하지 마세요."""
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            print(f"🤖 Gemini 레시피 생성 완료: {len(response.content)} 글자")
            return response.content
            
        except Exception as e:
            print(f"🚫 Gemini 레시피 생성 오류: {e}")
            return self._get_fallback_response(message)
    
    def _get_fallback_response(self, message: str) -> str:
        """AI 서비스 실패 시 대체 응답"""
        return f"""
🚫 '{message}' 레시피 생성 중 오류가 발생했습니다.

키토 식단에 도움이 될 수 있는 일반적인 조언을 드릴게요:

💡 키토 식단의 기본 원칙:
- 탄수화물: 20-50g/일 이하
- 지방: 70-80% (고품질 지방)
- 단백질: 15-25% (적당량)

🍽️ '{message}'에 대한 키토 조언:
- 키토 친화적인 대체 재료 사용
- 설탕 대신 스테비아, 에리스리톨 사용
- 밀가루 대신 아몬드 가루, 코코넛 가루 사용
- 고지방, 저탄수화물 조리법 적용

🔍 다시 시도해보시거나 다른 키워드로 검색해보세요!
"""
