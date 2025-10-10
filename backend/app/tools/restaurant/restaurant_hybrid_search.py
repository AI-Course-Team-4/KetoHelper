"""
식당 하이브리드 검색 도구
Supabase 벡터 검색 + 키워드 검색을 통한 식당 RAG
"""

import re
import openai
import asyncio
from typing import List, Dict, Any, Optional
from app.core.database import supabase
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
        """중복 결과 제거"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            # restaurant_id와 menu_id를 조합해서 고유 ID 생성
            result_id = f"{result.get('restaurant_id', '')}_{result.get('menu_id', '')}"
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        return unique_results
    
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
                return results.data
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
            print(f"  🔍 추출된 키워드: {keywords}")
            if not keywords:
                print("  ⚠️ 키워드 없음")
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
                        all_results.extend(ilike_results.data)
                    
                    # Trigram 검색
                    trgm_results = self.supabase.rpc('restaurant_trgm_search', {
                        'query_text': keyword,
                        'match_count': k,
                        'similarity_threshold': 0.3
                    }).execute()
                    
                    print(f"    Trigram 결과: {len(trgm_results.data) if trgm_results.data else 0}개")
                    if trgm_results.data:
                        all_results.extend(trgm_results.data)
                        
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
    
    async def hybrid_search(self, query: str, location: Optional[Dict[str, float]] = None, max_results: int = 5) -> List[Dict]:
        """식당 하이브리드 검색 메인 함수"""
        try:
            print(f"🔍 식당 하이브리드 검색 시작: '{query}'")
            
            # 1. 임베딩 생성
            print("  📊 임베딩 생성 중...")
            query_embedding = await self._create_embedding(query)
            
            # 2. 병렬 검색 실행
            vector_results = []
            keyword_results = []
            
            if query_embedding:
                print("  🔄 벡터 검색 실행...")
                vector_results = await self._supabase_vector_search(query_embedding, max_results)
                if not vector_results:
                    print("  ⚠️ 벡터 검색 결과 없음 - 키워드 검색에 의존")
            
            print("  🔄 키워드 검색 실행...")
            keyword_results = await self._supabase_keyword_search(query, max_results)
            
            # 3. 결과 통합
            all_results = []
            all_results.extend(vector_results)
            all_results.extend(keyword_results)
            
            # 중복 제거
            unique_results = self._deduplicate_results(all_results)
            
            # 4. 결과가 없으면 폴백 검색
            if not unique_results:
                print("  ⚠️ 하이브리드 검색 결과 없음, 폴백 검색 실행...")
                unique_results = await self._fallback_direct_search(query, max_results)
            
            # 5. 결과 포맷팅 및 source_url 보완
            formatted_results = []
            for result in unique_results[:max_results]:
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
            
            print(f"  ✅ 최종 결과: {len(formatted_results)}개")
            
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
