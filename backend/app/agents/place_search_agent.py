"""
식당 검색 전용 에이전트
RAG + 카카오 API 하이브리드 검색을 통한 키토 친화적 식당 추천

오케스트레이터에서 분리된 식당 검색 로직을 담당
"""

import asyncio
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

from app.core.config import settings
from app.tools.restaurant.place_search import PlaceSearchTool
from app.tools.restaurant.restaurant_hybrid_search import restaurant_hybrid_search_tool
from app.tools.meal.keto_score import KetoScoreCalculator
from app.prompts.restaurant.search_improvement import PLACE_SEARCH_IMPROVEMENT_PROMPT

class PlaceSearchAgent:
    """키토 친화적 식당 검색 전용 에이전트"""
    
    def __init__(self):
        """에이전트 초기화"""
        try:
            # Gemini LLM 초기화
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=settings.gemini_temperature,
                max_tokens=settings.gemini_max_tokens
            )
        except Exception as e:
            print(f"❌ Gemini AI 초기화 실패: {e}")
            self.llm = None
        
        # 도구들 초기화
        self.place_search = PlaceSearchTool()
        self.restaurant_hybrid_search = restaurant_hybrid_search_tool
        self.keto_score = KetoScoreCalculator()
        
        print("✅ PlaceSearchAgent 초기화 완료")
    
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
                    timeout=30.0  # 30초 타임아웃
                )
            except asyncio.TimeoutError:
                print(f"⏰ 검색 타임아웃 (30초)")
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
        
        # 1. RAG와 카카오 검색을 병렬로 실행 (성능 개선)
        print("  🚀 RAG와 카카오 API 병렬 검색 시작...")
        
        rag_task = asyncio.create_task(self._execute_rag_search(message, lat, lng))
        kakao_task = asyncio.create_task(self._execute_kakao_search(message, lat, lng, radius_km))
        
        # 병렬 실행 완료 대기
        rag_results, kakao_results = await asyncio.gather(
            rag_task, kakao_task, return_exceptions=True
        )
        
        # 예외 처리
        if isinstance(rag_results, Exception):
            print(f"  ❌ RAG 검색 실패: {rag_results}")
            rag_results = []
        
        if isinstance(kakao_results, Exception):
            print(f"  ❌ 카카오 검색 실패: {kakao_results}")
            kakao_results = []
        
        # 2. 결과 통합 및 정렬
        final_results = self._integrate_and_sort_results(rag_results, kakao_results)
        
        # 3. 응답 생성 (간단한 버전으로 최적화)
        response = await self._generate_fast_response(message, final_results, profile)
        
        return {
            "results": final_results[:10],  # 상위 10개
            "response": response,
            "search_stats": {
                "rag_results": len(rag_results) if isinstance(rag_results, list) else 0,
                "kakao_results": len(kakao_results) if isinstance(kakao_results, list) else 0,
                "final_results": len(final_results),
                "location": {"lat": lat, "lng": lng}
            },
            "tool_calls": [{
                "tool": "place_search_agent",
                "rag_results": len(rag_results) if isinstance(rag_results, list) else 0,
                "kakao_results": len(kakao_results) if isinstance(kakao_results, list) else 0,
                "final_results": len(final_results),
                "location": {"lat": lat, "lng": lng}
            }]
        }
    
    async def _execute_rag_search(self, message: str, lat: float, lng: float) -> List[Dict[str, Any]]:
        """RAG 검색 실행"""
        print("  🤖 RAG 검색 실행 중...")
        try:
            rag_results = await self.restaurant_hybrid_search.hybrid_search(
                query=message,
                location={"lat": lat, "lng": lng},
                max_results=10
            )
            print(f"  ✅ RAG 검색 결과: {len(rag_results)}개")
            return rag_results
        except Exception as e:
            print(f"  ❌ RAG 검색 실패: {e}")
            return []
    
    async def _execute_kakao_search(
        self, 
        message: str, 
        lat: float, 
        lng: float, 
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """카카오 API 검색 실행"""
        print("  📍 카카오 API 검색 실행 중...")
        try:
            # 검색 쿼리 개선
            search_keywords = await self._improve_search_keywords(message)
            
            all_places = []
            
            # 각 키워드로 검색
            for keyword in search_keywords[:3]:  # 최대 3개 키워드
                places = await self.place_search.search(
                    query=keyword.strip('"'),
                    lat=lat,
                    lng=lng,
                    radius=int(radius_km * 1000)
                )
                
                # 키토 스코어 계산 및 메타데이터 추가
                for place in places:
                    score_result = self.keto_score.calculate_score(
                        name=place.get("name", ""),
                        category=place.get("category", ""),
                        address=place.get("address", "")
                    )
                    
                    place.update({
                        "keto_score": score_result["score"],
                        "why": score_result["reasons"],
                        "tips": score_result["tips"],
                        "source": "kakao_api"
                    })
                    
                    all_places.append(place)
            
            # 중복 제거
            unique_places = {}
            for place in all_places:
                place_id = place.get("id", "")
                if place_id not in unique_places or place["keto_score"] > unique_places[place_id]["keto_score"]:
                    unique_places[place_id] = place
            
            kakao_results = list(unique_places.values())
            print(f"  ✅ 카카오 API 검색 결과: {len(kakao_results)}개")
            return kakao_results
            
        except Exception as e:
            print(f"  ❌ 카카오 API 검색 실패: {e}")
            return []
    
    async def _improve_search_keywords(self, message: str) -> List[str]:
        """LLM을 사용한 검색 키워드 개선 (타임아웃 적용)"""
        if not self.llm:
            return [message]
        
        try:
            query_improvement_prompt = PLACE_SEARCH_IMPROVEMENT_PROMPT.format(message=message)
            
            # 타임아웃 적용하여 LLM 호출
            llm_response = await asyncio.wait_for(
                self.llm.ainvoke([HumanMessage(content=query_improvement_prompt)]),
                timeout=15.0  # 15초 타임아웃
            )
            
            search_keywords = llm_response.content.strip().split(", ")
            print(f"  🔍 LLM 생성 키워드: {search_keywords[:3]}")
            return search_keywords
            
        except asyncio.TimeoutError:
            print(f"  ⏰ 키워드 개선 타임아웃 (15초) - 원본 메시지 사용")
            return [message]
            
        except Exception as e:
            print(f"  ❌ 키워드 개선 실패: {e}")
            return [message]
    
    def _integrate_and_sort_results(
        self, 
        rag_results: List[Dict[str, Any]], 
        kakao_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """RAG와 카카오 API 결과 통합 및 정렬"""
        print("  🔄 결과 통합 중...")
        all_results = []
        
        # RAG 결과 변환 (표준 포맷으로)
        for result in rag_results:
            all_results.append({
                "id": result.get("restaurant_id", ""),
                "name": result.get("restaurant_name", ""),
                "category": result.get("category", ""),
                "address": result.get("addr_road", result.get("addr_jibun", "")),
                "lat": result.get("lat", 0.0),
                "lng": result.get("lng", 0.0),
                "phone": result.get("phone", ""),
                "keto_score": result.get("keto_score", 0),
                "why": result.get("keto_reasons", {}),
                "tips": [],
                "source": "rag",
                "menu_info": {
                    "name": result.get("menu_name", ""),
                    "description": result.get("menu_description", ""),
                    "price": result.get("menu_price")
                },
                "similarity": result.get("similarity", 0.0),
                "final_score": result.get("final_score", 0.0)
            })
        
        # 카카오 결과 추가
        all_results.extend(kakao_results)
        
        # 중복 제거 (이름 + 주소 기준)
        unique_results = {}
        for result in all_results:
            key = f"{result.get('name', '')}_{result.get('address', '')}"
            if key not in unique_results:
                unique_results[key] = result
            else:
                # 더 높은 점수의 결과 선택
                existing_score = unique_results[key].get("keto_score", 0)
                current_score = result.get("keto_score", 0)
                if current_score > existing_score:
                    unique_results[key] = result
        
        # 최종 정렬 (키토 스코어 + RAG 점수 고려)
        final_results = sorted(
            unique_results.values(),
            key=lambda x: (x.get("keto_score", 0), x.get("final_score", 0), x.get("similarity", 0)),
            reverse=True
        )
        
        print(f"  ✅ 최종 결과: {len(final_results)}개 (RAG: {len(rag_results)}, 카카오: {len(kakao_results)})")
        return final_results
    
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
            # 간단한 프롬프트로 LLM 응답 생성 (성능 최적화)
            restaurant_list = ""
            for i, restaurant in enumerate(results[:3], 1):
                restaurant_list += f"{i}. {restaurant.get('name', '이름 없음')} (키토점수: {restaurant.get('keto_score', 0)}/100)\n"
                restaurant_list += f"   주소: {restaurant.get('address', '')}\n"
                
                # RAG 결과인 경우 메뉴 정보 추가
                if restaurant.get('source') == 'rag' and restaurant.get('menu_info', {}).get('name'):
                    menu_info = restaurant.get('menu_info', {})
                    restaurant_list += f"   추천메뉴: {menu_info.get('name', '')}"
                    if menu_info.get('price'):
                        restaurant_list += f" ({menu_info.get('price')}원)"
                    restaurant_list += "\n"
                restaurant_list += "\n"
            
            # 프로필 정보 (간단하게)
            profile_text = ""
            if profile:
                allergies = profile.get("allergies", [])
                if allergies:
                    profile_text = f"알레르기: {', '.join(allergies)}"
            
            # 간단한 프롬프트 (토큰 수 최소화)
            simple_prompt = f"""사용자 요청: "{message}"

찾은 키토 식당들:
{restaurant_list}

{f"사용자 알레르기: {profile_text}" if profile_text else ""}

위 식당들을 친근하게 추천해주세요. 키토 다이어트에 좋은 이유를 간단히 설명하고, 각 식당의 특징을 언급해주세요. 200자 이내로 간결하게 작성해주세요."""
            
            # 타임아웃 적용하여 LLM 호출
            llm_response = await asyncio.wait_for(
                self.llm.ainvoke([HumanMessage(content=simple_prompt)]),
                timeout=20.0  # 20초 타임아웃
            )
            
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
                "rag_results": 0,
                "kakao_results": 0,
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
                "rag_results": 0,
                "kakao_results": 0,
                "final_results": 0,
                "location": {"lat": 37.4979, "lng": 127.0276}
            },
            "tool_calls": [{
                "tool": "place_search_agent",
                "status": "timeout",
                "timeout_seconds": 30.0
            }]
        }
