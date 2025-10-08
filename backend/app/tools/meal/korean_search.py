"""
한글 최적화 검색 도구
PostgreSQL Full-Text Search + pg_trgm + 벡터 검색 통합
"""

import re
import openai
import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.core.database import supabase
from app.core.config import settings

class KoreanSearchTool:
    """한글 최적화 검색 도구 클래스"""
    
    def __init__(self):
        self.supabase = supabase
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # 동의어 사전 로드
        synonym_file = Path(__file__).parent.parent.parent / 'data' / 'ingredient_synonyms.json'
        try:
            with open(synonym_file, 'r', encoding='utf-8') as f:
                self.synonym_data = json.load(f)
                print(f"✅ 동의어 사전 로드 완료: {synonym_file}")
        except Exception as e:
            print(f"⚠️ 동의어 사전 로드 실패: {e}")
            self.synonym_data = {"알레르기": {}, "비선호": {}}
    
    def _expand_with_synonyms(self, words: List[str], category: str) -> List[str]:
        """단어 리스트를 동의어로 확장"""
        expanded = []
        synonym_dict = self.synonym_data.get(category, {})
        
        for word in words:
            expanded.append(word)  # 원래 단어 추가
            if word in synonym_dict:
                expanded.extend(synonym_dict[word])  # 동의어 추가
        
        return expanded
    
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
                                'allergens': row.get('allergens', []),
                                'ingredients': row.get('ingredients', []),
                                'search_score': row.get('search_score', 1.0),
                                'search_type': 'ilike_exact',
                                'metadata': {kk: vv for kk, vv in row.items() if kk not in ['id','title','content','search_score','allergens','ingredients']}
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
                    'allergens': result.get('allergens', []),
                    'ingredients': result.get('ingredients', []),
                    'search_score': result.get('search_score', 1.0),
                    'search_type': 'pgroonga',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'search_score', 'allergens', 'ingredients']}
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
                    'allergens': result.get('allergens', []),
                    'ingredients': result.get('ingredients', []),
                    'search_score': result.get('search_score', result.get('fts_score', 0.0)),
                    'search_type': 'fts',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'fts_score', 'allergens', 'ingredients']}
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
                    'allergens': result.get('allergens', []),
                    'ingredients': result.get('ingredients', []),
                    'search_score': result.get('search_score', result.get('similarity_score', 0.0)),
                    'search_type': 'trigram',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'similarity_score', 'allergens', 'ingredients']}
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Trigram 유사도 검색 오류: {e}")
            return []
    
    async def _vector_search(self, query: str, query_embedding: List[float], k: int, user_id: Optional[str] = None, meal_type: Optional[str] = None) -> List[Dict]:
        """벡터 검색 (사용자 프로필 기반 필터링)"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []
            
            # 사용자 프로필에서 알레르기/비선호 가져오기
            exclude_allergens_embeddings = None
            exclude_dislikes_embeddings = None
            exclude_allergens_names = None
            exclude_dislikes_names = None
            
            if user_id:
                from app.tools.shared.profile_tool import user_profile_tool
                user_preferences = await user_profile_tool.get_user_preferences(user_id)
                
                if user_preferences.get("success"):
                    prefs = user_preferences["preferences"]
                    user_allergies = prefs.get("allergies", [])
                    user_dislikes = prefs.get("dislikes", [])
                    
                    # 알레르기 키워드를 임베딩으로 변환 (하나의 문자열로 합쳐서)
                    if user_allergies:
                        allergy_text = ' '.join(user_allergies)
                        allergy_embedding = await self._create_embedding(allergy_text)
                        exclude_allergens_embeddings = [allergy_embedding]  # 배열로 감싸기
                        exclude_allergens_names = user_allergies
                        print(f"🔍 알레르기 임베딩 생성 (1개): {user_allergies}")
                    
                    # 비선호 키워드를 임베딩으로 변환 (하나의 문자열로 합쳐서)
                    if user_dislikes:
                        dislike_text = ' '.join(user_dislikes)
                        dislike_embedding = await self._create_embedding(dislike_text)
                        exclude_dislikes_embeddings = [dislike_embedding]  # 배열로 감싸기
                        exclude_dislikes_names = user_dislikes
                        print(f"🔍 비선호 임베딩 생성 (1개): {user_dislikes}")
            
            # 벡터 검색 실행 (RPC 함수 사용)
            rpc_params = {
                'query_embedding': query_embedding,
                'match_count': k,
                'similarity_threshold': 0.0
            }
            
            # 단일 벡터로 전달 (배열의 첫 번째 요소)
            if exclude_allergens_embeddings:
                rpc_params['exclude_allergens_embedding'] = exclude_allergens_embeddings[0]
            if exclude_dislikes_embeddings:
                rpc_params['exclude_dislikes_embedding'] = exclude_dislikes_embeddings[0]
            if exclude_allergens_names:
                rpc_params['exclude_allergens_names'] = exclude_allergens_names
            if exclude_dislikes_names:
                rpc_params['exclude_dislikes_names'] = exclude_dislikes_names
            
            # 🆕 meal_type 필터 추가
            if meal_type:
                rpc_params['meal_type_filter'] = meal_type
                print(f"🍽️ meal_type 필터 적용: {meal_type}")
            
            print(f"🔍 RPC 파라미터: allergens={len(exclude_allergens_names) if exclude_allergens_names else 0}, dislikes={len(exclude_dislikes_names) if exclude_dislikes_names else 0}")
            
            results = self.supabase.rpc('vector_search', rpc_params).execute()
            
            formatted_results = []
            filtered_count = 0
            
            # 동의어 확장
            expanded_allergens = self._expand_with_synonyms(exclude_allergens_names, '알레르기') if exclude_allergens_names else []
            expanded_dislikes = self._expand_with_synonyms(exclude_dislikes_names, '비선호') if exclude_dislikes_names else []
            
            for result in results.data or []:
                # 🚨 Python 레벨 필터링: title, ingredients에서 알레르기/비선호 체크 (동의어 포함)
                title = result.get('title', '').lower()
                ingredients = result.get('ingredients', [])
                ingredients_lower = [ing.lower() for ing in ingredients] if ingredients else []
                
                # 알레르기 체크 (동의어 포함)
                if expanded_allergens:
                    allergy_found = False
                    for allergy in expanded_allergens:
                        allergy_lower = allergy.lower()
                        # title에 있는지 체크
                        if allergy_lower in title:
                            print(f"    ⚠️ 알레르기 제외: '{result.get('title')}' (제목에 '{allergy}' 포함)")
                            allergy_found = True
                            break
                        # ingredients에 있는지 체크 (부분 일치)
                        for ing in ingredients_lower:
                            if allergy_lower in ing:
                                print(f"    ⚠️ 알레르기 제외: '{result.get('title')}' (재료 '{ing}'에 '{allergy}' 포함)")
                                allergy_found = True
                                break
                        if allergy_found:
                            break
                    if allergy_found:
                        filtered_count += 1
                        continue
                
                # 비선호 체크 (동의어 포함)
                if expanded_dislikes:
                    dislike_found = False
                    for dislike in expanded_dislikes:
                        dislike_lower = dislike.lower()
                        # title에 있는지 체크
                        if dislike_lower in title:
                            print(f"    ⚠️ 비선호 제외: '{result.get('title')}' (제목에 '{dislike}' 포함)")
                            dislike_found = True
                            break
                        # ingredients에 있는지 체크 (부분 일치)
                        for ing in ingredients_lower:
                            if dislike_lower in ing:
                                print(f"    ⚠️ 비선호 제외: '{result.get('title')}' (재료 '{ing}'에 '{dislike}' 포함)")
                                dislike_found = True
                                break
                        if dislike_found:
                            break
                    if dislike_found:
                        filtered_count += 1
                        continue
                
                # 통과!
                formatted_results.append({
                    'id': str(result.get('id', '')),
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'allergens': result.get('allergens', []),
                    'ingredients': result.get('ingredients', []),
                    'search_score': result.get('search_score', result.get('similarity_score', 0.0)),
                    'search_type': 'vector',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'similarity_score', 'allergens', 'ingredients']}
                })
            
            if filtered_count > 0:
                print(f"    🔍 Python 필터링: {filtered_count}개 제외됨")
            
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
                    # 제목에서 키워드 검색만 사용 (JSONB 검색 제거)
                    title_results = self.supabase.table('recipe_blob_emb').select('*').ilike('title', f'%{keyword}%').limit(k).execute()
                    
                    all_results.extend(title_results.data or [])
                    
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
                    'allergens': result.get('allergens', []),
                    'ingredients': result.get('ingredients', []),
                    'search_score': 0.5,  # ILIKE 검색 기본 점수
                    'search_type': 'ilike',
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'allergens', 'ingredients']}
                })
            
            return formatted_results[:k]
            
        except Exception as e:
            print(f"폴백 ILIKE 검색 오류: {e}")
            return []
    
    async def korean_hybrid_search(self, query: str, k: int = 5, user_id: Optional[str] = None, meal_type: Optional[str] = None) -> List[Dict]:
        """한글 최적화 하이브리드 검색 (병렬 실행 방식)"""
        try:
            print(f"🔍 한글 최적화 하이브리드 검색 시작: '{query}'")
            
            all_results = []
            search_strategy = "hybrid"
            search_message = "종합 검색 결과입니다."
            
            # 모든 검색 방식을 병렬로 실행
            print("  🚀 모든 검색 방식 병렬 실행...")
            
            # 1. 벡터 검색 (가중치 40% - 가장 높음)
            print("    📊 벡터 검색 실행...")
            query_embedding = await self._create_embedding(query)
            vector_results = []
            if query_embedding:
                vector_results = await self._vector_search(query, query_embedding, k, user_id, meal_type)
                for result in vector_results:
                    result['final_score'] = result['search_score'] * 0.4
                    result['search_type'] = 'vector'
                all_results.extend(vector_results)
                print(f"    ✅ 벡터 검색 완료: {len(vector_results)}개")
            else:
                print("    ⚠️ 임베딩 생성 실패, 벡터 검색 건너뜀")
            
            # 🚨 user_id가 있으면 벡터 검색만 사용 (알레르기/비선호 필터링 적용)
            # 다른 검색 방법은 필터링을 우회하므로 실행하지 않음
            if user_id:
                print("    ⚠️ 알레르기/비선호 필터링 적용 - 벡터 검색만 사용")
                ilike_exact = []
                fts_results = []
                trigram_results = []
            else:
                # 2. 정확한 ILIKE 매칭 (가중치 35%)
                print("    🔎 ILIKE 정확 매칭 검색...")
                ilike_exact = await self._exact_ilike_search(query, k)
                for result in ilike_exact:
                    result['final_score'] = result['search_score'] * 0.35
                    result['search_type'] = 'exact_ilike'
                all_results.extend(ilike_exact)
                print(f"    ✅ ILIKE 정확 매칭 완료: {len(ilike_exact)}개")
                
                # 3. Full-Text Search (가중치 30%)
                print("    📝 Full-Text Search 실행...")
                fts_results = await self._full_text_search(query, k)
                for result in fts_results:
                    result['final_score'] = result['search_score'] * 0.3
                    result['search_type'] = 'fts'
                all_results.extend(fts_results)
                print(f"    ✅ FTS 검색 완료: {len(fts_results)}개")
                
                # 4. Trigram 유사도 검색 (가중치 20%)
                print("    🔤 Trigram 검색 실행...")
                trigram_results = await self._trigram_similarity_search(query, k)
                for result in trigram_results:
                    result['final_score'] = result['search_score'] * 0.2
                    result['search_type'] = 'trigram'
                all_results.extend(trigram_results)
                print(f"    ✅ Trigram 검색 완료: {len(trigram_results)}개")
            
            # 검색 전략 결정 (결과 종류에 따라)
            if vector_results and len(vector_results) >= 2:
                search_strategy = "vector_strong"
                search_message = "AI 임베딩 검색으로 관련성 높은 결과를 찾았습니다."
            elif ilike_exact and len(ilike_exact) >= 2:
                search_strategy = "exact"
                search_message = "정확한 검색 결과를 찾았습니다."
            elif fts_results and len(fts_results) >= 2:
                search_strategy = "fts_strong"
                search_message = "전문 검색으로 관련 내용을 찾았습니다."
            elif any([vector_results, ilike_exact, fts_results, trigram_results]):
                search_strategy = "partial"
                search_message = "관련 키워드로 검색한 결과입니다."
            
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
                    'id': result.get('id', ''),
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'allergens': result.get('allergens', []),
                    'ingredients': result.get('ingredients', []),
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
