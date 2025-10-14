"""
식당 하이브리드 검색 도구
Supabase 벡터 검색 + 키워드 검색을 통한 식당 RAG
"""

import re
import random
import openai
import asyncio
import sys
import os
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.core.redis_cache import redis_cache

# Windows 콘솔에서 이모지 출력을 위한 인코딩 설정
if sys.platform == "win32":
    import codecs
    # Windows 콘솔 UTF-8 출력: detach()는 uvicorn 멀티프로세스와 충돌할 수 있으므로 사용하지 않음
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        # 일부 환경에서는 reconfigure 미지원: 환경 변수 또는 기본 출력 사용
        pass
from app.core.config import settings

class RestaurantHybridSearchTool:
    """식당 하이브리드 검색 도구 클래스"""
    
    def __init__(self):
        self.supabase = supabase
        # OpenAI 클라이언트 (임베딩용으로 유지)
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        # 실제 식당 테이블들
        self.restaurant_table = "restaurant"
        self.menu_table = "menu"
        self.menu_embedding_table = "menu_embedding"
        self.keto_scores_table = "keto_scores"
    
    async def _create_embedding(self, text: str) -> List[float]:
        """텍스트를 임베딩으로 변환"""
        try:
            print(f"📊 식당 임베딩 생성 중: {text[:50]}...")
            response = self.openai_client.embeddings.create(
                model=settings.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding
            print(f"✅ 식당 임베딩 생성 완료: {len(embedding)}차원")
            return embedding
        except Exception as e:
            print(f"❌ 식당 임베딩 생성 오류: {e}")
            return []
    
    def _extract_keywords(self, query: str) -> List[str]:
        """쿼리에서 키워드 추출 (식당 특화)"""
        # 한글, 영문, 숫자만 추출
        keywords = re.findall(r'[가-힣a-zA-Z0-9]+', query)
        # 2글자 이상만 필터링
        keywords = [kw for kw in keywords if len(kw) >= 2]
        
        # 식당 관련 키워드 우선순위 부여
        restaurant_keywords = ['구이', '찜', '회', '스테이크', '샐러드', '치킨', '삼겹살']
        prioritized = []
        
        for keyword in keywords:
            if any(rk in keyword for rk in restaurant_keywords):
                prioritized.insert(0, keyword)  # 앞에 추가
            else:
                prioritized.append(keyword)
        
        return prioritized[:5]  # 최대 5개
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """중복 결과 제거 (개선된 버전)"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            # 여러 필드명으로 고유 ID 생성 시도
            restaurant_id = result.get('restaurant_id') or result.get('id')
            menu_id = result.get('menu_id')
            
            # restaurant_id가 있으면 그것을 사용, 없으면 식당명으로 대체
            if restaurant_id:
                result_id = f"{restaurant_id}_{menu_id or 'no_menu'}"
            else:
                # 식당명으로 중복 제거 (폴백)
                restaurant_name = result.get('restaurant_name') or result.get('name', '')
                result_id = f"{restaurant_name}_{menu_id or 'no_menu'}"
            
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        return unique_results
    
    def _select_diverse_results(self, results: List[Dict], max_results: int, gimbap_cap: int = 1) -> List[Dict]:
        """메뉴 다양성을 고려한 결과 선택 (식당 다양성 우선)"""
        if len(results) <= max_results:
            return results
        
        import random
        
        # 1단계: 키토 키워드 보정 점수 시스템
        keto_keywords = ['키토', 'keto', '저탄', '저탄고지', '다이어트']
        
        # 점수 보정된 결과 생성
        corrected_results = []
        for result in results:
            menu_name = (result.get('menu_name') or '').lower()
            restaurant_name = (result.get('restaurant_name') or '').lower()
            original_score = result.get('keto_score')
            
            # 키토 키워드가 있는지 확인
            has_keto_keyword = any(keyword in menu_name or keyword in restaurant_name for keyword in keto_keywords)
            
            # 점수 보정 로직
            if original_score is None and has_keto_keyword:
                # 키토 점수가 None이고 키토 키워드가 있으면 +80점
                corrected_score = 80
                result['keto_score'] = corrected_score
                result['score_correction'] = f"키토 키워드 보정: None → {corrected_score}"
            elif original_score is not None:
                # 기존 점수가 있으면 그대로 사용
                corrected_score = original_score
            else:
                # 키토 키워드도 없고 점수도 None이면 0점
                corrected_score = 0
                result['keto_score'] = corrected_score
            
            corrected_results.append(result)
        
        # 키토 점수 1점 이상인 메뉴만 필터링
        valid_results = [r for r in corrected_results if (r.get('keto_score') or 0) >= 1]
        
        print(f"    📊 점수 보정 후 유효 메뉴: {len(valid_results)}개 (전체 {len(results)}개 중)")
        
        if len(valid_results) <= max_results:
            return valid_results
        
        # 2단계: 카테고리별로 그룹화하여 김밥 편향 완화
        category_groups = {}
        for result in valid_results:
            menu_name = result.get('menu_name') or ''
            category = self._categorize_menu(menu_name)
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(result)

        # 각 카테고리 내부는 점수 순으로 우선 정렬(동점은 랜덤성 부여)
        for items in category_groups.values():
            random.shuffle(items)
            items.sort(key=lambda x: x.get('keto_score') or 0, reverse=True)

        # 카테고리 우선순위 및 상한 설정: 김밥류 상한 적용(기본 1개, 쿨다운 시 0)
        priority_order = ['샐러드류', '고기류', '생선류', '볶음류', '면류', '김밥류', '기타']
        category_cap = {'김밥류': gimbap_cap}
        picked_count = {cat: 0 for cat in category_groups.keys()}

        selected_results = []

        # 3단계: 라운드-로빈으로 카테고리 우선 채우기
        while len(selected_results) < max_results:
            progressed = False
            for cat in priority_order:
                if len(selected_results) >= max_results:
                    break
                items = category_groups.get(cat, [])
                if not items:
                    continue
                # 카테고리 상한 체크(김밥류 1개 제한)
                cap = category_cap.get(cat)
                if cap is not None and picked_count.get(cat, 0) >= cap:
                    continue
                # 하나 선택
                selected_item = items.pop(0)
                selected_results.append(selected_item)
                picked_count[cat] = picked_count.get(cat, 0) + 1
                progressed = True
                if len(selected_results) >= max_results:
                    break
            if not progressed:
                break  # 더 이상 선택할 수 있는 항목이 없음

        # 4단계: 아직 부족하면 남은 항목 중에서 우선순위대로 보충(김밥 상한은 유지)
        if len(selected_results) < max_results:
            remaining_pool = []
            for cat in priority_order:
                items = category_groups.get(cat, [])
                if not items:
                    continue
                # 상한에 도달한 카테고리는 제외
                cap = category_cap.get(cat)
                if cap is not None and picked_count.get(cat, 0) >= cap:
                    continue
                remaining_pool.extend([(cat, item) for item in items])

            # 점수 우선 정렬
            random.shuffle(remaining_pool)
            remaining_pool.sort(key=lambda x: x[1].get('keto_score') or 0, reverse=True)

            for cat, item in remaining_pool:
                if len(selected_results) >= max_results:
                    break
                cap = category_cap.get(cat)
                if cap is not None and picked_count.get(cat, 0) >= cap:
                    continue
                selected_results.append(item)
                picked_count[cat] = picked_count.get(cat, 0) + 1

        return selected_results[:max_results]
    
    def _categorize_menu(self, menu_name: str) -> str:
        """메뉴명을 기반으로 카테고리 분류"""
        menu_name = menu_name.lower()
        
        # 김밥류
        if any(keyword in menu_name for keyword in ['김밥', 'gimbap', '키토김밥']):
            return '김밥류'
        
        # 샐러드류
        elif any(keyword in menu_name for keyword in ['샐러드', 'salad', '채소']):
            return '샐러드류'
        
        # 고기류
        elif any(keyword in menu_name for keyword in ['고기', '스테이크', '갈비', '삼겹살', '닭', '치킨', '돼지', '소고기']):
            return '고기류'
        
        # 생선류
        elif any(keyword in menu_name for keyword in ['생선', '회', '참치', '연어', '고등어', '조개']):
            return '생선류'
        
        # 면류
        elif any(keyword in menu_name for keyword in ['면', '파스타', '스파게티', '라면']):
            return '면류'
        
        # 볶음류
        elif any(keyword in menu_name for keyword in ['볶음', '구이', '찜', '튀김']):
            return '볶음류'
        
        # 기타
        else:
            return '기타'
    
    async def _supabase_vector_search(self, query_embedding: List[float], k: int) -> List[Dict]:
        """menu_embedding 테이블을 사용한 벡터 검색"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                print("  ⚠️ Supabase 클라이언트 없음 - 벡터 검색 건너뜀")
                return []
            
            # 실제 스키마 기반 RPC 함수 호출
            results = self.supabase.rpc('restaurant_menu_vector_search', {
                'query_embedding': query_embedding,
                'match_count': k,
                'similarity_threshold': 0.4  # 의미 있는 유사도만 반환
            }).execute()
            
            if results.data:
                print(f"✅ 식당 메뉴 벡터 검색 성공: {len(results.data)}개 (임계값 0.4 이상)")
                # 키토 점수 필터링 적용 (0점 제외)
                filtered_results = [r for r in results.data if (r.get('keto_score') or 0) > 0]
                print(f"✅ 벡터 검색 필터링 후 (키토 점수 > 0): {len(filtered_results)}개")
                return filtered_results
            else:
                print("⚠️ 식당 메뉴 벡터 검색 결과 없음 - 임계값 0.4 미만")
                return []
                
        except Exception as e:
            print(f"  ❌ Supabase 벡터 검색 실패: {e}")
            return []
    
    async def _supabase_keyword_search(self, query: str, k: int) -> List[Dict]:
        """실제 스키마 기반 키워드 검색"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                print("  ⚠️ Supabase 클라이언트 없음")
                return []
            
            keywords = self._extract_keywords(query)
            print(f"🔍 추출된 키워드: {keywords}")
            if not keywords:
                print("⚠️ 키워드 없음")
                return []
            
            all_results = []
            
            for keyword in keywords[:3]:  # 상위 3개 키워드만 사용
                try:
                    print(f"  🔍 키워드 '{keyword}' 검색 중...")
                    
                    # ILIKE 검색
                    ilike_results = self.supabase.rpc('restaurant_ilike_search', {
                        'query_text': keyword,
                        'match_count': k
                    }).execute()
                    
                    print(f"    ILIKE 결과: {len(ilike_results.data) if ilike_results.data else 0}개")
                    if ilike_results.data:
                        # 키토 점수 필터링 적용 (0점 제외)
                        filtered_results = [r for r in ilike_results.data if (r.get('keto_score') or 0) > 0]
                        print(f"    ILIKE 필터링 후 (키토 점수 > 0): {len(filtered_results)}개")
                        all_results.extend(filtered_results)
                    
                    # Trigram 검색
                    trgm_results = self.supabase.rpc('restaurant_trgm_search', {
                        'query_text': keyword,
                        'match_count': k,
                        'similarity_threshold': 0.3
                    }).execute()
                    
                    print(f"    Trigram 결과: {len(trgm_results.data) if trgm_results.data else 0}개")
                    if trgm_results.data:
                        # 키토 점수 필터링 적용 (0점 제외)
                        filtered_results = [r for r in trgm_results.data if (r.get('keto_score') or 0) > 0]
                        print(f"    Trigram 필터링 후 (키토 점수 > 0): {len(filtered_results)}개")
                        all_results.extend(filtered_results)
                        
                except Exception as e:
                    print(f"키워드 검색 오류 for '{keyword}': {e}")
                    continue
            
            print(f"  📊 총 결과: {len(all_results)}개 (중복 제거 전)")
            deduplicated = self._deduplicate_results(all_results)
            print(f"  📊 중복 제거 후: {len(deduplicated)}개")
            return deduplicated[:k]
            
        except Exception as e:
            print(f"식당 키워드 검색 오류: {e}")
            return []
    
    async def _fallback_direct_search(self, query: str, k: int) -> List[Dict]:
        """폴백 직접 테이블 검색 (실제 스키마 기반)"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []
            
            # 1. restaurant 테이블에서 식당명, 카테고리, 주소로 검색
            restaurant_results = self.supabase.table('restaurant').select('*').or_(
                f'name.ilike.%{query}%,category.ilike.%{query}%,addr_road.ilike.%{query}%,addr_jibun.ilike.%{query}%'
            ).limit(k).execute()
            
            # 2. menu 테이블에서 메뉴명, 설명으로 검색 (restaurant 조인)
            menu_results = self.supabase.table('menu').select(
                '*, restaurant:restaurant_id(*)'
            ).or_(
                f'name.ilike.%{query}%,description.ilike.%{query}%'
            ).limit(k).execute()
            
            formatted_results = []
            
            # 식당 결과 포맷팅
            if restaurant_results.data:
                for result in restaurant_results.data:
                    formatted_results.append({
                        'restaurant_id': str(result.get('id', '')),
                        'restaurant_name': result.get('name', '이름 없음'),
                        'restaurant_category': result.get('category', ''),
                        'addr_road': result.get('addr_road', ''),
                        'addr_jibun': result.get('addr_jibun', ''),
                        'lat': result.get('lat', 0.0),
                        'lng': result.get('lng', 0.0),
                        'phone': result.get('phone', ''),
                        'menu_id': None,
                        'menu_name': '',
                        'menu_description': '',
                        'menu_price': None,
                        'keto_score': 0,
                        'keto_reasons': None,
                        'similarity_score': 0.6,
                        'search_type': 'restaurant_fallback',
                        'source_url': result.get('source_url')
                    })
            
            # 메뉴 결과 포맷팅
            if menu_results.data:
                for result in menu_results.data:
                    restaurant_info = result.get('restaurant', {})
                    formatted_results.append({
                        'restaurant_id': str(result.get('restaurant_id', '')),
                        'restaurant_name': restaurant_info.get('name', '식당 정보 없음'),
                        'restaurant_category': restaurant_info.get('category', ''),
                        'addr_road': restaurant_info.get('addr_road', ''),
                        'addr_jibun': restaurant_info.get('addr_jibun', ''),
                        'lat': restaurant_info.get('lat', 0.0),
                        'lng': restaurant_info.get('lng', 0.0),
                        'phone': restaurant_info.get('phone', ''),
                        'menu_id': str(result.get('id', '')),
                        'menu_name': result.get('name', ''),
                        'menu_description': result.get('description', ''),
                        'menu_price': result.get('price'),
                        'keto_score': 0,
                        'keto_reasons': None,
                        'similarity_score': 0.7,
                        'search_type': 'menu_fallback',
                        'source_url': restaurant_info.get('source_url')
                    })
            
            return formatted_results[:k]
            
        except Exception as e:
            print(f"폴백 직접 검색 오류: {e}")
            return []
    
    async def hybrid_search(self, query: str, location: Optional[Dict[str, float]] = None, max_results: int = 5, user_id: Optional[str] = None) -> List[Dict]:
        """식당 하이브리드 검색 메인 함수 (전체 결과 기반 다양성 확보)"""
        try:
            print(f"🔍 식당 하이브리드 검색 시작: '{query}' (전체 결과 기반 다양성)")
            # 쿼리 정규화 함수: 회전 키 일관성 확보
            def _normalize_query(q: str) -> str:
                import re
                q = (q or "").strip().lower()
                stopwords = ['알려줘','알려 줘','찾아줘','찾아 줘','추천해줘','추천 해줘','추천','근처','주변','근방','식당','가게','맛집','좀','주세요','해줘']
                for sw in stopwords:
                    q = q.replace(sw, ' ')
                q = re.sub(r"\s+", " ", q).strip()
                return q
            normalized_query = _normalize_query(query)
            # 테스트/디버그 플래그 (location을 통해 전달)
            reset_rotation = bool((location or {}).get("reset_rotation"))
            ignore_rotation = bool((location or {}).get("ignore_rotation"))
            bypass_pool_cache = bool((location or {}).get("bypass_pool_cache"))
            
            # 🎲 식당은 데이터가 적으므로 제한 없이 모든 결과 가져오기
            search_limit = 5000  # 충분히 큰 수로 설정 (실제로는 모든 결과)
            print(f"  🎯 전체 결과 검색: 제한 없이 모든 식당 검색 후 {max_results}개 랜덤 선택")
            
            # 1. 결과 풀 캐시 확인 (쿼리 기준) - 회전을 위해 캐시 비활성화
            pool_cache_key = f"restaurant_result_pool:{normalized_query}"
            cached_pool = None  # 회전을 위해 항상 새로 검색
            if cached_pool:
                print(f"  ⚡ 캐시 히트 - 결과 풀 재사용: {len(cached_pool)}개")
                unique_results = cached_pool
            else:
                # 2. 임베딩 생성
                print("  📊 임베딩 생성 중...")
                query_embedding = await self._create_embedding(query)
                
                # 3. 병렬 검색 실행 (모든 결과)
                vector_results = []
                keyword_results = []
                
                if query_embedding:
                    print("  🔄 벡터 검색 실행...")
                    vector_results = await self._supabase_vector_search(query_embedding, search_limit)
                    if not vector_results:
                        print("  ⚠️ 벡터 검색 결과 없음 - 키워드 검색에 의존")
                
                print("  🔄 키워드 검색 실행...")
                keyword_results = await self._supabase_keyword_search(query, search_limit)
                
                # 비김밥 메뉴를 더 많이 가져오기 위한 추가 검색
                print("  🔄 비김밥 메뉴 추가 검색...")
                non_gimbap_queries = [
                    f"{query} 샐러드",
                    f"{query} 연어",
                    f"{query} 참치",
                    f"{query} 치킨",
                    f"{query} 스테이크",
                    f"{query} 파스타",
                    f"{query} 리조또",
                    f"{query} 볶음밥",
                    f"{query} 덮밥",
                    f"{query} 국수"
                ]
                
                additional_results = []
                for search_query in non_gimbap_queries:
                    try:
                        additional_keyword_results = await self._supabase_keyword_search(search_query, 50)
                        if additional_keyword_results:
                            additional_results.extend(additional_keyword_results)
                    except Exception as e:
                        print(f"  ⚠️ 추가 검색 실패 ({search_query}): {e}")
                
                print(f"  📊 추가 검색 결과: {len(additional_results)}개")
                
                # 4. 결과 통합
                all_results = []
                all_results.extend(vector_results)
                all_results.extend(keyword_results)
                all_results.extend(additional_results)
                
                print(f"  📊 벡터 검색 결과: {len(vector_results)}개")
                print(f"  📊 키워드 검색 결과: {len(keyword_results)}개")
                print(f"  📊 통합 결과: {len(all_results)}개 (중복 제거 전)")
            
            # 중복 제거
            unique_results = self._deduplicate_results(all_results)
            print(f"  📊 중복 제거 후: {len(unique_results)}개")
            print(f"  🔍 실제 검색된 메뉴들: {[r.get('menu_name', 'Unknown') for r in unique_results[:10]]}")
            
            # 김밥/비김밥 비율 조정 (회전을 위해)
            if len(unique_results) > 0:
                def _categorize_menu(name: str) -> str:
                    return self._categorize_menu(name or '')
                
                # 김밥과 비김밥 분리
                gimbap_results = []
                non_gimbap_results = []
                
                for result in unique_results:
                    menu_name = str(result.get('menu_name', '')).strip()
                    category = _categorize_menu(menu_name)
                    if category == '김밥류':
                        gimbap_results.append(result)
                    else:
                        non_gimbap_results.append(result)
                
                print(f"  🍙 원본 분류: 김밥 {len(gimbap_results)}개, 비김밥 {len(non_gimbap_results)}개")
                
                # 김밥 50개, 비김밥 100개로 제한
                final_gimbap = gimbap_results[:50]  # 김밥 최대 50개
                final_non_gimbap = non_gimbap_results[:100]  # 비김밥 최대 100개
                
                unique_results = final_gimbap + final_non_gimbap
                print(f"  🎯 최종 비율 조정: 김밥 {len(final_gimbap)}개, 비김밥 {len(final_non_gimbap)}개 (총 {len(unique_results)}개)")
            
            if len(unique_results) == 0:
                print("  ⚠️ base_pool=0 (벡터/키워드 통합 후 후보 없음)")

                # 🧪 디버그: 필터/회전/개인화 완전 우회 모드 (이번 요청 한정)
                debug_no_filter = bool((location or {}).get("debug_no_filter"))
                if debug_no_filter:
                    print("  🧪 디버그 모드: 필터/회전/개인화 우회 → 원시 결과에서 바로 선택")
                    choose_pool = list(unique_results)
                    # 충분하면 다양성 선택, 아니면 그대로 사용
                    if len(choose_pool) > max_results:
                        try:
                            selected_results = self._select_diverse_results(choose_pool, max_results)
                        except Exception:
                            import random
                            selected_results = random.sample(choose_pool, max_results)
                    else:
                        selected_results = choose_pool

                    # 결과 포맷만 맞춰 바로 반환
                    formatted_results = []
                    for result in selected_results[:max_results]:
                        restaurant_id = str(result.get('restaurant_id', ''))
                        source_url = result.get('source_url')
                        if not source_url and restaurant_id:
                            try:
                                restaurant_info = self.supabase.table('restaurant').select('source_url').eq('id', restaurant_id).execute()
                                if restaurant_info.data and len(restaurant_info.data) > 0:
                                    source_url = restaurant_info.data[0].get('source_url')
                            except Exception as e:
                                print(f"  ⚠️ source_url 조회 실패: {e}")
                        formatted_results.append({
                            'restaurant_id': restaurant_id,
                            'restaurant_name': result.get('restaurant_name', '이름 없음'),
                            'category': result.get('restaurant_category', ''),
                            'addr_road': result.get('addr_road', ''),
                            'addr_jibun': result.get('addr_jibun', ''),
                            'lat': result.get('lat', 0.0),
                            'lng': result.get('lng', 0.0),
                            'phone': result.get('phone', ''),
                            'menu_name': result.get('menu_name', ''),
                            'menu_description': result.get('menu_description', ''),
                            'menu_price': result.get('menu_price'),
                            'keto_score': result.get('keto_score', 0),
                            'keto_reasons': result.get('keto_reasons'),
                            'similarity': result.get('vector_score', result.get('ilike_score', result.get('trigram_score', result.get('similarity_score', 0.0)))),
                            'search_type': result.get('search_type', 'hybrid'),
                            'final_score': result.get('final_score', 0.0),
                            'source_url': source_url
                        })
                    print(f"  ✅ 디버그 모드 결과: {len(formatted_results)}개")
                    return formatted_results

                # 🔒 강력 필터: (키토 점수 ≥ 50) 또는 (점수 None 이고 키토 키워드 포함)
                def is_keto_keyword(r: Dict) -> bool:
                    name = (r.get('menu_name') or r.get('restaurant_name') or '').lower()
                    for kw in ['키토', 'keto', '저탄', '저탄고지']:
                        if kw in name:
                            return True
                    return False

                filtered_pool = []
                for r in unique_results:
                    score = r.get('keto_score')
                    if isinstance(score, (int, float)) and score >= 50:
                        filtered_pool.append(r)
                    elif score is None and is_keto_keyword(r):
                        # None + 키토 키워드 → +50 보정으로 포함
                        r['keto_score'] = 50
                        r['score_correction'] = 'None→+50(키토키워드)'
                        filtered_pool.append(r)
                    # score == 0인 경우는 명시적으로 제외 (키토 키워드가 있어도 0점은 제외)

                print(f"  ✅ 강력 필터 후: {len(filtered_pool)}개 (≥50 또는 None+키토키워드)")
                # 후보가 0이면 자동 완화(이번 요청 한정)
                if len(filtered_pool) == 0:
                    print("  🪄 자동 완화: 임계 50→45로 한시 하향 적용")
                    soft_pool = []
                    for r in unique_results:
                        sc = r.get('keto_score')
                        if (isinstance(sc, (int, float)) and sc >= 45) or (sc is None and is_keto_keyword(r)):
                            # None+키워드는 포함, 그 외 45점 이상 허용
                            if sc is None:
                                r['keto_score'] = 50
                                r['score_correction'] = 'None→+50(키토키워드-soft)'
                            soft_pool.append(r)
                    if len(soft_pool) == 0:
                        print("  ⚠️ 완화 후에도 0 → 키토 점수 45점 이상만 허용")
                        # 키토 점수 45점 이상만 허용 (0점은 절대 제외)
                        final_pool = []
                        for r in unique_results:
                            sc = r.get('keto_score')
                            if isinstance(sc, (int, float)) and sc >= 45:
                                final_pool.append(r)
                        unique_results = final_pool
                    else:
                        unique_results = soft_pool
                else:
                    unique_results = filtered_pool
                # 결과 풀 캐시 저장 (5분)
                if unique_results:
                    redis_cache.set(pool_cache_key, unique_results, ttl=300)
                    print(f"  💾 캐시 저장 - 결과 풀 {len(unique_results)}개 (TTL 300s)")
            
            # 4. 결과가 없으면 폴백 검색
            if not unique_results:
                print("  ⚠️ 하이브리드 검색 결과 없음, 폴백 검색 실행...")
                fallback_results = await self._fallback_direct_search(query, search_limit)
                # 폴백 검색 결과도 키토 점수 필터링 적용
                if fallback_results:
                    print(f"  🔍 폴백 검색 결과: {len(fallback_results)}개")
                    # 폴백 결과에서 키토 점수 45점 이상만 필터링
                    filtered_fallback = []
                    for r in fallback_results:
                        sc = r.get('keto_score')
                        if isinstance(sc, (int, float)) and sc >= 45:
                            filtered_fallback.append(r)
                    unique_results = filtered_fallback
                    print(f"  ✅ 폴백 필터링 후: {len(unique_results)}개 (45점 이상만)")
                else:
                    unique_results = []
            
            # 5. ♻️ 회전 추천: 최근 선택 식당 제외 → 부족하면 리셋
            # 사용자 ID 우선순위: 직접 전달된 user_id > location의 user_id > None
            if not user_id:
                try:
                    user_id = (location or {}).get("user_id")
                except Exception:
                    user_id = None
            rotation_user = str(user_id) if user_id else "anon"
            rotation_key = f"restaurant_rotation:{rotation_user}:{normalized_query}"
            recent_last_batch_key = rotation_key + ":last"
            menu_rotation_key = f"menu_rotation:{rotation_user}:{normalized_query}"
            last_menu_batch_key = f"{menu_rotation_key}:last"

            # 요청으로 회전 캐시 초기화 (비활성화)
            if reset_rotation:
                print("  🧹 테스트: 회전 캐시 초기화 요청 수신 (무시됨)")
                reset_rotation = False  # 회전 초기화 플래그 비활성화
                # try:
                #     redis_cache.delete(rotation_key)
                #     redis_cache.delete(recent_last_batch_key)
                #     redis_cache.delete(menu_rotation_key)
                # except Exception as e:
                #     print(f"  ⚠️ 회전 캐시 초기화 실패: {e}")


                
            recent_restaurant_ids = redis_cache.get(rotation_key) or []
            recent_last_batch = redis_cache.get(recent_last_batch_key) or []
            recent_set = set(str(rid) for rid in recent_restaurant_ids)

            # 최근에 추천한 식당 제외
            def _rid(result: Dict) -> str:
                return str(result.get('restaurant_id') or result.get('id') or "")

            def _normalize_menu_key(result: Dict) -> str:
                """메뉴 이름을 정규화하여 회전 키로 사용.
                - 소문자화
                - '추천' 및 변형 패턴 제거(사장추천/추천메뉴/오늘의추천, (추천), [추천], 단독 '추천')
                - 괄호 내용 제거
                - 한글/영문/숫자 외 제거(공백/특수문자 제거)
                """
                try:
                    import re
                    name = (result.get('menu_name') or '').lower()
                    # '추천' 관련 패턴 제거 (회전 키 통합)
                    name = re.sub(r"[\(\[]\s*추천\s*[\)\]]", " ", name)   # (추천), [추천]
                    name = re.sub(r"추천\s*메뉴", " ", name)
                    name = re.sub(r"사장\s*추천", " ", name)
                    name = re.sub(r"오늘의\s*추천", " ", name)
                    name = re.sub(r"\b추천\b", " ", name)                  # 단독 '추천'
                    # 괄호 안 텍스트 제거
                    name = re.sub(r"\(.*?\)", "", name)
                    # 한글/영문/숫자만 남기고 제거
                    name = re.sub(r"[^가-힣a-z0-9]+", "", name)
                    return name
                except Exception:
                    return (result.get('menu_name') or '').strip().lower()

            def _mid(result: Dict) -> str:
                # 우선 메뉴명 정규화 키를 사용하고, 식당ID와 결합해 충돌 방지
                norm = _normalize_menu_key(result)
                rid = _rid(result)
                if norm:
                    return f"{rid}:{norm}"
                # 메뉴명이 없으면 menu_id를 사용
                return f"{rid}:{str(result.get('menu_id') or '')}"

            base_pool = list(unique_results)
            # 식당 회전 제외는 비활성화(메뉴 회전만 적용)
            if ignore_rotation:
                print("  🚫 테스트: 회전 제외 무시 플래그 적용 (무시됨)")
                ignore_rotation = False  # 회전 무시 플래그 비활성화
            available_results = list(unique_results)
            print(f"  🔁 회전 추천(식당 제외 비활성): 최근 리스트 {len(recent_set)}개 → 사용 가능 {len(available_results)}개")

            # 메뉴 레벨 회전(used_menu)도 제외
            used_menus = set(str(x) for x in (redis_cache.get(menu_rotation_key) or []))
            if used_menus:
                before = len(available_results)
                remaining_after_menu = [r for r in available_results if _mid(r) not in used_menus]
                print(f"  🍽️ 메뉴 회전 제외: {before-len(remaining_after_menu)}개 제외")

                # ✅ 자동 회전 초기화 대신: 사용 이력 제외 유지한 채 베이스 풀에서 보충 시도
                if len(remaining_after_menu) < max_results:
                    print("  🔄 회전 유지 보충: 남은 후보 부족 → 사용 이력 제외하고 베이스 풀에서 채움")
                    try:
                        picked_mids_tmp = set(_mid(r) for r in remaining_after_menu)
                        candidates = []
                        for cand in base_pool:
                            mid_c = _mid(cand)
                            if mid_c in used_menus or mid_c in picked_mids_tmp:
                                continue
                            candidates.append(cand)
                        # 점수 우선 정렬 후 보충
                        candidates.sort(key=lambda x: x.get('keto_score') or 0, reverse=True)
                        need = max_results - len(remaining_after_menu)
                        fill = candidates[:need]
                        available_results = remaining_after_menu + fill
                    except Exception as e:
                        print(f"  ⚠️ 회전 유지 보충 실패: {e}")
                        available_results = remaining_after_menu
                else:
                    available_results = remaining_after_menu

            # 🧱 직전 배치 메뉴 1회 우선 제외(부족하면 해제)
            try:
                last_menu_batch = set(str(x) for x in (redis_cache.get(last_menu_batch_key) or []))
                if last_menu_batch:
                    before = len(available_results)
                    tmp = [r for r in available_results if _mid(r) not in last_menu_batch]
                    print(f"  ⛔ 직전 배치 메뉴 우선 제외: {before-len(tmp)}개 제외")
                    if len(tmp) >= max_results:
                        available_results = tmp
                    else:
                        print("  ↩️ 직전 배치 제외 해제(후보 부족)")
            except Exception as e:
                print(f"  ⚠️ 직전 배치 제외 처리 실패: {e}")

            # 🔁 회전/직전배치 제외 후 후보가 0이면, 이번 요청은 회전 무시하고 전체 풀로 복원
            if len(available_results) == 0 and len(base_pool) > 0:
                print("  🔁 후보 0 → 회전 무시하고 전체 풀로 복원")
                available_results = list(base_pool)

            # 식당 회전 제외를 쓰지 않으므로 직전 배치 보충 단계는 건너뜀

            # 6. 🎲 개인화 가중치 적용 후 메뉴 다양성 선택
            profile = (location or {}).get("profile") if isinstance(location, dict) else None
            if profile:
                # 간단 개인화: 알레르기/비선호 제외, 탄수화물/칼로리 목표 반영 가점
                allergies = set((profile.get("allergies") or []))
                dislikes = set((profile.get("disliked_foods") or []))
                carb_goal = profile.get("carb_goal") or profile.get("carbTarget")
                kcal_goal = profile.get("calorie_goal") or profile.get("kcalTarget")

                def is_blocked(r: Dict) -> bool:
                    name = (r.get('menu_name') or r.get('restaurant_name') or '').lower()
                    # 알레르기/비선호 키워드가 이름에 포함되면 제외
                    tokens = list(allergies) + list(dislikes)
                    return any((isinstance(t, str) and t and t.lower() in name) for t in tokens)

                before_cnt = len(available_results)
                filtered = [r for r in available_results if not is_blocked(r)]
                print(f"  👤 개인화 필터: {before_cnt}→{len(filtered)}개")

                # 후보가 부족하면(또는 0) 이번 요청 한정으로 개인화 제외를 완화/해제
                if len(filtered) < max_results:
                    print("  🩹 개인화 완화: 후보 부족으로 이번 요청은 제외 해제")
                    filtered = list(available_results)

                # 간단 가점: 키토 점수 + (키워드 보정) + 목표 존재시 +5
                for r in filtered:
                    base = (r.get('keto_score') or 0)
                    bonus = 0
                    if carb_goal is not None:
                        bonus += 5
                    if kcal_goal is not None:
                        bonus += 5
                    r['final_score'] = float(base) + bonus
                available_results = filtered

            # 회전 추천: 사용 가능한 메뉴 풀 관리
            rotation_user = str(user_id) if user_id else "anon"
            menu_rotation_key = f"menu_rotation:{rotation_user}:{normalized_query}"
            used_menus = set(str(x) for x in (redis_cache.get(menu_rotation_key) or []))
            
            # 전체 메뉴 풀 생성
            all_menu_names = set(str(r.get('menu_name', '')).strip() for r in available_results if r.get('menu_name'))
            
            # 처음 요청이면 전체 메뉴를 회전 풀에 저장
            if len(used_menus) == 0:
                print(f"  🆕 첫 요청: 전체 메뉴 {len(all_menu_names)}개를 회전 풀에 저장")
                redis_cache.set(menu_rotation_key, list(all_menu_names), ttl=1800)
                used_menus = set()
            
            # 사용 가능한 메뉴 풀 생성 (전체 메뉴 - 사용한 메뉴)
            unused_menus = all_menu_names - used_menus
            
            print(f"  🔁 회전 상태: 사용한 메뉴 {len(used_menus)}개, 사용 가능한 메뉴 {len(unused_menus)}개")
            print(f"  🔍 회전 키: {menu_rotation_key}")
            print(f"  👤 사용자 ID: {user_id} → 회전 사용자: {rotation_user}")
            
            # 사용 가능한 메뉴가 부족하면 회전 리셋
            if len(unused_menus) < max_results:
                print(f"  🔄 회전 리셋: 사용 가능한 메뉴 {len(unused_menus)}개 → 전체 메뉴로 리셋")
                try:
                    # 전체 메뉴로 리셋
                    redis_cache.delete(menu_rotation_key)
                    used_menus = set()
                    unused_menus = all_menu_names
                    print(f"  ✅ 회전 리셋 완료: 전체 메뉴 {len(unused_menus)}개 사용 가능")
                except Exception as e:
                    print(f"  ⚠️ 회전 리셋 실패: {e}")
            
            # 사용 가능한 메뉴에서만 선택
            deduplicated_results = []
            for result in available_results:
                menu_name = str(result.get('menu_name', '')).strip()
                
                # 사용 가능한 메뉴만 선택
                if menu_name and menu_name in unused_menus:
                    deduplicated_results.append(result)
                    print(f"  ✅ 회전 추천: {result.get('restaurant_name')} - {menu_name}")
                else:
                    print(f"  ⚠️ 회전 제외: {result.get('restaurant_name')} - {menu_name} (사용 불가: {menu_name not in unused_menus})")
            
            print(f"  📊 회전 후보 수: {len(deduplicated_results)}개 (전체: {len(available_results)}개)")
            
            # 회전 리셋으로 선택된 메뉴가 있으면 해당 메뉴들로 결과 구성
            if len(unused_menus) < max_results and len(used_menus) > 0:
                print(f"  🔄 회전 리셋으로 선택된 메뉴 {len(used_menus)}개로 결과 구성")
                deduplicated_results = []
                for result in available_results:
                    menu_name = str(result.get('menu_name', '')).strip()
                    if menu_name and menu_name in used_menus:
                        deduplicated_results.append(result)
                        print(f"  ✅ 회전 리셋 선택: {result.get('restaurant_name')} - {menu_name}")
            
            # 다양성 선택 (김밥 제한 포함)
            if len(deduplicated_results) > max_results:
                # 메뉴 다양성을 위한 선택 로직
                # 김밥 메뉴는 하루 최대 1개만 포함 가능
                import random
                def _cat(name: str) -> str:
                    return self._categorize_menu(name or '')
                
                # 김밥 메뉴와 비김밥 메뉴 분리
                gimbap_results = []
                non_gimbap_results = []
                
                for result in deduplicated_results:
                    menu_name = str(result.get('menu_name', '')).strip()
                    category = _cat(menu_name)
                    if category == '김밥류':
                        gimbap_results.append(result)
                    else:
                        non_gimbap_results.append(result)
                
                print(f"  🍙 김밥 메뉴: {len(gimbap_results)}개")
                print(f"  🍽️ 비김밥 메뉴: {len(non_gimbap_results)}개")
                
                # 선택 로직: 김밥 최대 1개 + 나머지 2개
                selected_results = []
                
                # 1. 김밥 메뉴 최대 1개 선택
                if gimbap_results:
                    selected_gimbap = random.sample(gimbap_results, min(1, len(gimbap_results)))
                    selected_results.extend(selected_gimbap)
                    print(f"  🍙 김밥 선택: {len(selected_gimbap)}개")
                
                # 2. 나머지 2개는 비김밥에서 선택
                remaining_needed = max_results - len(selected_results)
                if non_gimbap_results and remaining_needed > 0:
                    selected_non_gimbap = random.sample(non_gimbap_results, min(remaining_needed, len(non_gimbap_results)))
                    selected_results.extend(selected_non_gimbap)
                    print(f"  🍽️ 비김밥 선택: {len(selected_non_gimbap)}개")
                
                # 3. 여전히 부족하면 김밥에서 추가 선택 (최대 1개 제한 유지)
                if len(selected_results) < max_results and gimbap_results:
                    additional_needed = max_results - len(selected_results)
                    if additional_needed > 0:
                        # 이미 김밥이 1개 선택되었으면 추가 선택 안함
                        if len([r for r in selected_results if _cat(r.get('menu_name')) == '김밥류']) == 0:
                            additional_gimbap = random.sample(gimbap_results, min(additional_needed, len(gimbap_results)))
                            selected_results.extend(additional_gimbap)
                            print(f"  🍙 김밥 추가 선택: {len(additional_gimbap)}개")
                
                deduplicated_results = selected_results
                print(f"  🎯 최종 선택: {len(deduplicated_results)}개 (김밥: {len([r for r in selected_results if _cat(r.get('menu_name')) == '김밥류'])}개)")
                
            else:
                # 후보가 충분하지 않으면 그대로 사용
                print(f"  🎯 최종 선택: {len(deduplicated_results)}개 (후보 부족으로 그대로 사용)")

            # 만약 회전/다양성 적용 후 결과가 부족하면, 회전 무시하고 베이스 풀에서 보충
            if len(deduplicated_results) < max_results and len(base_pool) > 0:
                print("  ➕ 최종 보충: 회전 무시하고 베이스 풀에서 식당/메뉴 중복 없이 채움")
                picked_mids = set(_mid(r) for r in deduplicated_results)
                picked_rids = set(_rid(r) for r in deduplicated_results)
                for cand in base_pool:
                    if len(deduplicated_results) >= max_results:
                        break
                    if _mid(cand) in picked_mids:
                        continue
                    if _rid(cand) in picked_rids:
                        continue
                    # 보충 시에도 김밥 상한(1개) 유지
                    try:
                        def _cat2(name: str) -> str:
                            return self._categorize_menu(name or '')
                        gimbap_count = sum(1 for r in deduplicated_results if _cat2(r.get('menu_name')) == '김밥류')
                        if _cat2(cand.get('menu_name')) == '김밥류' and gimbap_count >= 1:
                            continue
                    except Exception:
                        pass
                    deduplicated_results.append(cand)
                    picked_mids.add(_mid(cand))
                    picked_rids.add(_rid(cand))
            
            # 6. 결과 포맷팅 및 source_url 보완
            def _clean_menu_name(name: str) -> str:
                # 메뉴명에서 '추천' 키워드를 제거하고 공백 정리
                try:
                    import re
                    if not name:
                        return name
                    cleaned = str(name)
                    # 괄호로 표시된 추천 제거 예: (추천), [추천]
                    cleaned = re.sub(r"[\(\[]\s*추천\s*[\)\]]", " ", cleaned)
                    # 연결어 형태 제거 예: 사장추천, 오늘의추천, 추천메뉴 등
                    cleaned = re.sub(r"추천\s*메뉴", " ", cleaned)
                    cleaned = re.sub(r"사장\s*추천", " ", cleaned)
                    cleaned = re.sub(r"오늘의\s*추천", " ", cleaned)
                    # 단독 '추천' 단어 제거
                    cleaned = re.sub(r"\b추천\b", " ", cleaned)
                    # 여분 공백 정리
                    cleaned = re.sub(r"\s+", " ", cleaned).strip()
                    return cleaned
                except Exception:
                    return name
            formatted_results = []
            for result in deduplicated_results[:max_results]:
                restaurant_id = str(result.get('restaurant_id', ''))
                
                # source_url이 없으면 직접 조회
                source_url = result.get('source_url')
                if not source_url and restaurant_id:
                    try:
                        restaurant_info = self.supabase.table('restaurant').select('source_url').eq('id', restaurant_id).execute()
                        if restaurant_info.data and len(restaurant_info.data) > 0:
                            source_url = restaurant_info.data[0].get('source_url')
                            print(f"  📎 {result.get('restaurant_name')} source_url 보완: {source_url}")
                    except Exception as e:
                        print(f"  ⚠️ source_url 조회 실패: {e}")
                
                formatted_results.append({
                    'restaurant_id': restaurant_id,
                    'restaurant_name': result.get('restaurant_name', '이름 없음'),
                    'category': result.get('restaurant_category', ''),
                    'addr_road': result.get('addr_road', ''),
                    'addr_jibun': result.get('addr_jibun', ''),
                    'lat': result.get('lat', 0.0),
                    'lng': result.get('lng', 0.0),
                    'phone': result.get('phone', ''),
                    'menu_name': _clean_menu_name(result.get('menu_name', '')),
                    'menu_description': result.get('menu_description', ''),
                    'menu_price': result.get('menu_price'),
                    'keto_score': result.get('keto_score', 0),
                    'keto_reasons': result.get('keto_reasons'),
                    'similarity': result.get('vector_score', result.get('ilike_score', result.get('trigram_score', result.get('similarity_score', 0.0)))),
                    'search_type': result.get('search_type', 'hybrid'),
                    'final_score': result.get('final_score', 0.0),
                    'source_url': source_url
                })
            
            if len(deduplicated_results) == 0:
                try:
                    print("  📉 요약: base_pool=", len(base_pool))
                except Exception:
                    pass
            print(f"  ✅ 최종 결과: {len(formatted_results)}개")

            # 7. 🧠 회전 추천 상태 업데이트 (최근 추천 식당 기록)
            try:
                new_ids = [res.get('restaurant_id') for res in formatted_results if res.get('restaurant_id')]
                # 기존 목록과 합치되 중복 제거, 길이 제한(최근 100개)
                merged = [*recent_restaurant_ids]
                seen = set(str(x) for x in merged)
                for rid in new_ids:
                    if str(rid) not in seen:
                        merged.append(str(rid))
                        seen.add(str(rid))
                merged = merged[-100:]
                # 30분 TTL
                redis_cache.set(rotation_key, merged, ttl=1800)
                # 직전 배치도 별도 저장하여 보충 로직에 활용
                redis_cache.set(recent_last_batch_key, new_ids, ttl=1800)
                print(f"  🧠 회전 추천 업데이트: 총 {len(merged)}개 저장")

                # 메뉴 레벨 회전 업데이트 (사용한 메뉴 추가)
                try:
                    # 실제 추천된 메뉴명 수집
                    new_menu_names = [str(r.get('menu_name', '')).strip() for r in formatted_results if r.get('menu_name')]
                    if new_menu_names:
                        # 사용한 메뉴에 추가
                        updated_used_menus = used_menus | set(new_menu_names)
                        
                        # Redis에 저장
                        try:
                            redis_cache.set(menu_rotation_key, list(updated_used_menus), ttl=1800)
                            print(f"  🍽️ 메뉴 회전 업데이트: 사용한 메뉴 {len(updated_used_menus)}개 저장")
                        except Exception as e:
                            print(f"  ⚠️ 메뉴 회전 키 저장 실패: {e}")
                    else:
                        print(f"  ⚠️ 메뉴 회전 업데이트: 추천된 메뉴 없음")
                except Exception as e:
                    print(f"  ⚠️ 메뉴 회전 업데이트 오류: {e}")
            except Exception as e:
                print(f"  ⚠️ 회전 추천 상태 저장 실패: {e}")
            
            # 결과 요약 출력
            for i, result in enumerate(formatted_results[:3], 1):
                print(f"    {i}. {result['restaurant_name']} - {result['menu_name']} (점수: {result['similarity']:.3f}, 키토: {result['keto_score']})")
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 식당 하이브리드 검색 오류: {e}")
            return []
    
    async def search_by_location(
        self, 
        query: str, 
        lat: float, 
        lng: float, 
        radius_km: float = 5.0, 
        max_results: int = 5
    ) -> List[Dict]:
        """위치 기반 식당 검색"""
        try:
            # 위치 정보를 쿼리에 포함
            location_query = f"{query} 위치: {lat}, {lng} 반경: {radius_km}km"
            
            # 기본 하이브리드 검색 실행
            results = await self.hybrid_search(location_query, {"lat": lat, "lng": lng}, max_results)
            
            # TODO: 실제 거리 계산 및 필터링 추가
            # 현재는 기본 검색 결과 반환
            return results
            
        except Exception as e:
            print(f"위치 기반 식당 검색 오류: {e}")
            return []
    
    async def search_by_category(self, category: str, max_results: int = 5) -> List[Dict]:
        """카테고리별 식당 검색"""
        try:
            # 카테고리 특화 쿼리 생성
            category_keywords = {
                "meat": "고기 구이 삼겹살 갈비 스테이크",
                "seafood": "회 생선 조개 해산물",
                "salad": "샐러드 채소 건강식",
                "chicken": "치킨 닭 튀김",
                "western": "양식 스테이크 파스타"
            }
            
            query = category_keywords.get(category, category)
            results = await self.hybrid_search(query, None, max_results)
            
            # 카테고리 정보 추가
            for result in results:
                result['search_category'] = category
            
            return results
            
        except Exception as e:
            print(f"카테고리별 식당 검색 오류: {e}")
            return []

# 전역 식당 하이브리드 검색 도구 인스턴스
restaurant_hybrid_search_tool = RestaurantHybridSearchTool()
