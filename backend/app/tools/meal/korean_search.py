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
from app.core.redis_cache import redis_cache

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
        
        # 임베딩 캐시 (성능 최적화)
        self._embedding_cache = {}
        self._normalization_cache = {}
        self._expansion_cache = {}
        self._query_embedding_cache = {}  # 쿼리 임베딩 캐시 추가
        self._search_results_cache = {}   # 검색 결과 캐시 추가
        
        # 캐시 크기 제한 (메모리 최적화)
        self._max_cache_size = 100  # 최대 100개 항목
    
    def _manage_cache_size(self, cache_dict: dict):
        """캐시 크기 관리 (LRU 방식)"""
        if len(cache_dict) > self._max_cache_size:
            # 가장 오래된 항목 제거 (FIFO)
            oldest_key = next(iter(cache_dict))
            del cache_dict[oldest_key]
            print(f"    📊 캐시 크기 관리: {oldest_key[:30]}... 제거")
    
    def _expand_with_synonyms(self, words: List[str], category: str) -> List[str]:
        """단어 리스트를 동의어로 확장 (캐싱 적용)"""
        if not words:
            return []
        
        # 캐시 확인
        cache_key = f"expand_{category}_{hash(tuple(sorted(words)))}"
        if cache_key in self._expansion_cache:
            print(f"📊 확장 캐시 히트: {words}")
            return self._expansion_cache[cache_key]
        
        expanded = []
        synonym_dict = self.synonym_data.get(category, {})
        
        for word in words:
            expanded.append(word)  # 원래 단어 추가
            if word in synonym_dict:
                # 동의어 추가 (최대 5개로 제한)
                synonyms = synonym_dict[word][:5]  # 처음 5개만 사용
                expanded.extend(synonyms)
        
        # 중복 제거 (순서 유지)
        seen = set()
        unique_expanded = []
        for item in expanded:
            if item not in seen:
                seen.add(item)
                unique_expanded.append(item)
        
        # 캐시 저장
        self._expansion_cache[cache_key] = unique_expanded
        self._manage_cache_size(self._expansion_cache)
        print(f"✅ 동의어 확장 완료: {words} → {len(unique_expanded)}개 (캐시 저장)")
        print(f"    🔍 확장된 항목들: {unique_expanded[:10]}...")  # 처음 10개만 표시
        return unique_expanded
    
    def _normalize_to_canonical(self, words: List[str], category: str) -> List[str]:
        """입력 단어 리스트를 표준명(canonical)으로 정규화 (캐싱 적용)
        
        Args:
            words: 입력 단어 리스트 (알레르기/비선호/검색 키워드)
            category: 카테고리 ("알레르기" 또는 "비선호")
        
        Returns:
            표준명 리스트 (정확 비교용)
        """
        if not words:
            return []
        
        # 캐시 확인
        cache_key = f"normalize_{category}_{hash(tuple(sorted(words)))}"
        if cache_key in self._normalization_cache:
            print(f"📊 정규화 캐시 히트: {words}")
            return self._normalization_cache[cache_key]
        
        synonym_dict = self.synonym_data.get(category, {})
        canonicals = []
        
        for word in words:
            if not word:
                continue
            
            # 소문자화 및 공백 트림
            normalized = word.strip().lower()
            
            # 역매핑: 동의어 → 표준명
            found_canonical = None
            for canonical, synonyms in synonym_dict.items():
                # 표준명 자체와 일치하는 경우
                if normalized == canonical.lower():
                    found_canonical = canonical
                    break
                # 동의어 리스트에서 찾기
                for syn in synonyms:
                    if normalized == syn.lower():
                        found_canonical = canonical
                        break
                if found_canonical:
                    break
            
            if found_canonical:
                canonicals.append(found_canonical)
            else:
                # 표준명을 찾지 못한 경우 원본 추가
                canonicals.append(word.strip())
        
        # 중복 제거
        result = list(set(canonicals))
        
        # 캐시 저장
        self._normalization_cache[cache_key] = result
        self._manage_cache_size(self._normalization_cache)
        print(f"✅ 정규화 완료: {words} → {result} (캐시 저장)")
        return result
    
    def _tokenize_ingredients(self, text: str) -> List[str]:
        """재료 텍스트를 토큰화
        
        Args:
            text: 재료 문자열
        
        Returns:
            토큰 리스트 (공백, 쉼표, 특수문자 기준 분리)
        """
        if not text:
            return []
        
        # 한글, 영문, 숫자만 추출 (공백과 구분자 기준)
        tokens = re.split(r'[,\s\(\)\[\]\{\}/]+', text.lower())
        
        # 빈 문자열 제거 및 정규화
        return [t.strip() for t in tokens if t.strip()]
    
    def _exact_match_filter(self, text: str, banned_terms: List[str]) -> bool:
        """정확 매칭 필터 (부분문자열 금지)
        
        Args:
            text: 검사할 텍스트 (제목 또는 재료)
            banned_terms: 금지 단어 리스트 (표준명)
        
        Returns:
            True if 금지 단어가 발견됨, False otherwise
        """
        if not text or not banned_terms:
            return False
        
        # 텍스트 토큰화
        tokens = self._tokenize_ingredients(text)
        
        # 표준명을 표준명으로 정규화 (동의어 확장)
        for banned in banned_terms:
            banned_lower = banned.lower()
            
            # 한글 토큰 정확 일치
            for token in tokens:
                if token == banned_lower:
                    return True
            
            # 영문 단어 경계 정규식 (공백이 있는 경우 대비)
            # 예: "bell pepper", "sesame oil" 등
            if ' ' in banned_lower:
                # 복합어는 원문에서 직접 검색
                if banned_lower in text.lower():
                    return True
        
        return False
    
    async def _create_embedding(self, text: str) -> List[float]:
        """텍스트를 임베딩으로 변환 (캐싱 적용)"""
        try:
            # 캐시 확인
            cache_key = f"embedding_{hash(text)}"
            if cache_key in self._embedding_cache:
                print(f"📊 임베딩 캐시 히트: {text[:50]}...")
                return self._embedding_cache[cache_key]
            
            print(f"📊 임베딩 생성 중: {text[:50]}...")
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embedding = response.data[0].embedding
            
            # 캐시 저장
            self._embedding_cache[cache_key] = embedding
            self._manage_cache_size(self._embedding_cache)
            print(f"✅ 임베딩 생성 완료: {len(embedding)}차원 (캐시 저장)")
            return embedding
        except Exception as e:
            print(f"❌ 임베딩 생성 오류: {e}")
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
                                'url': row.get('url'),  # URL 추가
                                'metadata': {kk: vv for kk, vv in row.items() if kk not in ['id','title','content','search_score','allergens','ingredients','url']}
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
                    'url': result.get('url'),  # URL 추가
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'fts_score', 'allergens', 'ingredients', 'url']}
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
                    'url': result.get('url'),  # URL 추가
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'similarity_score', 'allergens', 'ingredients', 'url']}
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Trigram 유사도 검색 오류: {e}")
            return []
    
    async def _vector_search(self, query: str, query_embedding: List[float], k: int, user_id: Optional[str] = None, meal_type: Optional[str] = None,
                            allergies: Optional[List[str]] = None, dislikes: Optional[List[str]] = None) -> List[Dict]:
        """벡터 검색 (사용자 프로필 기반 필터링 + 임시 제약조건)"""
        try:
            # print(f"🔍 DEBUG: _vector_search 함수 시작 - query='{query}', k={k}, user_id={user_id}")  # 임시 비활성화
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                # print(f"🔍 DEBUG: Supabase가 None이거나 DummySupabase - 빈 결과 반환")  # 임시 비활성화
                return []
            
            # 알레르기/비선호 정보 준비
            exclude_allergens_embeddings = None
            exclude_dislikes_embeddings = None
            exclude_allergens_names = None
            exclude_dislikes_names = None
            
            # 1. 파라미터로 전달된 allergies/dislikes가 있으면 우선 사용
            user_allergies = allergies if allergies is not None else []
            user_dislikes = dislikes if dislikes is not None else []
            # print(f"    🔍 전달받은 알레르기: {user_allergies}")  # 임시 비활성화
            # print(f"    🔍 전달받은 비선호: {user_dislikes}")  # 임시 비활성화
            
            # 2. 파라미터가 없으면 프로필에서 조회
            if not user_allergies and not user_dislikes and user_id:
            # print(f"    🔍 프로필에서 알레르기 정보 조회: user_id={user_id}")  # 임시 비활성화
                from app.tools.shared.profile_tool import user_profile_tool
                user_preferences = await user_profile_tool.get_user_preferences(user_id)
                
                if user_preferences.get("success"):
                    prefs = user_preferences["preferences"]
                    user_allergies = prefs.get("allergies", [])
                    user_dislikes = prefs.get("dislikes", [])
                    # print(f"    🔍 프로필에서 조회된 알레르기: {user_allergies}")  # 임시 비활성화
                    # print(f"    🔍 프로필에서 조회된 비선호: {user_dislikes}")  # 임시 비활성화
                else:
                    print(f"    ⚠️ 프로필 조회 실패: {user_preferences}")
            
            # 알레르기 임베딩 생성
            if user_allergies:
                allergy_text = ' '.join(user_allergies)
                allergy_embedding = await self._create_embedding(allergy_text)
                exclude_allergens_embeddings = [allergy_embedding]
                exclude_allergens_names = user_allergies
                # print(f"🔍 알레르기 임베딩 생성 (1개): {user_allergies}")  # 임시 비활성화
            
            # 비선호 임베딩 생성
            if user_dislikes:
                dislike_text = ' '.join(user_dislikes)
                dislike_embedding = await self._create_embedding(dislike_text)
                exclude_dislikes_embeddings = [dislike_embedding]
                exclude_dislikes_names = user_dislikes
                print(f"🔍 비선호 임베딩 생성 (1개): {user_dislikes}")
            
            # 벡터 검색 실행 (RPC 함수 사용) - 최대한 많은 데이터 검색
            # 알레르기 필터링을 고려하여 충분한 데이터 확보
            max_search_count = 1000  # 최대 1000개 검색 (DB의 모든 데이터)
            
            rpc_params = {
                'query_embedding': query_embedding,
                'match_count': max_search_count,
                'similarity_threshold': 0.0
            }
            # print(f"    🔍 최대 검색 수: {max_search_count}개 (알레르기 필터링 고려)")  # 임시 비활성화
            
            # 단일 벡터로 전달 (배열의 첫 번째 요소)
            if exclude_allergens_embeddings:
                rpc_params['exclude_allergens_embedding'] = exclude_allergens_embeddings[0]
            if exclude_dislikes_embeddings:
                rpc_params['exclude_dislikes_embedding'] = exclude_dislikes_embeddings[0]
            if exclude_allergens_names:
                rpc_params['exclude_allergens_names'] = exclude_allergens_names
            if exclude_dislikes_names:
                rpc_params['exclude_dislikes_names'] = exclude_dislikes_names
            
            # 🆕 meal_type 필터 추가 (항상 전달하여 함수 오버로딩 모호성 제거)
            rpc_params['meal_type_filter'] = meal_type if meal_type else None
            if meal_type:
                print(f"🍽️ meal_type 필터 적용: {meal_type}")
            
            print(f"🔍 RPC 파라미터: allergens={len(exclude_allergens_names) if exclude_allergens_names else 0}, dislikes={len(exclude_dislikes_names) if exclude_dislikes_names else 0}")
            
            results = self.supabase.rpc('vector_search', rpc_params).execute()
            
            formatted_results = []
            filtered_count = 0
            
            # 표준명으로 정규화 (동의어 확장 대신)
            canonical_allergens = self._normalize_to_canonical(exclude_allergens_names, '알레르기') if exclude_allergens_names else []
            canonical_dislikes = self._normalize_to_canonical(exclude_dislikes_names, '비선호') if exclude_dislikes_names else []
            
            # 동의어 확장 (캐싱된 함수 사용)
            expanded_allergens = self._expand_with_synonyms(canonical_allergens, '알레르기') if canonical_allergens else []
            expanded_dislikes = self._expand_with_synonyms(canonical_dislikes, '비선호') if canonical_dislikes else []
            
            # print(f"    🔍 정규화된 알레르기: {canonical_allergens}")  # 임시 비활성화
            # print(f"    🔍 확장된 알레르기: {len(expanded_allergens)}개 - {expanded_allergens[:10]}...")  # 임시 비활성화
            # print(f"    🔍 정규화된 비선호: {canonical_dislikes}")  # 임시 비활성화
            # print(f"    🔍 확장된 비선호: {len(expanded_dislikes)}개 - {expanded_dislikes[:10]}...")  # 임시 비활성화
            # print(f"    🚨 알레르기 필터링 시작 - 총 {len(results.data or [])}개 결과 검사")  # 임시 비활성화
            
            for result in results.data or []:
                # 🚨 Python 레벨 필터링: title, ingredients에서 알레르기/비선호 체크
                title = result.get('title', '')
                ingredients = result.get('ingredients', [])
                should_skip = False
                # print(f"    🔍 검사 중: '{title}' (재료: {ingredients[:3]}...)")  # 임시 비활성화
                
                # 알레르기 체크 (토큰 매칭 + 부분 문자열 매칭)
                # print(f"    🔍 알레르기 체크 조건: expanded_allergens={len(expanded_allergens) if expanded_allergens else 0}, should_skip={should_skip}")  # 임시 비활성화
                if expanded_allergens and not should_skip:
                    # 제목 체크 (토큰 매칭)
                    if self._exact_match_filter(title, expanded_allergens):
                        print(f"    ⚠️ 알레르기 제외: '{title}' (제목에 알레르기 재료 포함)")
                        filtered_count += 1
                        should_skip = True
                    
                    # 제목 체크 (부분 문자열 매칭 - "계란샐러드" 같은 경우)
                    if not should_skip:
                        title_lower = title.lower()
                        for allergen in expanded_allergens:
                            if allergen in title_lower:
                                print(f"    ⚠️ 알레르기 제외: '{title}' (제목에 '{allergen}' 포함)")
                                print(f"        🔍 매칭된 알레르기: '{allergen}' in '{title_lower}'")
                                filtered_count += 1
                                should_skip = True
                                break
                    
                    # 재료 체크
                    if not should_skip:
                        for ing in ingredients:
                            if self._exact_match_filter(ing, expanded_allergens):
                                print(f"    ⚠️ 알레르기 제외: '{title}' (재료 '{ing}'에 알레르기 재료 포함)")
                                print(f"        🔍 매칭된 재료: '{ing}' in 알레르기 목록")
                                filtered_count += 1
                                should_skip = True
                                break
                
                # 비선호 체크 (토큰 매칭 + 부분 문자열 매칭)
                if expanded_dislikes and not should_skip:
                    # 제목 체크 (토큰 매칭)
                    if self._exact_match_filter(title, expanded_dislikes):
                        # print(f"    ⚠️ 비선호 제외: '{title}' (제목에 비선호 재료 포함)")  # 임시 비활성화
                        filtered_count += 1
                        should_skip = True
                    
                    # 제목 체크 (부분 문자열 매칭 - "계란샐러드" 같은 경우)
                    if not should_skip:
                        title_lower = title.lower()
                        for dislike in expanded_dislikes:
                            if dislike in title_lower:
                                # print(f"    ⚠️ 비선호 제외: '{title}' (제목에 '{dislike}' 포함)")  # 임시 비활성화
                                filtered_count += 1
                                should_skip = True
                                break
                    
                    # 재료 체크
                    if not should_skip:
                        for ing in ingredients:
                            if self._exact_match_filter(ing, expanded_dislikes):
                                # print(f"    ⚠️ 비선호 제외: '{title}' (재료 '{ing}'에 비선호 재료 포함)")  # 임시 비활성화
                                filtered_count += 1
                                should_skip = True
                                break
                
                if should_skip:
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
                    'url': result.get('url'),  # URL 추가
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'similarity_score', 'allergens', 'ingredients', 'url']}
                })
            
            if filtered_count > 0:
                print(f"    🔍 Python 필터링: {filtered_count}개 제외됨")
            
            print(f"    ✅ 최종 결과: {len(formatted_results)}개 (검색 {len(results.data or [])}개 → 필터링 후 {len(formatted_results)}개)")
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 벡터 검색 오류: {e}")
            import traceback
            print(f"🔍 DEBUG: 벡터 검색 예외 상세 정보:")
            traceback.print_exc()
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
                    'url': result.get('url'),  # URL 추가
                    'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'allergens', 'ingredients', 'url']}
                })
            
            return formatted_results[:k]
            
        except Exception as e:
            print(f"폴백 ILIKE 검색 오류: {e}")
            return []
    
    async def korean_hybrid_search(self, query: str, k: int = 5, user_id: Optional[str] = None, meal_type: Optional[str] = None, 
                                   allergies: Optional[List[str]] = None, dislikes: Optional[List[str]] = None) -> List[Dict]:
        """한글 최적화 하이브리드 검색 (병렬 실행 방식 + 결과 캐싱)"""
        try:
            print(f"🔍 한글 최적화 하이브리드 검색 시작: '{query}'")
            
            # 스마트 캐시 시스템: 다양성 확보를 위한 랜덤 요소 추가
            import random
            import time
            
            # 기본 캐시 키
            base_cache_key = f"search_{hash(query)}_{k}_{user_id}_{meal_type}_{hash(tuple(sorted(allergies or [])))}_{hash(tuple(sorted(dislikes or [])))}"
            
            # 다양성을 위한 랜덤 요소 (매번 다른 결과를 위해 캐시 비활성화)
            # random_seed = int(time.time() / 300)  # 5분마다 변경
            # random_factor = random.randint(1, 10)
            # cache_key = f"{base_cache_key}_{random_seed}_{random_factor}"
            
            # 🚀 다양성 확보를 위해 캐시 비활성화 (매번 새로운 결과)
            cache_key = f"{base_cache_key}_{int(time.time())}_{random.randint(1, 1000)}"
            
            print(f"  🎲 스마트 캐시 키: {cache_key}")
            
            # Redis 캐시 확인
            cached_result = redis_cache.get(cache_key)
            if cached_result:
                print(f"    📊 Redis 검색 결과 캐시 히트: {query[:30]}...")
                return cached_result
            
            # 메모리 캐시 확인 (폴백)
            if cache_key in self._search_results_cache:
                print(f"    📊 메모리 검색 결과 캐시 히트: {query[:30]}...")
                return self._search_results_cache[cache_key]
            
            all_results = []
            search_strategy = "hybrid"
            search_message = "종합 검색 결과입니다."
            
            # 모든 검색 방식을 병렬로 실행
            print("  🚀 모든 검색 방식 병렬 실행...")
            
            # 1. 벡터 검색 (가중치 40% - 가장 높음)
            print("    📊 벡터 검색 실행...")
            
            # 쿼리 임베딩 캐싱 (Redis 우선, 메모리 폴백)
            query_cache_key = f"query_{hash(query)}"
            
            # Redis에서 쿼리 임베딩 확인
            cached_embedding = redis_cache.get(query_cache_key)
            if cached_embedding:
                print(f"    📊 Redis 쿼리 임베딩 캐시 히트: {query[:30]}...")
                query_embedding = cached_embedding
            elif query_cache_key in self._query_embedding_cache:
                print(f"    📊 쿼리 임베딩 캐시 히트: {query[:30]}...")
                query_embedding = self._query_embedding_cache[query_cache_key]
            else:
                query_embedding = await self._create_embedding(query)
                if query_embedding:
                    # Redis에 쿼리 임베딩 저장 (TTL: 1시간)
                    redis_cache.set(query_cache_key, query_embedding, ttl=3600)
                    # 메모리 캐시에도 저장 (폴백용)
                    self._query_embedding_cache[query_cache_key] = query_embedding
                    self._manage_cache_size(self._query_embedding_cache)
                    print(f"    📊 쿼리 임베딩 캐시 저장: {query[:30]}...")
            
            vector_results = []
            if query_embedding:
                vector_results = await self._vector_search(query, query_embedding, k, user_id, meal_type, allergies, dislikes)
                for result in vector_results:
                    result['final_score'] = result['search_score'] * 0.4
                    result['search_type'] = 'vector'
                all_results.extend(vector_results)
                # print(f"    ✅ 벡터 검색 완료: {len(vector_results)}개")  # 임시 비활성화
            else:
                print("    ⚠️ 임베딩 생성 실패, 벡터 검색 건너뜀")
            
            # 🚨 알레르기/비선호 필터링이 있어도 모든 검색 방식 사용 (결과 확보 우선)
            has_filters = (allergies and len(allergies) > 0) or (dislikes and len(dislikes) > 0) or user_id
            if has_filters:
                print("    ⚠️ 알레르기/비선호 필터링 적용 - 모든 검색 방식 사용 (결과 확보 우선)")
            
            # 모든 검색 방식 실행 (필터링 여부와 관계없이)
            # 2. 정확한 ILIKE 매칭 (가중치 35%)
            print("    🔎 ILIKE 정확 매칭 검색...")
            ilike_exact = await self._exact_ilike_search(query, k)
            for result in ilike_exact:
                result['final_score'] = result['search_score'] * 0.35
                result['search_type'] = 'exact_ilike'
            all_results.extend(ilike_exact)
            # print(f"    ✅ ILIKE 정확 매칭 완료: {len(ilike_exact)}개")  # 임시 비활성화
            
            # 3. Full-Text Search (가중치 30%)
            print("    📝 Full-Text Search 실행...")
            fts_results = await self._full_text_search(query, k)
            for result in fts_results:
                result['final_score'] = result['search_score'] * 0.3
                result['search_type'] = 'fts'
            all_results.extend(fts_results)
            # print(f"    ✅ FTS 검색 완료: {len(fts_results)}개")  # 임시 비활성화
            
            # 4. Trigram 유사도 검색 (가중치 20%)
            print("    🔤 Trigram 검색 실행...")
            trigram_results = await self._trigram_similarity_search(query, k)
            for result in trigram_results:
                result['final_score'] = result['search_score'] * 0.2
                result['search_type'] = 'trigram'
            all_results.extend(trigram_results)
            # print(f"    ✅ Trigram 검색 완료: {len(trigram_results)}개")  # 임시 비활성화
            
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
            
            # 최종 점수로 정렬 + 다양성을 위한 랜덤 요소 추가
            unique_results.sort(key=lambda x: x['final_score'], reverse=True)
            
            # 🎯 아침 식사에만 특별 로직 적용: 계란 포함/제외 분리 후 랜덤 선택
            # 아침 키워드 체크
            breakfast_keywords = ['아침', '브렉퍼스트', '모닝', 'breakfast', 'morning']
            is_breakfast_query = any(keyword in query.lower() for keyword in breakfast_keywords)
            
            if is_breakfast_query:
                print(f"    🌅 아침 식사 감지 - 특별 다양성 로직 적용")
                
                egg_recipes = []
                non_egg_recipes = []
                
                # 계란 관련 키워드 (동의어 포함)
                egg_keywords = ['계란', 'egg', '달걀', '계란프라이', '스크램블', '오믈렛', '에그']
                
                for result in unique_results:
                    title = result.get('title', '').lower()
                    content = result.get('content', '').lower()
                    
                    # 계란 포함 여부 체크
                    is_egg = any(keyword in title or keyword in content for keyword in egg_keywords)
                    
                    if is_egg:
                        egg_recipes.append(result)
                    else:
                        non_egg_recipes.append(result)
                
                print(f"    🔍 계란 포함 레시피: {len(egg_recipes)}개")
                print(f"    🔍 계란 제외 레시피: {len(non_egg_recipes)}개")
                
                # 다양성 확보: 계란 1개 + 비계란 2개 (총 3개)
                import random
                selected_results = []
                
                # 계란 레시피 1개 선택 (있으면)
                if egg_recipes:
                    selected_egg = random.choice(egg_recipes)
                    selected_results.append(selected_egg)
                    print(f"    ✅ 계란 레시피 선택: {selected_egg.get('title')}")
                
                # 비계란 레시피 2개 선택 (부족하면 가능한 만큼)
                non_egg_count = min(2, len(non_egg_recipes))
                if non_egg_count > 0:
                    selected_non_egg = random.sample(non_egg_recipes, non_egg_count)
                    selected_results.extend(selected_non_egg)
                    print(f"    ✅ 비계란 레시피 선택: {[r.get('title') for r in selected_non_egg]}")
                
                # 결과가 부족하면 나머지 추가
                if len(selected_results) < 3 and len(unique_results) > len(selected_results):
                    remaining = [r for r in unique_results if r not in selected_results]
                    needed = 3 - len(selected_results)
                    selected_results.extend(remaining[:needed])
                    print(f"    ✅ 추가 레시피 선택: {[r.get('title') for r in remaining[:needed]]}")
                
                print(f"    ✅ 최종 선택된 레시피: {len(selected_results)}개")
                
                filtered_results = selected_results
            else:
                print(f"    🍽️ 일반 식사 - 기존 다양성 로직 적용")
                
                # 기존 다양성 필터링 로직 (아침이 아닌 경우)
                filtered_results = []
                seen_ingredients = set()
                seen_categories = set()
                seen_proteins = set()
                
                for result in unique_results:
                    title = result.get('title', '').lower()
                    content = result.get('content', '').lower()
                    
                    # 배추류 중복 체크
                    cabbage_keywords = ['양배추', '알배추', '배추', 'cabbage']
                    is_cabbage = any(keyword in title or keyword in content for keyword in cabbage_keywords)
                    if is_cabbage and '배추류' in seen_ingredients:
                        print(f"    ⚠️ 배추류 중복 제외: {result.get('title')}")
                        continue
                    if is_cabbage:
                        seen_ingredients.add('배추류')
                    
                    # 계란 중복 체크 (일반적인 경우)
                    egg_keywords = ['계란', 'egg', '달걀', '계란프라이', '스크램블', '오믈렛', '에그']
                    is_egg = any(keyword in title or keyword in content for keyword in egg_keywords)
                    if is_egg and '계란' in seen_ingredients:
                        print(f"    ⚠️ 계란 중복 제외: {result.get('title')}")
                        continue
                    if is_egg:
                        seen_ingredients.add('계란')
                    
                    # 김밥 중복 체크
                    if '김밥' in title or 'gimbap' in title:
                        if '김밥' in seen_categories:
                            print(f"    ⚠️ 김밥 중복 제외: {result.get('title')}")
                            continue
                        seen_categories.add('김밥')
                    
                    # 단백질원 중복 체크
                    protein_keywords = ['닭고기', '소고기', '돼지고기', '연어', '새우', '참치', '베이컨', '치즈']
                    for protein in protein_keywords:
                        if protein in title or protein in content:
                            if protein in seen_proteins:
                                print(f"    ⚠️ 단백질원 중복 제외: {result.get('title')} (단백질원: {protein})")
                                continue
                            seen_proteins.add(protein)
                            break
                    
                    filtered_results.append(result)
                    
                    # 다양성 확보를 위해 최대 3개로 제한
                    if len(filtered_results) >= 3:
                        print(f"    ✅ 다양성 확보: {len(filtered_results)}개 결과로 제한")
                        break
            
            # 다양성 확보: 상위 결과에서 랜덤하게 선택
            if len(filtered_results) > k:
                # 상위 70%에서 랜덤 선택
                top_count = max(k, int(len(filtered_results) * 0.7))
                top_results = filtered_results[:top_count]
                final_results = random.sample(top_results, k)
                print(f"  🎲 다양성 확보: 상위 {top_count}개에서 {k}개 랜덤 선택")
            else:
                final_results = filtered_results[:k]
            
            # URL 보완: RPC 함수가 url을 반환하지 않는 경우 직접 조회
            for result in final_results:
                recipe_id = result.get('id')
                if not result.get('url') and recipe_id:
                    try:
                        recipe_info = self.supabase.table('recipe_blob_emb').select('url').eq('id', recipe_id).execute()
                        if recipe_info.data and len(recipe_info.data) > 0:
                            result['url'] = recipe_info.data[0].get('url')
                            if result.get('url'):
                                print(f"  📎 {result.get('title')} URL 보완: {result['url']}")
                    except Exception as e:
                        print(f"  ⚠️ URL 조회 실패 ({recipe_id}): {e}")
            
            # 검색 전략과 메시지 추가
            for result in final_results:
                result['search_strategy'] = search_strategy
                result['search_message'] = search_message
            
            print(f"  ✅ 최종 결과: {len(final_results)}개 (전략: {search_strategy})")
            print(f"  💬 {search_message}")
            
            # 결과 요약 출력
            for i, result in enumerate(final_results[:3], 1):
                print(f"    {i}. {result['title']} (점수: {result['final_score']:.3f}, 타입: {result['search_type']})")
            
            # 검색 결과 캐시 저장 (Redis 우선, 메모리 폴백)
            # Redis에 저장 (TTL: 1시간)
            redis_cache.set(cache_key, final_results, ttl=3600)
            
            # 메모리 캐시에도 저장 (폴백용)
            self._search_results_cache[cache_key] = final_results
            self._manage_cache_size(self._search_results_cache)
            print(f"    📊 검색 결과 캐시 저장 (Redis + 메모리): {query[:30]}...")
            
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
                # 아침 키워드별로 랜덤하게 하나씩 선택
                import random
                breakfast_keywords = ["오믈렛", "샐러드", "요거트", "베이컨", "아보카도", "연어", "닭가슴살", "소고기"]
                selected_keywords = random.sample(breakfast_keywords, min(3, len(breakfast_keywords)))
                adjusted_query = f"{query} {' '.join(selected_keywords)}"
                print(f"  🎲 아침 키워드 랜덤 선택: {selected_keywords}")
            elif any(k in query for k in ["점심", "런치", "lunch"]):
                meal_hint = '점심'
                adjusted_query = f"{query} 샐러드 스테이크 볶음 구이"
            elif any(k in query for k in ["저녁", "디너", "dinner"]):
                meal_hint = '저녁'
                adjusted_query = f"{query} 스테이크 구이 찜 볶음"

            # 스마트 하이브리드 검색 실행(강화 쿼리 우선)
            print(f"  🔍 확장된 쿼리로 검색: '{adjusted_query}'")
            results = await self.korean_hybrid_search(adjusted_query, max_results)
            if not results and adjusted_query != query:
                print(f"  🔍 원본 쿼리로 재검색: '{query}'")
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
                
                # blob 데이터 디버깅
                blob_data = result.get('blob', '')
                print(f"    🔍 검색 결과 blob 확인: {result.get('title', '제목없음')}")
                print(f"    🔍 blob 존재: {bool(blob_data)}")
                print(f"    🔍 blob 길이: {len(str(blob_data))}")
                if blob_data:
                    print(f"    🔍 blob 내용: {str(blob_data)[:100]}...")
                
                formatted_results.append({
                    'id': result.get('id', ''),
                    'title': result.get('title', '제목 없음'),
                    'content': result.get('content', ''),
                    'blob': result.get('blob', ''),  # blob 데이터 추가
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
