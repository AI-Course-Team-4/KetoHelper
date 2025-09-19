"""
한글 최적화 검색 도구
PostgreSQL Full-Text Search + pg_trgm + 벡터 검색 통합
"""

import re
import openai
import asyncio
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.core.config import settings

class KoreanSearchTool:
    """한글 최적화 검색 도구 클래스"""
    
    def __init__(self):
        self.supabase = supabase
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
    
    async def _create_embedding(self, text: str) -> List[float]:
        """텍스트를 임베딩으로 변환"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"임베딩 생성 오류: {e}")
            return []
    
    def _extract_korean_keywords(self, query: str) -> List[str]:
        """한글 키워드 추출 및 정규화"""
        # 한글, 영문, 숫자만 추출
        keywords = re.findall(r'[가-힣a-zA-Z0-9]+', query)
        
        # 2글자 이상만 필터링
        keywords = [kw for kw in keywords if len(kw) >= 2]
        
        # 한글 키워드 정규화 (조사 제거 등)
        normalized_keywords = []
        for keyword in keywords:
            # 한글인 경우 조사 제거
            if re.match(r'[가-힣]+', keyword):
                # 간단한 조사 제거 (더 정교한 형태소 분석 필요시 KoNLPy 사용)
                normalized = re.sub(r'(을|를|이|가|은|는|에|에서|로|으로|와|과|의|도|만|까지|부터|부터|한테|에게)$', '', keyword)
                if len(normalized) >= 2:
                    normalized_keywords.append(normalized)
            else:
                normalized_keywords.append(keyword)
        
        return normalized_keywords
    
    def _generate_query_variants(self, query: str) -> List[str]:
        """사용자 검색어를 다양한 형태로 정규화해 변형 쿼리 리스트를 생성.
        - 불용어 제거: 레시피/만드는법/만드는 법/요리 등
        - 공백 제거/토큰 분리/OR 토큰
        """
        q = (query or '').strip()
        if not q:
            return []

        stopwords = ['레시피', '만드는법', '만드는 법', '요리', '방법']
        base = q
        for sw in stopwords:
            base = base.replace(sw, '').strip()

        # 토큰화(공백 기준)
        tokens = [t for t in base.split() if t]

        variants = []
        variants.append(q)            # 원문
        if base and base != q:
            variants.append(base)     # 불용어 제거
        if tokens:
            joined = ' '.join(tokens)
            if joined not in variants:
                variants.append(joined)
            nospace = ''.join(tokens)
            if nospace and nospace not in variants:
                variants.append(nospace)
            # OR 토큰(당근|라페|김밥)
            if len(tokens) > 1:
                or_tokens = '|'.join(tokens)
                variants.append(or_tokens)

        # 중복 제거 유지 순서
        seen = set()
        uniq = []
        for v in variants:
            if v and v not in seen:
                uniq.append(v)
                seen.add(v)
        return uniq[:5]

    async def _exact_ilike_search(self, query: str, k: int) -> List[Dict]:
        """정확 매칭에 가까운 ILIKE 기반 검색(RPC 사용).
        변형 쿼리(불용어 제거/공백 제거/OR 토큰)를 순차 시도하여
        최초로 결과가 나오면 그 결과를 반환한다.
        """
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []

            for vq in self._generate_query_variants(query):
                try:
                    res = self.supabase.rpc('ilike_search', {'query_text': vq, 'match_count': k}).execute()
                    rows = res.data or []
                    if rows:
                        formatted = []
                        for row in rows:
                            formatted.append({
                                'id': str(row.get('id', '')),
                                'title': row.get('title', '제목 없음'),
                                'content': row.get('content', ''),
                                'search_score': row.get('search_score', 1.0),
                                'search_type': 'ilike_exact',
                                'metadata': {kk: vv for kk, vv in row.items() if kk not in ['id','title','content','search_score']}
                            })
                        return formatted
                except Exception as e:
                    print(f"ILIKE 정확 매칭 RPC 오류({vq}): {e}")
                    continue
            return []
        except Exception as e:
            print(f"ILIKE 정확 매칭 오류: {e}")
            return []
    async def _groonga_search(self, query: str, k: int) -> List[Dict]:
        """PGroonga 검색 (제목/본문 우선 정확 매칭)"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []
            results = self.supabase.rpc('groonga_search', {
                'query_text': query,
                'match_count': k
            }).execute()

            formatted_results = []
            for result in results.data or []:
                formatted_results.append({
                    'id': str(result.get('id', '')),
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'search_score': result.get('search_score', 1.0),
                    'search_type': 'pgroonga',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'search_score']}
                })

            return formatted_results
        except Exception as e:
            print(f"PGroonga 검색 오류: {e}")
            return []

    async def _full_text_search(self, query: str, k: int) -> List[Dict]:
        """PostgreSQL Full-Text Search (한글 최적화)"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []
            
            # Full-Text Search 실행 (RPC 함수 사용)
            results = self.supabase.rpc('fts_search', {
                'query_text': query,
                'match_count': k
            }).execute()
            
            formatted_results = []
            for result in results.data or []:
                formatted_results.append({
                    'id': str(result.get('id', '')),
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'search_score': result.get('search_score', result.get('fts_score', 0.0)),
                    'search_type': 'fts',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'fts_score']}
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Full-Text Search 오류: {e}")
            return []
    
    async def _trigram_similarity_search(self, query: str, k: int) -> List[Dict]:
        """Trigram 유사도 검색 (한글 유사도)"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []
            
            # Trigram 유사도 검색 (RPC 함수 사용)
            results = self.supabase.rpc('trgm_search', {
                'query_text': query,
                'match_count': k
            }).execute()
            
            formatted_results = []
            for result in results.data or []:
                formatted_results.append({
                    'id': str(result.get('id', '')),
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'search_score': result.get('search_score', result.get('similarity_score', 0.0)),
                    'search_type': 'trigram',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'similarity_score']}
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Trigram 유사도 검색 오류: {e}")
            return []
    
    async def _vector_search(self, query: str, query_embedding: List[float], k: int) -> List[Dict]:
        """벡터 검색 (기존)"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []
            
            # 벡터 검색 실행 (RPC 함수 사용)
            results = self.supabase.rpc('vector_search', {
                'q_embedding': query_embedding,
                'k': k
            }).execute()
            
            formatted_results = []
            for result in results.data or []:
                formatted_results.append({
                    'id': str(result.get('id', '')),
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'search_score': result.get('search_score', result.get('similarity_score', 0.0)),
                    'search_type': 'vector',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'similarity_score']}
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"벡터 검색 오류: {e}")
            return []
    
    async def _fallback_ilike_search(self, query: str, k: int) -> List[Dict]:
        """폴백 ILIKE 검색 (기존)"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []
            
            keywords = self._extract_korean_keywords(query)
            if not keywords:
                return []
            
            all_results = []
            
            for keyword in keywords[:3]:  # 상위 3개 키워드만 사용
                try:
                    # 제목에서 키워드 검색
                    title_results = self.supabase.table('recipes_keto_enhanced').select('*').ilike('title', f'%{keyword}%').limit(k).execute()
                    
                    # blob(내용)에서 키워드 검색
                    content_results = self.supabase.table('recipes_keto_enhanced').select('*').ilike('blob', f'%{keyword}%').limit(k).execute()
                    
                    all_results.extend(title_results.data or [])
                    all_results.extend(content_results.data or [])
                    
                except Exception as e:
                    print(f"키워드 검색 오류 for '{keyword}': {e}")
                    continue
            
            # 중복 제거
            seen_ids = set()
            unique_results = []
            for result in all_results:
                result_id = result.get('id')
                if result_id and result_id not in seen_ids:
                    seen_ids.add(result_id)
                    unique_results.append(result)
            
            # 결과 포맷팅
            formatted_results = []
            for result in unique_results:
                formatted_results.append({
                    'id': str(result.get('id', '')),
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'search_score': 0.5,  # ILIKE 검색 기본 점수
                    'search_type': 'ilike',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content']}
                })
            
            return formatted_results[:k]
            
        except Exception as e:
            print(f"폴백 ILIKE 검색 오류: {e}")
            return []
    
    async def korean_hybrid_search(self, query: str, k: int = 5) -> List[Dict]:
        """한글 최적화 하이브리드 검색 (스마트 개선)"""
        try:
            print(f"🔍 한글 최적화 하이브리드 검색 시작: '{query}'")
            
            all_results = []
            search_strategy = "hybrid"
            search_message = ""
            
            # 0단계: ILIKE 기반 정확 매칭(가장 단순·안정)
            print("  🔎 0단계: ILIKE 정확 매칭 검색...")
            ilike_exact = await self._exact_ilike_search(query, k)
            if ilike_exact:
                print(f"    ✅ ILIKE 정확 매칭 발견: {len(ilike_exact)}개")
                search_strategy = "exact"
                search_message = "정확한 검색 결과를 찾았습니다."
                for result in ilike_exact:
                    result['final_score'] = result['search_score'] * 2.2
                all_results.extend(ilike_exact)
            else:
                print("    ⚠️ ILIKE 정확 매칭 없음 → FTS 단계로")

            # 1단계: 정확한 매칭 시도 (Full-Text Search 우선)
            print("  📝 1단계: 정확한 매칭 검색...")
            fts_results = await self._full_text_search(query, k)
            if fts_results and any(result['search_score'] > 0.1 for result in fts_results):
                print(f"    ✅ 정확한 매칭 발견: {len(fts_results)}개")
                search_strategy = "exact"
                search_message = "정확한 검색 결과를 찾았습니다."
                for result in fts_results:
                    result['final_score'] = result['search_score'] * 2.0  # 정확한 매칭 가중치 증가
                all_results.extend(fts_results)
            else:
                print("    ⚠️ 정확한 매칭 없음, 부분 매칭 시도...")
                
                # 2단계: 부분 매칭 시도 (Trigram + ILIKE)
                print("  🔤 2단계: 부분 매칭 검색...")
                trigram_results = await self._trigram_similarity_search(query, k)
                ilike_results = await self._fallback_ilike_search(query, k)
                
                if trigram_results or ilike_results:
                    print(f"    ✅ 부분 매칭 발견: Trigram {len(trigram_results)}개, ILIKE {len(ilike_results)}개")
                    search_strategy = "partial"
                    search_message = "정확한 검색어가 없어서 관련 키워드로 검색했습니다."
                    
                    # Trigram 결과 처리
                    for result in trigram_results:
                        result['final_score'] = result['search_score'] * 1.5  # 부분 매칭 가중치
                    all_results.extend(trigram_results)
                    
                    # ILIKE 결과 처리
                    for result in ilike_results:
                        result['final_score'] = result['search_score'] * 1.0  # 기본 가중치
                    all_results.extend(ilike_results)
                else:
                    print("    ⚠️ 부분 매칭도 없음, 하이브리드 검색 시도...")
                    
                    # 3단계: 하이브리드 검색 (모든 방식)
                    print("  🔄 3단계: 하이브리드 검색...")
                    search_strategy = "hybrid"
                    search_message = "종합 검색 결과입니다."
                    
                    # 벡터 검색 (가중치 40%)
                    print("    📊 벡터 검색 실행...")
                    query_embedding = await self._create_embedding(query)
                    if query_embedding:
                        vector_results = await self._vector_search(query, query_embedding, k)
                        for result in vector_results:
                            result['final_score'] = result['search_score'] * 0.4
                        all_results.extend(vector_results)
                    
                    # Full-Text Search (가중치 30%)
                    print("    📝 Full-Text Search 실행...")
                    fts_results = await self._full_text_search(query, k)
                    for result in fts_results:
                        result['final_score'] = result['search_score'] * 0.3
                    all_results.extend(fts_results)
                    
                    # Trigram 유사도 검색 (가중치 20%)
                    print("    🔤 Trigram 유사도 검색 실행...")
                    trigram_results = await self._trigram_similarity_search(query, k)
                    for result in trigram_results:
                        result['final_score'] = result['search_score'] * 0.2
                    all_results.extend(trigram_results)
                    
                    # 폴백 ILIKE 검색 (가중치 10%)
                    print("    🔍 ILIKE 폴백 검색 실행...")
                    ilike_results = await self._fallback_ilike_search(query, k)
                    for result in ilike_results:
                        result['final_score'] = result['search_score'] * 0.1
                    all_results.extend(ilike_results)
            
            # 결과 통합 및 정렬
            if not all_results:
                print("    ❌ 검색 결과가 없습니다.")
                return []
            
            # 중복 제거 (ID 기준)
            seen_ids = set()
            unique_results = []
            for result in all_results:
                result_id = result.get('id')
                if result_id and result_id not in seen_ids:
                    seen_ids.add(result_id)
                    unique_results.append(result)
                elif result_id in seen_ids:
                    # 중복된 경우 더 높은 점수로 업데이트
                    for i, existing in enumerate(unique_results):
                        if existing.get('id') == result_id and result['final_score'] > existing['final_score']:
                            unique_results[i] = result
                            break
            
            # 최종 점수로 정렬
            unique_results.sort(key=lambda x: x['final_score'], reverse=True)
            
            # 상위 k개 결과 반환
            final_results = unique_results[:k]
            
            # 검색 전략과 메시지 추가
            for result in final_results:
                result['search_strategy'] = search_strategy
                result['search_message'] = search_message
            
            print(f"  ✅ 최종 결과: {len(final_results)}개 (전략: {search_strategy})")
            print(f"  💬 {search_message}")
            
            # 결과 요약 출력
            for i, result in enumerate(final_results[:3], 1):
                print(f"    {i}. {result['title']} (점수: {result['final_score']:.3f}, 타입: {result['search_type']})")
            
            return final_results
            
        except Exception as e:
            print(f"❌ 한글 하이브리드 검색 오류: {e}")
            return []
    
    async def search(self, query: str, profile: str = "", max_results: int = 5) -> List[Dict]:
        """간단한 검색 인터페이스 (한글 최적화 + 스마트 개선)"""
        try:
            # 프로필에서 필터 추출
            filters = {}
            if profile:
                if "아침" in profile or "morning" in profile.lower():
                    filters['category'] = '아침'
                if "쉬운" in profile or "easy" in profile.lower():
                    filters['difficulty'] = '쉬움'
            
            # 메시지에서 식사-시간 키워드 감지 → 보조 키워드로 강화
            adjusted_query = query
            meal_hint = None
            if any(k in query for k in ["아침", "브렉퍼스트", "아침식사", "morning", "breakfast"]):
                meal_hint = '아침'
                adjusted_query = f"{query} 오믈렛 계란 샐러드 요거트"
            elif any(k in query for k in ["점심", "런치", "lunch"]):
                meal_hint = '점심'
                adjusted_query = f"{query} 샐러드 스테이크 볶음 구이"
            elif any(k in query for k in ["저녁", "디너", "dinner"]):
                meal_hint = '저녁'
                adjusted_query = f"{query} 스테이크 구이 찜 볶음"

            # 스마트 하이브리드 검색 실행(강화 쿼리 우선)
            results = await self.korean_hybrid_search(adjusted_query, max_results)
            if not results and adjusted_query != query:
                results = await self.korean_hybrid_search(query, max_results)
            
            # 결과 포맷팅 (검색 전략과 메시지 포함)
            formatted_results = []
            search_message = ""
            search_strategy = "unknown"
            
            for result in results:
                # 첫 번째 결과에서 검색 전략과 메시지 추출
                if not search_message:
                    search_message = result.get('search_message', '')
                    search_strategy = result.get('search_strategy', 'unknown')
                    if meal_hint and not search_message:
                        search_message = f"'{meal_hint}' 키워드를 반영해 레시피를 추천했습니다."
                
                formatted_results.append({
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'similarity': result.get('final_score', 0.0),
                    'metadata': result.get('metadata', {}),
                    'search_types': [result.get('search_type', 'hybrid')],
                    'search_strategy': search_strategy
                })
            
            # 검색 결과가 없는 경우 메시지 추가
            if not formatted_results:
                formatted_results.append({
                    'title': '검색 결과 없음',
                    'content': '검색 결과가 없습니다. 다른 키워드를 시도해보세요.',
                    'similarity': 0.0,
                    'metadata': {'search_message': '검색 결과가 없습니다.'},
                    'search_types': ['none'],
                    'search_strategy': 'none'
                })
            
            # 검색 메시지 출력
            if search_message:
                print(f"💬 사용자 안내: {search_message}")
            
            return formatted_results
            
        except Exception as e:
            print(f"Search error: {e}")
            return [{
                'title': '검색 오류',
                'content': f'검색 중 오류가 발생했습니다: {str(e)}',
                'similarity': 0.0,
                'metadata': {'error': str(e)},
                'search_types': ['error'],
                'search_strategy': 'error'
            }]

    async def smart_search(self, query: str, k: int = 5) -> Dict[str, Any]:
        """스마트 검색 (사용자 피드백 포함)"""
        try:
            print(f"🧠 스마트 검색 시작: '{query}'")
            
            # 1단계: 정확한 매칭 시도
            print("  🎯 1단계: 정확한 매칭 검색...")
            fts_results = await self._full_text_search(query, k)
            
            if fts_results and any(result['search_score'] > 0.1 for result in fts_results):
                print(f"    ✅ 정확한 매칭 발견: {len(fts_results)}개")
                return {
                    'results': fts_results,
                    'search_strategy': 'exact',
                    'message': '정확한 검색 결과를 찾았습니다.',
                    'total_count': len(fts_results)
                }
            
            # 2단계: 부분 매칭 시도
            print("  🔍 2단계: 부분 매칭 검색...")
            trigram_results = await self._trigram_similarity_search(query, k)
            ilike_results = await self._fallback_ilike_search(query, k)
            
            if trigram_results or ilike_results:
                print(f"    ✅ 부분 매칭 발견: Trigram {len(trigram_results)}개, ILIKE {len(ilike_results)}개")
                
                # 결과 통합
                all_partial_results = []
                all_partial_results.extend(trigram_results)
                all_partial_results.extend(ilike_results)
                
                # 중복 제거
                seen_ids = set()
                unique_results = []
                for result in all_partial_results:
                    result_id = result.get('id')
                    if result_id and result_id not in seen_ids:
                        seen_ids.add(result_id)
                        unique_results.append(result)
                
                return {
                    'results': unique_results[:k],
                    'search_strategy': 'partial',
                    'message': '정확한 검색어가 없어서 관련 키워드로 검색했습니다.',
                    'total_count': len(unique_results)
                }
            
            # 3단계: 하이브리드 검색
            print("  🔄 3단계: 하이브리드 검색...")
            hybrid_results = await self.korean_hybrid_search(query, k)
            
            if hybrid_results:
                return {
                    'results': hybrid_results,
                    'search_strategy': 'hybrid',
                    'message': '종합 검색 결과입니다.',
                    'total_count': len(hybrid_results)
                }
            
            # 4단계: 검색 결과 없음
            print("    ❌ 모든 검색 방식에서 결과 없음")
            return {
                'results': [],
                'search_strategy': 'none',
                'message': '검색 결과가 없습니다. 다른 키워드를 시도해보세요.',
                'total_count': 0
            }
            
        except Exception as e:
            print(f"❌ 스마트 검색 오류: {e}")
            return {
                'results': [],
                'search_strategy': 'error',
                'message': f'검색 중 오류가 발생했습니다: {str(e)}',
                'total_count': 0
            }

# 전역 한글 검색 도구 인스턴스
korean_search_tool = KoreanSearchTool()
