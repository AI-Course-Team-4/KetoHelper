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
from app.core.semantic_cache import semantic_cache_service
from app.core.config import settings
from config import get_personal_configs, get_agent_config
from app.core.llm_factory import create_chat_llm
from app.core.redis_cache import redis_cache
import hashlib
import json
import random
import re

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

    def _format_quick_response(self, message: str, results: List[Dict[str, Any]]) -> str:
        """LLM 없이 빠르게 구성하는 간단 응답 텍스트(풀 캐시용).
        상위 3개 항목만 요약해 가벼운 응답을 만든다.
        """
        if not results:
            return "죄송합니다. 조건에 맞는 식당을 찾지 못했습니다. 다른 키워드로 다시 시도해 주세요."
        lines = ["🍽️ 키토 친화적 식당을 추천합니다:"]
        for i, r in enumerate(results[:3], 1):
            name = r.get("name", "이름 없음")
            addr = r.get("address", "")
            menu = r.get("menu_name") or "키토 친화 메뉴"
            lines.append(f"{i}. {name} - {menu} | {addr}")
        return "\n".join(lines)

    def _extract_profile_filters(self, profile: Optional[Dict[str, Any]]) -> Dict[str, set]:
        """프로필에서 알레르기/비선호 단어 집합 추출(소문자 정규화)."""
        allergies = set()
        dislikes = set()
        try:
            if profile and isinstance(profile, dict):
                for a in (profile.get("allergies") or []):
                    if isinstance(a, str) and a.strip():
                        allergies.add(a.strip().lower())
                for d in (profile.get("disliked_foods") or []):
                    if isinstance(d, str) and d.strip():
                        dislikes.add(d.strip().lower())
        except Exception:
            pass
        return {"allergies": allergies, "dislikes": dislikes}

    def _passes_personal_filters(self, item: Dict[str, Any], filters: Dict[str, set]) -> bool:
        """메뉴/식당 텍스트에 알레르기/비선호 키워드가 포함되면 제외.
        현 단계에서는 단순 포함(contains) 기반 필터를 사용한다.
        """
        text_parts = [
            str(item.get("name", "")),
            str(item.get("menu_name", "")),
        ]
        # keto_reasons가 문자열 리스트일 수 있음
        reasons = item.get("keto_reasons") or []
        if isinstance(reasons, list):
            text_parts.extend(str(x) for x in reasons)
        text = " ".join(text_parts).lower()
        for w in filters.get("allergies", set()):
            if w and w in text:
                return False
        for w in filters.get("dislikes", set()):
            if w and w in text:
                return False
        return True
    
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
            
            # ⚠️ 에이전트 레벨 결과 캐시는 비활성화 (회전 추천/개인화가 즉시 반영되어야 함)
            
            # 전체 검색에 타임아웃 적용
            try:
                result = await asyncio.wait_for(
                    self._execute_search_with_timeout(message, lat, lng, radius_km, profile),
                    timeout=90.0  # 90초 타임아웃으로 증가
                )
                
                return result
                
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
        
        # 1. 풀 캐시(응답 풀) 먼저 확인 → 라운드로빈 반환
        try:
            user_id = profile.get("user_id", "") if profile else ""
            stable_key_obj = {
                "q": message.strip(),
                "lat": round(lat, 3),
                "lng": round(lng, 3),
                "radius_km": radius_km,
                "user_id": user_id,
            }
            stable_key = hashlib.sha256(json.dumps(stable_key_obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
            pool_key = f"place_pool:{stable_key}"
            idx_key = f"place_pool_idx:{stable_key}"
            pool_data = redis_cache.get(pool_key) if redis_cache else None
            if pool_data and isinstance(pool_data, dict):
                pool = pool_data.get("pool", [])
                if pool:
                    # 사용 이력 기반 다양성 보장(미사용 우선 → 부족 시 재사용)
                    used_key = f"{idx_key}:used"
                    last_top3_key = f"{idx_key}:last_top3"
                    used_list = redis_cache.get(used_key) or []
                    last_top3_pairs = set()
                    try:
                        last_top3 = redis_cache.get(last_top3_key) or []
                        # 저장 형태: "placeId|menuKey" 리스트
                        last_top3_pairs = set(str(x) for x in last_top3)
                    except Exception:
                        last_top3_pairs = set()
                    try:
                        used_set = set(int(x) for x in used_list if isinstance(x, (int, float, str)))
                    except Exception:
                        used_set = set()
                    all_indices = list(range(len(pool)))
                    available = [i for i in all_indices if i not in used_set]
                    if not available:
                        # 모두 소비되면 이력 초기화 후 다시 전체에서 선택
                        available = all_indices
                        used_set = set()
                        used_list = []
                    # 1) 우선 미사용에서 최대 3개 선정
                    candidates = available.copy()
                    random.shuffle(candidates)
                    selected = candidates[:3]
                    # 2) 3개 미만이면 사용된 것 중에서 채움(중복 제외)
                    if len(selected) < 3:
                        rest = [i for i in all_indices if i not in set(selected)]
                        random.shuffle(rest)
                        selected += rest[: 3 - len(selected)]
                    # 안전장치
                    if not selected:
                        selected = [random.randrange(len(pool))]

                    # 3) 선택된 3개를 사용해 결과 상위 1,2,3을 구성
                    combined_results: List[Dict[str, Any]] = []
                    seen_menu_per_place: Dict[str, set] = {}
                    picked_top3_pairs: List[str] = []
                    for si in selected:
                        entry = pool[si]
                        res_list = entry.get("results", []) or []
                        # 각 후보에서 가능한 첫 아이템을 고르되, 같은 식당이면 메뉴명이 달라야 함
                        picked_one = None
                        for item in res_list:
                            place_id = str(item.get("place_id", ""))
                            menu_name = item.get("menu_name") or "__no_menu__"
                            used_menus = seen_menu_per_place.setdefault(place_id, set())
                            pair_key = f"{place_id}|{menu_name}"
                            # 직전 라운드 TOP3 (place,menu) 회피
                            if (menu_name not in used_menus) and (pair_key not in last_top3_pairs):
                                picked_one = item
                                used_menus.add(menu_name)
                                picked_top3_pairs.append(pair_key)
                                break
                        if picked_one:
                            combined_results.append(picked_one)

                    # 회피 규칙으로 3개를 못 채웠다면, last_top3 회피를 완화하여 보충
                    if len(combined_results) < 3:
                        for si in selected:
                            if len(combined_results) >= 3:
                                break
                            res_list = (pool[si].get("results", []) or [])
                            for item in res_list:
                                place_id = str(item.get("place_id", ""))
                                menu_name = item.get("menu_name") or "__no_menu__"
                                used_menus = seen_menu_per_place.setdefault(place_id, set())
                                if menu_name in used_menus:
                                    continue
                                combined_results.append(item)
                                used_menus.add(menu_name)
                                picked_top3_pairs.append(f"{place_id}|{menu_name}")
                                break

                    # 4) 나머지 슬롯(최대 10)은 선택된 엔트리들의 리스트를 순회하며 중복 메뉴 방지로 채움
                    for si in selected:
                        res_list = (pool[si].get("results", []) or [])
                        for item in res_list:
                            if len(combined_results) >= 10:
                                break
                            place_id = str(item.get("place_id", ""))
                            menu_name = item.get("menu_name") or ""
                            used_menus = seen_menu_per_place.setdefault(place_id, set())
                            if menu_name in used_menus:
                                continue
                            combined_results.append(item)
                            used_menus.add(menu_name)
                        if len(combined_results) >= 10:
                            break

                    # 5) 응답 텍스트 재생성(개인화 요약을 위해 LLM 호출 허용)
                    resp = await self._generate_fast_response(message, combined_results, profile)

                    result = {
                        "results": combined_results,
                        "response": resp,
                        "search_stats": {
                            "hybrid_results": sum(len((pool[si].get("results", []) or [])) for si in selected),
                            "final_results": len(combined_results),
                            "location": {"lat": lat, "lng": lng}
                        },
                        "tool_calls": [{
                            "tool": "place_search_agent(pool-used)",
                            "selected_indices": selected,
                            "location": {"lat": lat, "lng": lng}
                        }]
                    }

                    # 6) 사용 이력 업데이트(선택된 3개 모두 기록, 길이 제한: 풀 크기-1 유지)
                    used_list.extend(int(x) for x in selected)
                    max_used = max(1, len(pool) - 1)
                    if len(used_list) > max_used:
                        used_list = used_list[-max_used:]
                    ttl = pool_data.get("ttl", 1800)
                    redis_cache.set(used_key, used_list, ttl=ttl)
                    # 직전 TOP3 메뉴 갱신
                    try:
                        redis_cache.set(last_top3_key, picked_top3_pairs[:3], ttl=ttl)
                    except Exception:
                        pass
                    print(f"    📦 장소 풀 캐시 히트: {len(pool)}개 중 선택 {selected} (상위 3 슬롯에 배치)")
                    return result
        except Exception as e:
            print(f"    ⚠️ 장소 풀 캐시 조회 오류: {e}")

        # 2. 시맨틱 캐시 선조회(텍스트만 선확보하고, 실제 검색/풀 저장은 계속 진행)
        semantic_text: Optional[str] = None
        if settings.semantic_cache_enabled:
            try:
                user_id = profile.get("user_id", "") if profile else ""
                model_ver = f"place_search_{settings.llm_model}"
                opts_hash = f"{lat:.2f}_{lng:.2f}_{radius_km}_{user_id}"
                tmp_semantic = await semantic_cache_service.semantic_lookup(
                    message, user_id, model_ver, opts_hash
                )
                if tmp_semantic:
                    print(f"    🧠 시맨틱 캐시 히트(텍스트 확보): 식당 검색")
                    semantic_text = tmp_semantic
            except Exception as e:
                print(f"    ⚠️ 시맨틱 캐시 조회 오류: {e}")

        # 3. 하이브리드 검색 실행 (벡터 + 키워드 + RAG)
        print("  🚀 하이브리드 검색 시작...")
        
        try:
            # 하이브리드 검색 실행
            # hybrid_search에 사용자별 회전/개인화 정보를 전달
            location_payload = {"lat": lat, "lng": lng}
            # 사용자 ID 전달 (있다면)
            if profile and isinstance(profile, dict) and profile.get("user_id"):
                location_payload["user_id"] = profile.get("user_id")
            # 프로필 전체 전달 (개인화 가중치용)
            if profile and isinstance(profile, dict):
                location_payload["profile"] = profile

            # 🔧 테스트 1회용 초기화 플래그 (이번 한 번만)
            location_payload["reset_rotation"] = True   # TODO: 확인 후 주석 처리
            location_payload["bypass_pool_cache"] = True # TODO: 확인 후 주석 처리
            location_payload["ignore_rotation"] = True  # 필요시 1회 완전 무시

            # 디버그 로그: 전달 플래그 확인
            try:
                print(
                    "  🧪 테스트 플래그:",
                    {
                        "reset_rotation": location_payload.get("reset_rotation"),
                        "bypass_pool_cache": location_payload.get("bypass_pool_cache"),
                        "ignore_rotation": location_payload.get("ignore_rotation"),
                        "user_id": location_payload.get("user_id", "anon")
                    }
                )
            except Exception:
                pass

            hybrid_results = await self.restaurant_hybrid_search.hybrid_search(
                query=message,
                location=location_payload,
                max_results=20
            )
            # 결과 집계 로그
            try:
                print(f"  📦 에이전트 수신 결과: {len(hybrid_results)}개")
                # 샘플 3개만 요약 출력
                for i, r in enumerate(hybrid_results[:3], 1):
                    print(f"    {i}. {r.get('restaurant_name')} - {r.get('menu_name')}")  # keto 점수 제거
            except Exception:
                pass
            
            print(f"  ✅ 하이브리드 검색 결과: {len(hybrid_results)}개")
            
            # 결과를 표준 형식으로 변환 + 유니크화(place_id+menu)
            formatted_results = []
            seen_pairs = set()
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
            uniq_results = []
            for r in formatted_results:
                key = (r.get("place_id", ""), r.get("menu_name") or "__no_menu__")
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                uniq_results.append(r)
            
            # 응답 생성
            # 개인화 필터 적용(알레르기/비선호 제외)
            filters = self._extract_profile_filters(profile)
            filtered_results = [r for r in uniq_results if self._passes_personal_filters(r, filters)]
            # 필터로 모두 빠지면 원본 일부라도 사용(안내문 방지)
            effective_results = filtered_results or uniq_results

            response = await self._generate_fast_response(message, effective_results, profile)
            
            result_data = {
                "results": effective_results[:10],  # 상위 10개
                "response": response,
                "search_stats": {
                    "hybrid_results": len(formatted_results),
                    "final_results": len(effective_results),
                    "location": {"lat": lat, "lng": lng}
                },
                "tool_calls": [{
                    "tool": "place_search_agent",
                    "hybrid_results": len(formatted_results),
                    "final_results": len(effective_results),
                    "location": {"lat": lat, "lng": lng}
                }]
            }

            # 하이브리드가 비었고, 시맨틱 텍스트가 있으면 시맨틱 응답으로 폴백
            if not effective_results and semantic_text:
                print("    ↩️ 하이브리드 결과 없음 → 시맨틱 텍스트 폴백 반환")
                return {
                    "results": [],
                    "response": semantic_text,
                    "search_stats": {
                        "hybrid_results": len(formatted_results),
                        "final_results": 0,
                        "location": {"lat": lat, "lng": lng}
                    },
                    "tool_calls": [{
                        "tool": "place_search_agent(semantic-fallback)",
                        "location": {"lat": lat, "lng": lng}
                    }],
                    "source": "semantic_cache"
                }
            
            # 4. 풀 캐시 저장(응답 다양성 보존)
            try:
                # 풀 구성: 최대 10개 응답을 후보로 생성
                pool_candidates: List[Dict[str, Any]] = []
                top_k = min(len(effective_results), 24)
                sample_k = min(6, top_k)
                indices = list(range(top_k))
                random.shuffle(indices)
                indices = indices[:sample_k]
                for i in indices:
                    subset = effective_results[i:i+10]
                    # LLM 호출 없이 빠른 템플릿 응답으로 대체(타임아웃 방지)
                    resp = self._format_quick_response(message, subset)
                    pool_candidates.append({
                        "results": subset[:10],
                        "response": resp,
                        "search_stats": {
                            "hybrid_results": len(effective_results),
                            "final_results": len(subset[:10]),
                            "location": {"lat": lat, "lng": lng}
                        },
                        "tool_calls": [{
                            "tool": "place_search_agent(pool)",
                            "hybrid_results": len(effective_results),
                            "final_results": len(subset[:10]),
                            "location": {"lat": lat, "lng": lng}
                        }]
                    })

                if pool_candidates:
                    ttl = 1800  # 30분
                    redis_cache.set(pool_key, {"pool": pool_candidates, "ttl": ttl}, ttl=ttl)
                    redis_cache.set(idx_key, 0, ttl=ttl)
                    print(f"    💾 장소 풀 캐시 저장: {len(pool_candidates)}개")
            except Exception as e:
                print(f"    ⚠️ 장소 풀 캐시 저장 오류: {e}")

            # 5. 시맨틱 캐시 저장 (식당 검색 결과)
            if settings.semantic_cache_enabled:
                try:
                    user_id = profile.get("user_id", "") if profile else ""
                    model_ver = f"place_search_{settings.llm_model}"
                    opts_hash = f"{lat:.2f}_{lng:.2f}_{radius_km}_{user_id}"
                    
                    meta = {
                        "route": "place_search",
                        "location": {"lat": lat, "lng": lng},
                        "radius_km": radius_km,
                        "result_count": len(formatted_results)
                    }
                    
                    await semantic_cache_service.save_semantic_cache(
                        message, user_id, model_ver, opts_hash, 
                        response, meta
                    )
                except Exception as e:
                    print(f"    ⚠️ 시맨틱 캐시 저장 오류: {e}")
            
            return result_data
            
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
                # response += f"⭐ 키토 점수: {restaurant.get('keto_score', 0)}/100\n\n"  # 키토 점수 표시 제거
            
            return response
        
        try:
            # 시간 측정 시작
            import time
            start_time = time.time()
            
            # 구조화된 프롬프트로 LLM 응답 생성
            restaurant_list = ""
            for i, restaurant in enumerate(results[:3], 1):
                restaurant_list += f"{i}. {restaurant.get('name', '이름 없음')}\n"
                # restaurant_list += f"   - 키토 점수: {restaurant.get('keto_score', 0)}/100\n"  # 키토 점수 표시 제거
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
            print(f"✅ '키토 점수' 포함 여부: {'키토 점수' in llm_response.content}")
            print(f"⏱️ 총 생성 시간: {total_time:.2f}초")
            print(f"{'='*60}\n")
            
            return llm_response.content
            
        except asyncio.TimeoutError:
            print(f"⏰ LLM 응답 생성 타임아웃 (20초)")
            # 타임아웃 시 템플릿 기반 응답으로 폴백
            return f"🍽️ 키토 친화적 식당 {len(results)}곳을 찾았습니다!\n\n" + \
                   "\n".join([f"• {r.get('name', '이름 없음')}" 
                             for r in results[:3]])  # 키토점수 제거
            
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
