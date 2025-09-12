"""
간단한 키토 코치 에이전트 (LangGraph 호환성 문제 해결용)
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

from app.core.config import settings
from app.tools.hybrid_search import hybrid_search_tool

class SimpleKetoCoachAgent:
    """간단한 키토 코치 에이전트"""
    
    def __init__(self):
        try:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.openai_api_key,
                temperature=0.1
            )
        except Exception as e:
            print(f"OpenAI 초기화 실패: {e}")
            self.llm = None
    
    async def process_message(
        self,
        message: str,
        location: Optional[Dict[str, float]] = None,
        radius_km: float = 5.0,
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """간단한 메시지 처리"""
        
        try:
            if not self.llm:
                return {
                    "response": "AI 서비스가 현재 사용할 수 없습니다. OpenAI API 키를 확인해주세요.",
                    "intent": "error",
                    "results": [],
                    "tool_calls": []
                }
            
            # 간단한 의도 분류
            intent = self._classify_intent(message)
            
            # 의도에 따른 응답 생성
            response = await self._generate_response(message, intent, profile)
            
            return {
                "response": response,
                "intent": intent,
                "results": [],
                "tool_calls": [{"tool": "simple_agent", "message": message}]
            }
            
        except Exception as e:
            return {
                "response": f"처리 중 오류가 발생했습니다: {str(e)}",
                "intent": "error",
                "results": [],
                "tool_calls": []
            }
    
    def _classify_intent(self, message: str) -> str:
        """간단한 의도 분류"""
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["레시피", "요리", "만들", "조리", "식단", "추천", "메뉴"]):
            return "recipe"
        elif any(word in message_lower for word in ["식당", "맛집", "근처", "주변"]):
            return "place"
        elif any(word in message_lower for word in ["식단표", "계획", "일주일", "7일"]):
            return "mealplan"
        elif any(word in message_lower for word in ["알레르기", "프로필", "설정"]):
            return "memory"
        else:
            return "other"
    
    async def _generate_response(
        self, 
        message: str, 
        intent: str, 
        profile: Optional[Dict[str, Any]]
    ) -> str:
        """의도에 따른 응답 생성"""
        
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
            
            # 의도별 프롬프트
            if intent == "recipe":
                # Supabase 하이브리드 검색
                try:
                    print(f"🔍 하이브리드 검색 실행: '{message}'")
                    recipes = await hybrid_search_tool.search(message, profile_context, max_results=3)
                    
                    # 검색 결과가 있으면 Supabase 데이터 사용
                    if recipes:
                        recipe_info = ""
                        for i, recipe in enumerate(recipes[:2], 1):
                            recipe_info += f"\n{i}. {recipe.get('title', '제목 없음')}\n"
                            recipe_info += f"   내용: {recipe.get('content', '내용 없음')}\n"
                            recipe_info += f"   유사도: {recipe.get('similarity', 0):.2f}\n"
                            
                            # 메타데이터 정보 추가
                            metadata = recipe.get('metadata', {})
                            if metadata.get('ingredients'):
                                recipe_info += f"   재료: {metadata['ingredients']}\n"
                            if metadata.get('steps'):
                                recipe_info += f"   조리법: {metadata['steps']}\n"
                            if metadata.get('keto_score'):
                                recipe_info += f"   키토 점수: {metadata['keto_score']}\n"
                        
                        prompt = f"""
                        사용자가 키토 레시피를 요청했습니다.
                        요청: {message}
                        프로필: {profile_context}
                        
                        Supabase에서 검색된 레시피 정보:
                        {recipe_info}
                        
                        위 레시피 정보를 바탕으로 한국형 키토 레시피를 추천해주세요. 다음을 포함해주세요:
                        1. 추천 레시피 1-2개
                        2. 재료 및 조리법 간단 설명
                        3. 키토 친화적인 대체재 팁
                        4. 예상 탄수화물량
                        
                        친근하고 도움이 되는 톤으로 답변해주세요.
                        """
                    else:
                        # 검색 결과가 없으면 기본 프롬프트 사용
                        prompt = f"""
                        사용자가 키토 레시피를 요청했습니다.
                        요청: {message}
                        프로필: {profile_context}
                        
                        한국형 키토 레시피를 추천해주세요. 다음을 포함해주세요:
                        1. 추천 레시피 1-2개
                        2. 재료 및 조리법 간단 설명
                        3. 키토 친화적인 대체재 팁
                        4. 예상 탄수화물량
                        
                        친근하고 도움이 되는 톤으로 답변해주세요.
                        """
                except Exception as e:
                    print(f"Supabase 하이브리드 검색 오류: {e}")
                    # 오류 발생 시 기본 프롬프트 사용
                    prompt = f"""
                    사용자가 키토 레시피를 요청했습니다.
                    요청: {message}
                    프로필: {profile_context}
                    
                    한국형 키토 레시피를 추천해주세요. 다음을 포함해주세요:
                    1. 추천 레시피 1-2개
                    2. 재료 및 조리법 간단 설명
                    3. 키토 친화적인 대체재 팁
                    4. 예상 탄수화물량
                    
                    친근하고 도움이 되는 톤으로 답변해주세요.
                    """
            
            elif intent == "place":
                prompt = f"""
                사용자가 키토 친화적인 식당을 찾고 있습니다.
                요청: {message}
                프로필: {profile_context}
                
                키토 식단에 적합한 식당 유형과 주문 팁을 제공해주세요:
                1. 추천 식당 유형 (고기구이, 샤브샤브, 샐러드 등)
                2. 주문 시 주의사항 (밥 빼기, 양념 조심 등)
                3. 키토 점수가 높은 메뉴 추천
                
                실제 위치 정보가 없으므로 일반적인 조언을 해주세요.
                """
            
            elif intent == "mealplan":
                prompt = f"""
                사용자가 키토 식단표를 요청했습니다.
                요청: {message}
                프로필: {profile_context}
                
                7일 키토 식단 계획의 기본 구조를 제안해주세요:
                1. 아침/점심/저녁 메뉴 예시
                2. 일일 탄수화물 목표 (20-30g)
                3. 식단 실행 팁
                4. 주의사항
                
                개인화된 조언을 포함해주세요.
                """
            
            else:
                prompt = f"""
                키토 식단 전문가로서 다음 질문에 답해주세요.
                질문: {message}
                프로필: {profile_context}
                
                키토 식단의 기본 원칙과 실용적인 조언을 제공해주세요.
                친근하고 이해하기 쉬운 톤으로 답변해주세요.
                """
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            return f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def stream_response(self, *args, **kwargs):
        """스트리밍 응답 (향후 구현)"""
        result = await self.process_message(*args, **kwargs)
        yield {"event": "complete", **result}
