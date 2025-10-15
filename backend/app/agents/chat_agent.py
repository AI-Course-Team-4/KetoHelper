"""
일반 채팅 전용 키토 코치 에이전트
레시피/식당 검색이 아닌 일반적인 키토 식단 상담 처리

팀원 개인화 가이드:
1. config/personal_config.py에서 CHAT_AGENT_CONFIG 수정
2. 개인 프롬프트 파일을 chat/prompts/ 폴더에 생성
3. USE_PERSONAL_CONFIG를 True로 설정하여 활성화
"""

from typing import Dict, Any, Optional
from langchain.schema import HumanMessage
import importlib

from app.core.llm_factory import create_chat_llm
from app.core.redis_cache import redis_cache
from app.core.semantic_cache import semantic_cache_service
from app.core.config import settings
from config import get_personal_configs, get_agent_config

class SimpleKetoCoachAgent:
    """일반 채팅 전용 키토 코치 에이전트"""
    
    # 기본 설정 (개인 설정이 없을 때 사용)
    DEFAULT_AGENT_NAME = "Simple Keto Coach"
    DEFAULT_PROMPT_FILE_NAME = "general_chat"  # chat/prompts/ 폴더의 파일명
    
    def __init__(self, prompt_file_name: str = None, agent_name: str = None):
        # 개인 설정 로드
        personal_configs = get_personal_configs()
        agent_config = get_agent_config("chat_agent", personal_configs)
        
        # 개인화된 설정 적용 (우선순위: 매개변수 > 개인설정 > 기본설정)
        self.prompt_file_name = prompt_file_name or agent_config.get("prompt_file_name", self.DEFAULT_PROMPT_FILE_NAME)
        self.agent_name = agent_name or agent_config.get("agent_name", self.DEFAULT_AGENT_NAME)
        
        # 동적 프롬프트 로딩
        self.prompt_template = self._load_prompt_template()
        
        try:
            # ChatAgent 전용 LLM 설정 사용
            from app.core.config import settings
            self.llm = create_chat_llm(
                provider=settings.chat_agent_provider,
                model=settings.chat_agent_model,
                temperature=settings.chat_agent_temperature,
                max_tokens=settings.chat_agent_max_tokens,
                timeout=settings.chat_agent_timeout
            )
            print(f"✅ ChatAgent LLM 초기화: {settings.chat_agent_provider}/{settings.chat_agent_model}")
            print(f"🔧 ChatAgent 설정: max_tokens={settings.chat_agent_max_tokens}, timeout={settings.chat_agent_timeout}s")
        except Exception as e:
            print(f"❌ ChatAgent LLM 초기화 실패: {e}")
            self.llm = None
    
    def _load_prompt_template(self) -> str:
        """프롬프트 템플릿 동적 로딩"""
        try:
            # 프롬프트 모듈 동적 import
            module_path = f"app.prompts.chat.{self.prompt_file_name}"
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
            from app.prompts.chat.general_chat import DEFAULT_CHAT_PROMPT
            return DEFAULT_CHAT_PROMPT
        except ImportError:
            # 폴백 프롬프트 파일에서 로드
            try:
                from app.prompts.chat.fallback import FALLBACK_GENERAL_CHAT_PROMPT
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
            
            # 🚀 일반 채팅 캐싱 로직 추가 (meal_planner와 동일한 방식)
            user_id = profile.get("user_id", "") if profile else ""
            allergies = profile.get("allergies", []) if profile else []
            dislikes = profile.get("dislikes", []) if profile else []
            
            cache_key = f"general_chat_{hash(message)}_{user_id}_{hash(tuple(sorted(allergies)))}_{hash(tuple(sorted(dislikes)))}"
            
            # 🔍 디버깅 로그 추가
            print(f"🔍 일반 채팅 캐시 키: {cache_key}")
            print(f"🔍 사용자 ID: {user_id}")
            print(f"🔍 알레르기 해시: {hash(tuple(sorted(allergies)))}")
            print(f"🔍 기피식품 해시: {hash(tuple(sorted(dislikes)))}")
            print(f"🔍 메시지 해시: {hash(message)}")
            
            # Redis 캐시 확인
            print(f"    🔍 캐시 확인 시작: {cache_key}")
            print(f"    🔍 Redis 활성화 상태: {redis_cache.is_enabled}")
            print(f"    🔍 Redis 객체: {redis_cache}")
            print(f"    🔍 Redis 타입: {type(redis_cache)}")
            
            try:
                cached_result = redis_cache.get(cache_key)
                print(f"    🔍 Redis get 결과: {cached_result is not None}")
            except Exception as e:
                print(f"    ❌ Redis get 오류: {e}")
                cached_result = None
            
            if cached_result:
                print(f"    ✅ Redis 일반 채팅 캐시 히트: {message[:30]}...")
                print(f"    ✅ 캐시된 응답 길이: {len(str(cached_result))} 문자")
                return cached_result
            
            # 시맨틱 캐시 확인 (정확 캐시 미스 시)
            if settings.semantic_cache_enabled:
                try:
                    model_ver = f"chat_agent_{settings.llm_model}"
                    opts_hash = f"{user_id}_{hash(tuple(sorted(allergies)))}_{hash(tuple(sorted(dislikes)))}"
                    
                    semantic_result = await semantic_cache_service.semantic_lookup(
                        message, user_id, model_ver, opts_hash
                    )
                    
                    if semantic_result:
                        print(f"    🧠 시맨틱 캐시 히트: 일반 채팅")
                        return semantic_result
                except Exception as e:
                    print(f"    ⚠️ 시맨틱 캐시 조회 오류: {e}")
            
            # 캐시 미스 시
                print(f"    ❌ Redis 일반 채팅 캐시 미스: {message[:30]}...")
                print(f"    ❌ 캐시 키: {cache_key}")
            
            # 일반 채팅 응답 생성
            response = await self._generate_general_response(message, profile)
            
            result_data = {
                "response": response,
                "intent": "general_chat",
                "results": [],
                "tool_calls": [{"tool": "general_chat_agent", "message": message}]
            }
            
            # 🚀 일반 채팅 결과 캐싱 (TTL: 30분)
            print(f"    💾 캐시 저장 시작: {cache_key}")
            redis_cache.set(cache_key, result_data, ttl=1800)
            print(f"    ✅ 일반 채팅 결과 캐시 저장 완료: {message[:30]}...")
            print(f"    ✅ 저장된 응답 길이: {len(str(result_data))} 문자")
            
            # 🧠 시맨틱 캐시 저장
            if settings.semantic_cache_enabled:
                try:
                    model_ver = f"chat_agent_{settings.llm_model}"
                    opts_hash = f"{user_id}_{hash(tuple(sorted(allergies)))}_{hash(tuple(sorted(dislikes)))}"
                    
                    meta = {
                        "route": "general_chat",
                        "allergies": allergies,
                        "dislikes": dislikes
                    }
                    
                    await semantic_cache_service.save_semantic_cache(
                        message, user_id, model_ver, opts_hash, 
                        result_data.get("response", ""), meta
                    )
                except Exception as e:
                    print(f"    ⚠️ 시맨틱 캐시 저장 오류: {e}")
            
            return result_data
            
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
            # 🚀 일반 채팅 캐싱 로직 추가 (meal_planner와 동일한 방식)
            user_id = profile.get("user_id", "") if profile else ""
            allergies = profile.get("allergies", []) if profile else []
            dislikes = profile.get("dislikes", []) if profile else []
            
            cache_key = f"general_chat_response_{hash(message)}_{user_id}_{hash(tuple(sorted(allergies)))}_{hash(tuple(sorted(dislikes)))}"
            
            # 🔍 디버깅 로그 추가
            print(f"🔍 _generate_general_response 캐시 키: {cache_key}")
            print(f"🔍 사용자 ID: {user_id}")
            print(f"🔍 알레르기 해시: {hash(tuple(sorted(allergies)))}")
            print(f"🔍 기피식품 해시: {hash(tuple(sorted(dislikes)))}")
            print(f"🔍 메시지 해시: {hash(message)}")
            
            # Redis 캐시 확인
            print(f"    🔍 캐시 확인 시작: {cache_key}")
            print(f"    🔍 Redis 활성화 상태: {redis_cache.is_enabled}")
            print(f"    🔍 Redis 객체: {redis_cache}")
            print(f"    🔍 Redis 타입: {type(redis_cache)}")
            
            try:
                cached_result = redis_cache.get(cache_key)
                print(f"    🔍 Redis get 결과: {cached_result is not None}")
            except Exception as e:
                print(f"    ❌ Redis get 오류: {e}")
                cached_result = None
            
            if cached_result:
                print(f"    ✅ Redis 일반 채팅 응답 캐시 히트: {message[:30]}...")
                print(f"    ✅ 캐시된 응답 길이: {len(str(cached_result))} 문자")
                return cached_result
            else:
                print(f"    ❌ Redis 일반 채팅 응답 캐시 미스: {message[:30]}...")
                print(f"    ❌ 캐시 키: {cache_key}")
            
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
            response_content = response.content
            
            # 🚀 일반 채팅 응답 캐싱 (TTL: 30분)
            print(f"    💾 캐시 저장 시작: {cache_key}")
            redis_cache.set(cache_key, response_content, ttl=1800)
            print(f"    ✅ 일반 채팅 응답 캐시 저장 완료: {message[:30]}...")
            print(f"    ✅ 저장된 응답 길이: {len(str(response_content))} 문자")
            
            return response_content
            
        except Exception as e:
            return f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def stream_response(self, *args, **kwargs):
        """스트리밍 응답"""
        result = await self.process_message(*args, **kwargs)
        yield {"event": "complete", **result}
    
