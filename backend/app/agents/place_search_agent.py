"""
식당 검색 전용 에이전트
하이브리드 검색(RAG + 벡터 검색)을 통한 키토 친화적 식당 추천

오케스트레이터에서 분리된 식당 검색 로직을 담당

팀원 개인화 가이드:
1. config/.personal_config.py에서 RESTAURANT_AGENT_CONFIG 수정
2. 개인 프롬프트 파일을 restaurant/ 폴더에 생성
3. USE_PERSONAL_CONFIG를 True로 설정하여 활성화
"""

import asyncio
import importlib
from typing import Dict, Any, List, Optional
from langchain.schema import HumanMessage

from app.tools.restaurant.restaurant_hybrid_search import restaurant_hybrid_search_tool
from app.tools.meal.keto_score import KetoScoreCalculator
from config import get_personal_configs, get_agent_config
from app.core.llm_factory import create_chat_llm

class PlaceSearchAgent:
    """키토 친화적 식당 검색 전용 에이전트"""
    
    # 기본 설정 (개인 설정이 없을 때 사용)
    DEFAULT_AGENT_NAME = "Place Search Agent"
    DEFAULT_PROMPT_FILES = {
        "search_improvement": "search_improvement",  # 검색 개선 프롬프트
        "search_failure": "search_failure",  # 검색 실패 프롬프트
        "recommendation": "recommendation",  # 식당 추천 프롬프트
        "fallback": "fallback"  # 폴백 프롬프트
    }
    
    def __init__(self, prompt_files: Dict[str, str] = None, agent_name: str = None):
        """에이전트 초기화"""
        # 개인 설정 로드
        personal_configs = get_personal_configs()
        agent_config = get_agent_config("restaurant_agent", personal_configs)
        
        # 개인화된 설정 적용 (우선순위: 매개변수 > 개인설정 > 기본설정)
        self.prompt_files = prompt_files or agent_config.get("prompts", self.DEFAULT_PROMPT_FILES)
        self.agent_name = agent_name or agent_config.get("agent_name", self.DEFAULT_AGENT_NAME)
        
        # 동적 프롬프트 로딩
        self.prompts = self._load_prompts()
        
        print(f"✅ {self.agent_name} 초기화 (프롬프트: {list(self.prompts.keys())})")
        
        try:
            # PlaceSearchAgent 전용 LLM 설정 사용
            from app.core.config import settings
            self.llm = create_chat_llm(
                provider=settings.place_search_provider,
                model=settings.place_search_model,
                temperature=settings.place_search_temperature,
                max_tokens=settings.place_search_max_tokens,
                timeout=settings.place_search_timeout
            )
            print(f"✅ PlaceSearchAgent LLM 초기화: {settings.place_search_provider}/{settings.place_search_model}")
        except Exception as e:
            print(f"❌ PlaceSearchAgent LLM 초기화 실패: {e}")
            self.llm = None
        
        # 도구들 초기화
        self.restaurant_hybrid_search = restaurant_hybrid_search_tool
        self.keto_score = KetoScoreCalculator()
        
        print("✅ PlaceSearchAgent 초기화 완료")
    
    def _load_prompts(self) -> Dict[str, str]:
        """프롬프트 파일들 동적 로딩"""
        prompts = {}
        
        for key, filename in self.prompt_files.items():
            try:
                module_path = f"app.prompts.restaurant.{filename}"
                prompt_module = importlib.import_module(module_path)
                
                # 다양한 프롬프트 속성명 지원
                possible_names = [
                    f"{key.upper()}_PROMPT",  # RECOMMENDATION_PROMPT
                    f"RESTAURANT_{key.upper()}_PROMPT",  # RESTAURANT_RECOMMENDATION_PROMPT
                    f"PLACE_{key.upper()}_PROMPT",  # PLACE_RECOMMENDATION_PROMPT
                    "RESTAURANT_RECOMMENDATION_PROMPT",  # recommendation의 경우
                    "PROMPT",
                    filename.upper().replace("_", "_") + "_PROMPT"
                ]
                
                prompt_found = False
                for name in possible_names:
                    if hasattr(prompt_module, name):
                        prompts[key] = getattr(prompt_module, name)
                        prompt_found = True
                        print(f"  ✅ {key} 프롬프트 로드: {filename}.{name}")
                        break
                
                if not prompt_found:
                    print(f"  ⚠️ {filename}에서 프롬프트를 찾을 수 없습니다. 기본 프롬프트 사용.")
                    prompts[key] = self._get_default_prompt(key)
                    
            except ImportError as e:
                print(f"  ⚠️ {filename} 프롬프트 파일을 찾을 수 없습니다: {e}. 기본 프롬프트 사용.")
                prompts[key] = self._get_default_prompt(key)
        
        return prompts
    
    def _get_default_prompt(self, key: str) -> str:
        """기본 프롬프트 템플릿"""
        try:
            if key == "search_improvement":
                from app.prompts.restaurant.search_improvement import PLACE_SEARCH_IMPROVEMENT_PROMPT
                return PLACE_SEARCH_IMPROVEMENT_PROMPT
            elif key == "search_failure":
                from app.prompts.restaurant.search_failure import SEARCH_FAILURE_PROMPT
                return SEARCH_FAILURE_PROMPT
            elif key == "recommendation":
                from app.prompts.restaurant.recommendation import RESTAURANT_RECOMMENDATION_PROMPT
                return RESTAURANT_RECOMMENDATION_PROMPT
            elif key == "fallback":
                from app.prompts.restaurant.fallback import FALLBACK_RECOMMENDATION_PROMPT
                return FALLBACK_RECOMMENDATION_PROMPT
        except ImportError:
            pass
        
        # 최종 폴백
        try:
            from app.prompts.restaurant.fallback import (
                FALLBACK_RECOMMENDATION_PROMPT,
                FALLBACK_SEARCH_FAILURE_PROMPT,
                FALLBACK_SEARCH_IMPROVEMENT_PROMPT
            )
            
            fallback_defaults = {
                "recommendation": FALLBACK_RECOMMENDATION_PROMPT,
                "search_failure": FALLBACK_SEARCH_FAILURE_PROMPT,
                "search_improvement": FALLBACK_SEARCH_IMPROVEMENT_PROMPT,
                "fallback": FALLBACK_RECOMMENDATION_PROMPT
            }
            
            return fallback_defaults.get(key, "키토 친화적 식당을 추천하세요.")
            
        except ImportError:
            # 정말 마지막 폴백
            return f"키토 친화적 식당 {key} 작업을 수행하세요."
    
    async def search_places(
        self,
        message: str,
        location: Optional[Dict[str, float]] = None,
        radius_km: float = 5.0,
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        식당 검색 메인 함수 (성능 최적화 버전)
        
        Args:
            message: 사용자 검색 메시지
            location: 위치 정보 {"lat": float, "lng": float}
            radius_km: 검색 반경 (km)
            profile: 사용자 프로필 정보
            
        Returns:
            검색 결과 딕셔너리
        """
        try:
            # 위치 정보 설정
            lat = location.get("lat", 37.4979) if location else 37.4979  # 기본: 강남역
            lng = location.get("lng", 127.0276) if location else 127.0276
            
            print(f"🔍 PlaceSearchAgent 검색 시작: '{message}' (위치: {lat}, {lng})")
            
            # 전체 검색에 타임아웃 적용
            try:
                return await asyncio.wait_for(
                    self._execute_search_with_timeout(message, lat, lng, radius_km, profile),
                    timeout=90.0  # 90초 타임아웃으로 증가
                )
            except asyncio.TimeoutError:
                print(f"⏰ 검색 타임아웃 (90초)")
                return self._get_timeout_response()
            
        except Exception as e:
            print(f"❌ PlaceSearchAgent 검색 실패: {e}")
            return self._get_error_response(str(e))
    
    async def _execute_search_with_timeout(
        self, 
        message: str, 
        lat: float, 
        lng: float, 
        radius_km: float, 
        profile: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """타임아웃이 적용된 검색 실행"""
        
        # 1. 하이브리드 검색 실행 (벡터 + 키워드 + RAG)
        print("  🚀 하이브리드 검색 시작...")
        
        try:
            # 하이브리드 검색 실행
            hybrid_results = await self.restaurant_hybrid_search.hybrid_search(
                query=message,
                location={"lat": lat, "lng": lng},
                max_results=20
            )
            
            print(f"  ✅ 하이브리드 검색 결과: {len(hybrid_results)}개")
            
            # 결과를 표준 형식으로 변환
            formatted_results = []
            for result in hybrid_results:
                formatted_results.append({
                    "place_id": str(result.get("restaurant_id", "")),
                    "name": result.get("restaurant_name", ""),
                    "address": result.get("addr_road", result.get("addr_jibun", "")),
                    "category": result.get("category", ""),
                    "lat": float(result.get("lat", 0.0)),
                    "lng": float(result.get("lng", 0.0)),
                    "keto_score": result.get("keto_score", 0),
                    "menu_name": result.get("menu_name", ""),
                    "menu_description": result.get("menu_description", ""),
                    "why": [f"하이브리드 검색: {message}"] if result.get("menu_name") else ["키토 친화 식당"],
                    "tips": result.get("keto_reasons", []) if result.get("keto_reasons") else ["메뉴 선택 시 주의하세요"],
                    "similarity_score": result.get("similarity", 0.0),
                    "search_type": result.get("search_type", "hybrid"),
                    "source": "hybrid_search",
                    "source_url": result.get("source_url")
                })
            
            # 응답 생성
            response = await self._generate_fast_response(message, formatted_results, profile)
            
            return {
                "results": formatted_results[:10],  # 상위 10개
                "response": response,
                "search_stats": {
                    "hybrid_results": len(formatted_results),
                    "final_results": len(formatted_results),
                    "location": {"lat": lat, "lng": lng}
                },
                "tool_calls": [{
                    "tool": "place_search_agent",
                    "hybrid_results": len(formatted_results),
                    "final_results": len(formatted_results),
                    "location": {"lat": lat, "lng": lng}
                }]
            }
            
        except Exception as e:
            print(f"  ❌ 하이브리드 검색 실패: {e}")
            return self._get_error_response(f"하이브리드 검색 실패: {str(e)}")
    
    # 카카오 API 관련 함수들 제거됨 - 이제 하이브리드 검색만 사용
    
    # 더 이상 사용하지 않는 함수들 제거됨 - 하이브리드 검색에서 모든 것을 처리
    
    async def _generate_fast_response(
        self, 
        message: str, 
        results: List[Dict[str, Any]], 
        profile: Optional[Dict[str, Any]]
    ) -> str:
        """빠른 응답 생성 (LLM 사용, 간단한 프롬프트)"""
        if not results:
            return "죄송합니다. 요청하신 조건에 맞는 식당을 찾을 수 없습니다. 다른 지역이나 키워드로 다시 시도해보세요."
        
        if not self.llm:
            # LLM이 없는 경우 템플릿 기반 응답
            response = f"🍽️ **키토 친화적 식당 {len(results)}곳을 찾았습니다!**\n\n"
            
            for i, restaurant in enumerate(results[:3], 1):
                response += f"**{i}. {restaurant.get('name', '이름 없음')}**\n"
                response += f"📍 {restaurant.get('address', '')}\n"
                response += f"⭐ 키토 점수: {restaurant.get('keto_score', 0)}/100\n\n"
            
            return response
        
        try:
            # 시간 측정 시작
            import time
            start_time = time.time()
            
            # 구조화된 프롬프트로 LLM 응답 생성
            restaurant_list = ""
            for i, restaurant in enumerate(results[:3], 1):
                restaurant_list += f"{i}. {restaurant.get('name', '이름 없음')}\n"
                restaurant_list += f"   - 키토 점수: {restaurant.get('keto_score', 0)}/100\n"
                restaurant_list += f"   - 주소: {restaurant.get('address', '')}\n"
                restaurant_list += f"   - 카테고리: {restaurant.get('category', '')}\n"
                
                # 메뉴 정보 추가
                if restaurant.get('menu_name'):
                    restaurant_list += f"   - 대표 메뉴: {restaurant.get('menu_name', '')}\n"
                if restaurant.get('menu_description'):
                    restaurant_list += f"   - 메뉴 설명: {restaurant.get('menu_description', '')}\n"
                
                # 키토 관련 정보
                if restaurant.get('keto_reasons'):
                    reasons = restaurant.get('keto_reasons', [])
                    if isinstance(reasons, list) and reasons:
                        restaurant_list += f"   - 키토 친화 이유: {', '.join(reasons)}\n"
                
                # 출처 URL 추가
                if restaurant.get('source_url'):
                    restaurant_list += f"   - 출처 URL: {restaurant.get('source_url')}\n"
                
                restaurant_list += "\n"
            
            # 프로필 정보 구조화
            profile_text = "없음"
            if profile:
                profile_parts = []
                if profile.get("allergies"):
                    profile_parts.append(f"알레르기: {', '.join(profile.get('allergies', []))}")
                if profile.get("disliked_foods"):
                    profile_parts.append(f"비선호 음식: {', '.join(profile.get('disliked_foods', []))}")
                if profile_parts:
                    profile_text = " | ".join(profile_parts)
            
            # 동적으로 로드된 프롬프트 사용
            recommendation_prompt = self.prompts.get("recommendation", "")
            if not recommendation_prompt:
                print("⚠️ recommendation 프롬프트가 없습니다. 기본 프롬프트 사용.")
                recommendation_prompt = self._get_default_prompt("recommendation")
            
            structured_prompt = recommendation_prompt.format(
                message=message,
                restaurants=restaurant_list,
                profile=profile_text
            )
            
            # 🔍 디버깅: 실제 프롬프트 내용 확인
            print(f"\n{'='*60}")
            print("🔍 LLM에 전달되는 프롬프트:")
            print(f"{'='*60}")
            print(structured_prompt[:500])  # 처음 500자만 출력
            print(f"{'='*60}")
            print(f"✅ 프롬프트 길이: {len(structured_prompt)} 글자")
            print(f"✅ '냥체' 포함 여부: {'냥체' in structured_prompt}")
            print(f"✅ '응답 형식' 포함 여부: {'응답 형식' in structured_prompt}")
            print(f"✅ '키토 점수' 포함 여부: {'키토 점수' in structured_prompt}")
            print(f"{'='*60}\n")
            
            # LLM 호출 시간 측정
            llm_start_time = time.time()
            
            # 타임아웃 적용하여 LLM 호출 (타임아웃 증가)
            llm_response = await asyncio.wait_for(
                self.llm.ainvoke([HumanMessage(content=structured_prompt)]),
                timeout=180.0  # 180초 타임아웃으로 증가
            )
            
            llm_end_time = time.time()
            llm_duration = llm_end_time - llm_start_time
            
            # 시간 측정 종료
            end_time = time.time()
            total_time = end_time - start_time
            
            # 🔍 디버깅: LLM 응답 확인
            print(f"\n{'='*60}")
            print("🤖 LLM 응답 (처음 300자):")
            print(f"{'='*60}")
            print(llm_response.content[:300])
            print(f"{'='*60}")
            print(f"✅ 응답 길이: {len(llm_response.content)} 글자")
            print(f"✅ '🍽️' 포함 여부: {'🍽️' in llm_response.content}")
            print(f"✅ '냥' 포함 여부: {'냥' in llm_response.content}")
            print(f"✅ '키토 점수' 포함 여부: {'키토 점수' in llm_response.content}")
            print(f"⏱️ 총 생성 시간: {total_time:.2f}초")
            print(f"{'='*60}\n")
            
            return llm_response.content
            
        except asyncio.TimeoutError:
            print(f"⏰ LLM 응답 생성 타임아웃 (20초)")
            # 타임아웃 시 템플릿 기반 응답으로 폴백
            return f"🍽️ 키토 친화적 식당 {len(results)}곳을 찾았습니다!\n\n" + \
                   "\n".join([f"• {r.get('name', '이름 없음')} (키토점수: {r.get('keto_score', 0)}/100)" 
                             for r in results[:3]])
            
        except Exception as e:
            print(f"❌ 빠른 응답 생성 실패: {e}")
            # 에러 시 템플릿 기반 응답으로 폴백
            return f"총 {len(results)}개의 키토 친화적 식당을 찾았습니다. 키토 다이어트에 적합한 곳들을 선별했습니다."
    
    def _get_error_response(self, error_message: str) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "results": [],
            "response": f"식당 검색 중 오류가 발생했습니다: {error_message}",
            "search_stats": {
                "hybrid_results": 0,
                "final_results": 0,
                "location": {"lat": 37.4979, "lng": 127.0276}
            },
            "tool_calls": [{
                "tool": "place_search_agent",
                "error": error_message,
                "status": "failed"
            }]
        }
    
    def _get_timeout_response(self) -> Dict[str, Any]:
        """타임아웃 응답 생성"""
        return {
            "results": [],
            "response": "⏰ 식당 검색 시간이 초과되었습니다.\n\n💡 **해결 방법:**\n• 더 구체적인 지역명으로 검색해보세요\n• 간단한 키워드로 다시 시도해보세요\n• 잠시 후 다시 시도해보세요",
            "search_stats": {
                "hybrid_results": 0,
                "final_results": 0,
                "location": {"lat": 37.4979, "lng": 127.0276}
            },
            "tool_calls": [{
                "tool": "place_search_agent",
                "status": "timeout",
                "timeout_seconds": 30.0
            }]
        }
