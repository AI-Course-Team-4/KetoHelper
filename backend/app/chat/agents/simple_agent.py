"""
일반 채팅 전용 키토 코치 에이전트
레시피/식당 검색이 아닌 일반적인 키토 식단 상담 처리
"""

from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

from app.core.config import settings

class SimpleKetoCoachAgent:
    """일반 채팅 전용 키토 코치 에이전트"""
    
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
    
    async def process_message(
        self,
        message: str,
        location: Optional[Dict[str, float]] = None,
        radius_km: float = 5.0,
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """일반 채팅 메시지 처리"""
        
        try:
            if not self.llm:
                return {
                    "response": "AI 서비스가 현재 사용할 수 없습니다. Google API 키를 확인해주세요.",
                    "intent": "general_chat",
                    "results": [],
                    "tool_calls": []
                }
            
            # 일반 채팅 응답 생성
            response = await self._generate_general_response(message, profile)
            
            return {
                "response": response,
                "intent": "general_chat",
                "results": [],
                "tool_calls": [{"tool": "general_chat_agent", "message": message}]
            }
            
        except Exception as e:
            return {
                "response": f"처리 중 오류가 발생했습니다: {str(e)}",
                "intent": "error",
                "results": [],
                "tool_calls": []
            }
    
    async def _generate_general_response(self, message: str, profile: Optional[Dict[str, Any]]) -> str:
        """일반 채팅 응답 생성"""
        
        try:
            # 프로필 정보 컨텍스트
            profile_context = ""
            if profile:
                if profile.get("allergies"):
                    profile_context += f"알레르기: {', '.join(profile['allergies'])}. "
                if profile.get("dislikes"):
                    profile_context += f"비선호 음식: {', '.join(profile['dislikes'])}. "
                if profile.get("goals_carbs_g"):
                    profile_context += f"목표 탄수화물: {profile['goals_carbs_g']}g/일. "
            
            # 일반 키토 상담 프롬프트
            prompt = f"""
키토 식단 전문가로서 다음 질문에 친근하고 도움이 되는 답변을 해주세요.

질문: {message}
사용자 프로필: {profile_context if profile_context else '특별한 제약사항 없음'}

답변 가이드라인:
1. 키토 식단 관련 질문에는 과학적이고 실용적인 조언 제공
2. 일반적인 인사나 대화에는 친근하게 응답하되 키토 주제로 자연스럽게 유도
3. 구체적인 레시피나 식당을 요청하면 전문 검색 서비스 이용을 안내
4. 개인의 건강 상태에 대한 의학적 조언은 피하고 전문의 상담 권유
5. 200-300자 내외로 간결하고 이해하기 쉽게 답변

특별한 경우 처리:
- "안녕", "안녕하세요" 등 인사: 친근한 인사 후 키토 식단 도움 제안
- "고마워", "감사해" 등 감사 인사: 따뜻한 응답 후 추가 도움 제안  
- "해볼게", "좋네" 등 모호한 대답: 구체적인 키토 관련 질문 유도
- 키토와 무관한 질문: 정중히 키토 식단 전문가임을 알리고 관련 질문 유도

친근하고 격려하는 톤으로 답변해주세요.
"""
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            return f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def stream_response(self, *args, **kwargs):
        """스트리밍 응답"""
        result = await self.process_message(*args, **kwargs)
        yield {"event": "complete", **result}
    
