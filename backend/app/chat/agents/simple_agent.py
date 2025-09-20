"""
일반 채팅 전용 키토 코치 에이전트
레시피/식당 검색이 아닌 일반적인 키토 식단 상담 처리

팀원 개인화 가이드:
1. PROMPT_FILE_NAME을 변경하여 자신만의 프롬프트 파일 사용
2. AGENT_NAME을 변경하여 개인 브랜딩
3. 프롬프트 파일은 chat/prompts/ 폴더에 생성
"""

from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
import importlib

from app.core.config import settings

class SimpleKetoCoachAgent:
    """일반 채팅 전용 키토 코치 에이전트"""
    
    # 개인화 설정 - 이 부분을 수정하여 자신만의 에이전트 만들기
    AGENT_NAME = "Simple Keto Coach"
    PROMPT_FILE_NAME = "general_chat_prompt"  # chat/prompts/ 폴더의 파일명
    
    def __init__(self, prompt_file_name: str = None, agent_name: str = None):
        # 개인화된 설정 적용
        self.prompt_file_name = prompt_file_name or self.PROMPT_FILE_NAME
        self.agent_name = agent_name or self.AGENT_NAME
        
        # 동적 프롬프트 로딩
        self.prompt_template = self._load_prompt_template()
        
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
    
    def _load_prompt_template(self) -> str:
        """프롬프트 템플릿 동적 로딩"""
        try:
            # 프롬프트 모듈 동적 import
            module_path = f"app.chat.prompts.{self.prompt_file_name}"
            prompt_module = importlib.import_module(module_path)
            
            # GENERAL_CHAT_PROMPT 또는 PROMPT 속성 찾기
            if hasattr(prompt_module, 'GENERAL_CHAT_PROMPT'):
                return prompt_module.GENERAL_CHAT_PROMPT
            elif hasattr(prompt_module, 'PROMPT'):
                return prompt_module.PROMPT
            else:
                print(f"경고: {self.prompt_file_name}에서 프롬프트를 찾을 수 없습니다. 기본 프롬프트 사용.")
                return self._get_default_prompt()
            
        except ImportError:
            print(f"경고: {self.prompt_file_name} 프롬프트 파일을 찾을 수 없습니다. 기본 프롬프트 사용.")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """기본 프롬프트 템플릿 (프롬프트 파일에서 로드)"""
        try:
            from app.chat.prompts.general_chat_prompt import DEFAULT_CHAT_PROMPT
            return DEFAULT_CHAT_PROMPT
        except ImportError:
            # 폴백 프롬프트 파일에서 로드
            try:
                from app.chat.prompts.fallback_prompts import FALLBACK_GENERAL_CHAT_PROMPT
                return FALLBACK_GENERAL_CHAT_PROMPT
            except ImportError:
                # 정말 마지막 폴백
                return "키토 식단에 대해 질문해주세요. 질문: {message}, 프로필: {profile_context}"
    
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
        """일반 채팅 응답 생성 (개인화된 프롬프트 사용)"""
        
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
            
            # 개인화된 프롬프트 템플릿 사용
            prompt = self.prompt_template.format(
                message=message,
                profile_context=profile_context if profile_context else '특별한 제약사항 없음'
            )
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            return f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def stream_response(self, *args, **kwargs):
        """스트리밍 응답"""
        result = await self.process_message(*args, **kwargs)
        yield {"event": "complete", **result}
    
