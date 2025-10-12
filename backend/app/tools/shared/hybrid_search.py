"""
Supabase 하이브리드 검색 도구
벡터 검색 + 키워드 검색 + 메타데이터 필터링을 Supabase RPC로 통합
"""

import re
# OpenAI import (임베딩용으로 유지)
import openai
import asyncio
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.core.config import settings
from app.tools.shared.profile_tool import user_profile_tool

class HybridSearchTool:
    """Supabase 하이브리드 검색 도구 클래스"""
    
    def __init__(self):
        self.supabase = supabase
        # OpenAI 클라이언트 (임베딩용으로 유지)
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        # 알레르기/비선호 임베딩 캐시
        self._allergy_cache = {}
        self._dislike_cache = {}
    
    async def _create_embedding(self, text: str) -> List[float]:
        """텍스트를 임베딩으로 변환"""
        try:
            print(f"📊 임베딩 생성 중: {text[:50]}...")
            response = self.openai_client.embeddings.create(
                model=settings.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding
            print(f"✅ 임베딩 생성 완료: {len(embedding)}차원")
            return embedding
        except Exception as e:
            print(f"❌ 임베딩 생성 오류: {e}")
            return []
    
    def _extract_meal_type(self, query: str) -> Optional[str]:
        """쿼리에서 meal_type 추출"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['아침', 'morning', 'breakfast', '브런치']):
            return '아침'
        elif any(word in query_lower for word in ['점심', 'lunch', '런치']):
            return '점심'
        elif any(word in query_lower for word in ['저녁', 'dinner', '디너', '이브닝']):
            return '저녁'
        elif any(word in query_lower for word in ['간식', 'snack', '스낵', '애프터눈']):
            return '간식'
        
        return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """코사인 유사도 계산"""
        try:
            import numpy as np
            
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            print(f"❌ 코사인 유사도 계산 오류: {e}")
            return 0.0
    
    def _extract_keywords(self, query: str) -> List[str]:
        """쿼리에서 키워드 추출"""
        # 한글, 영문, 숫자만 추출
        keywords = re.findall(r'[가-힣a-zA-Z0-9]+', query)
        # 2글자 이상만 필터링
        keywords = [kw for kw in keywords if len(kw) >= 2]
        return keywords
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """중복 결과 제거"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        return unique_results
    
    async def _supabase_hybrid_search(self, query: str, query_embedding: List[float], k: int) -> List[Dict]:
        """Supabase RPC 하이브리드 검색"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []
            
            # Supabase RPC 함수 호출
            results = self.supabase.rpc('hybrid_search', {
                'query_text': query,
                'query_embedding': query_embedding,
                'match_count': k
            }).execute()
            
            if results.data:
                print(f"✅ Supabase 하이브리드 검색 성공: {len(results.data)}개")
                return results.data
            else:
                print("⚠️ Supabase 하이브리드 검색 결과 없음")
                return []
                
        except Exception as e:
            print(f"Supabase 하이브리드 검색 오류: {e}")
            return []
    
    async def _fallback_keyword_search(self, query: str, k: int) -> List[Dict]:
        """폴백 키워드 검색 (RPC 실패 시)"""
        try:
            if isinstance(self.supabase, type(None)) or hasattr(self.supabase, '__class__') and 'DummySupabase' in str(self.supabase.__class__):
                return []
            
            keywords = self._extract_keywords(query)
            if not keywords:
                return []
            
            keyword_results = []
            
            for keyword in keywords[:3]:  # 상위 3개 키워드만 사용
                try:
                    # 제목에서 키워드 검색
                    title_results = self.supabase.table('recipe_blob_emb').select('*').ilike('title', f'%{keyword}%').limit(k).execute()
                    
                    # 내용에서 키워드 검색
                    content_results = self.supabase.table('recipe_blob_emb').select('*').ilike('content', f'%{keyword}%').limit(k).execute()
                    
                    keyword_results.extend(title_results.data or [])
                    keyword_results.extend(content_results.data or [])
                    
                except Exception as e:
                    print(f"키워드 검색 오류 for '{keyword}': {e}")
                    continue
            
            # 중복 제거
            unique_results = self._deduplicate_results(keyword_results)
            
            # 키워드 검색 결과 포맷팅
            formatted_results = []
            for result in unique_results:
                    formatted_results.append({
                        'id': str(result.get('id', '')),
                        'title': result.get('title', '제목 없음'),
                        'content': result.get('content', ''),
                        'blob': result.get('blob', ''),  # blob 데이터 추가
                        'content': result.get('content', ''),
                        'blob': result.get('blob', ''),  # blob 데이터 추가
                        'vector_score': 0.0,
                        'keyword_score': 1.0,
                        'hybrid_score': 1.0,
                        'search_type': 'keyword',
                        'url': result.get('url'),  # URL 추가
                        'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'embedding', 'url', 'blob']}
                    })
            
            return formatted_results[:k]
            
        except Exception as e:
            print(f"폴백 키워드 검색 오류: {e}")
            return []
    
    
    async def hybrid_search(self, query: str, filters: Optional[Dict] = None, k: int = 5) -> List[Dict]:
        """Supabase 하이브리드 검색"""
        try:
            print(f"🔍 Supabase 하이브리드 검색 시작: '{query}'")
            
            # 1. 임베딩 생성
            print("  📊 임베딩 생성 중...")
            query_embedding = await self._create_embedding(query)
            
            if not query_embedding:
                print("  ⚠️ 임베딩 생성 실패, 키워드 검색으로 폴백")
                return await self._fallback_keyword_search(query, k)
            
            # 2. Supabase RPC 하이브리드 검색
            print("  🔄 Supabase RPC 하이브리드 검색 실행...")
            results = await self._supabase_hybrid_search(query, query_embedding, k)
            
            if not results:
                print("  ⚠️ RPC 검색 실패, 키워드 검색으로 폴백")
                return await self._fallback_keyword_search(query, k)
            
            # 3. 결과 포맷팅 및 다양성 개선 (강화된 버전)
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
                
                for result in results:
                    title = result.get('title', '제목 없음')
                    content = result.get('content', '')
                    
                    # 계란 포함 여부 체크
                    is_egg = any(keyword in title.lower() or keyword in content.lower() for keyword in egg_keywords)
                    
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
                if len(selected_results) < 3 and len(results) > len(selected_results):
                    remaining = [r for r in results if r not in selected_results]
                    needed = 3 - len(selected_results)
                    selected_results.extend(remaining[:needed])
                    print(f"    ✅ 추가 레시피 선택: {[r.get('title') for r in remaining[:needed]]}")
                
                print(f"    ✅ 최종 선택된 레시피: {len(selected_results)}개")
                
                # 선택된 결과로 formatted_results 생성
                formatted_results = []
                for result in selected_results:
                    title = result.get('title', '제목 없음')
                    content = result.get('content', '')
                    
                    # 간단한 결과 포맷팅 (이미 다양성이 확보된 상태)
                    
                    formatted_results.append({
                        'id': str(result.get('id', '')),
                        'title': result.get('title', '제목 없음'),
                        'content': result.get('content', ''),
                        'blob': result.get('blob', ''),  # blob 데이터 추가
                        'vector_score': result.get('vector_score', 0.0),
                        'keyword_score': result.get('keyword_score', 0.0),
                        'hybrid_score': result.get('hybrid_score', 0.0),
                        'search_type': 'hybrid',
                        'url': result.get('url'),
                        'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'vector_score', 'keyword_score', 'hybrid_score', 'url', 'blob']}
                    })
            else:
                print(f"    🍽️ 일반 식사 - 기존 다양성 로직 적용")
                
                # 기존 다양성 필터링 로직 (아침이 아닌 경우)
                formatted_results = []
                seen_titles = set()
                seen_ingredients = set()
                seen_categories = set()
                seen_proteins = set()
                
                for result in results:
                    title = result.get('title', '제목 없음')
                    content = result.get('content', '')
                    
                    # 다양성 체크: 같은 제목이나 유사한 카테고리 제외
                    if title in seen_titles:
                        continue
                    
                    # 배추류 중복 체크
                    cabbage_keywords = ['양배추', '알배추', '배추', 'cabbage']
                    is_cabbage = any(keyword in title.lower() or keyword in content.lower() for keyword in cabbage_keywords)
                    if is_cabbage and '배추류' in seen_ingredients:
                        print(f"    ⚠️ 배추류 중복 제외: '{title}'")
                        continue
                    if is_cabbage:
                        seen_ingredients.add('배추류')
                    
                    # 계란 중복 체크 (일반적인 경우)
                    egg_keywords = ['계란', 'egg', '달걀', '계란프라이', '스크램블', '오믈렛', '에그']
                    is_egg = any(keyword in title.lower() or keyword in content.lower() for keyword in egg_keywords)
                    if is_egg and '계란' in seen_ingredients:
                        print(f"    ⚠️ 계란 중복 제외: '{title}'")
                        continue
                    if is_egg:
                        seen_ingredients.add('계란')
                    
                    # 김밥 중복 체크
                    if '김밥' in title.lower() or 'gimbap' in title.lower():
                        if '김밥' in seen_categories:
                            print(f"    ⚠️ 김밥 중복 제외: '{title}'")
                            continue
                        seen_categories.add('김밥')
                    
                    # 단백질원 중복 체크
                    protein_keywords = ['닭고기', '소고기', '돼지고기', '연어', '새우', '참치', '베이컨', '치즈']
                    for protein in protein_keywords:
                        if protein in title.lower() or protein in content.lower():
                            if protein in seen_proteins:
                                print(f"    ⚠️ 단백질원 중복 제외: '{title}' (단백질원: {protein})")
                                continue
                            seen_proteins.add(protein)
                            break
                    
                    formatted_results.append({
                        'id': str(result.get('id', '')),
                        'title': result.get('title', '제목 없음'),
                        'content': result.get('content', ''),
                        'blob': result.get('blob', ''),  # blob 데이터 추가
                        'vector_score': result.get('vector_score', 0.0),
                        'keyword_score': result.get('keyword_score', 0.0),
                        'hybrid_score': result.get('hybrid_score', 0.0),
                        'search_type': 'hybrid',
                        'url': result.get('url'),
                        'metadata': {k: v for k, v in result.items() if k not in ['id', 'title', 'content', 'vector_score', 'keyword_score', 'hybrid_score', 'url', 'blob']}
                    })
                    
                    # 다양성 확보를 위해 최대 3개로 제한
                    if len(formatted_results) >= 3:
                        print(f"    ✅ 다양성 확보: {len(formatted_results)}개 결과로 제한")
                        break
            
            print(f"  ✅ 최종 결과: {len(formatted_results)}개")
            
            # 결과 요약 출력
            for i, result in enumerate(formatted_results[:3], 1):
                print(f"    {i}. {result['title']} (점수: {result['hybrid_score']:.3f})")
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 하이브리드 검색 오류: {e}")
            return []
    
    async def search(self, query: str, profile: str = "", max_results: int = 5, user_id: Optional[str] = None,
                    allergies: Optional[List[str]] = None, dislikes: Optional[List[str]] = None) -> List[Dict]:
        """간단한 검색 인터페이스 (한글 최적화) + 사용자 프로필 필터링 + 임시 제약조건"""
        try:
            print(f"🔧 hybrid_search.search 호출됨: user_id={user_id}, allergies={allergies}, dislikes={dislikes}")
            # 한글 검색 최적화 도구 사용
            from app.tools.meal.korean_search import korean_search_tool

            # 프로필에서 필터 추출
            filters = {}
            if profile:
                if "아침" in profile or "morning" in profile.lower():
                    filters['category'] = '아침'
                if "쉬운" in profile or "easy" in profile.lower():
                    filters['difficulty'] = '쉬움'

            # 한글 최적화 검색 실행 (meal_type 추출)
            meal_type = self._extract_meal_type(query)
            results = await korean_search_tool.korean_hybrid_search(query, max_results, user_id, meal_type, allergies, dislikes)

            print(f"✅ RAG 벡터 검색 완료: {len(results)}개 결과 (DB 레벨 필터링 적용)")
            
            # 결과 포맷팅 (검색 전략과 메시지 포함)
            formatted_results = []
            search_strategy = "unknown"
            search_message = ""
            
            for result in results:
                # 첫 번째 결과에서 검색 전략과 메시지 추출
                if not search_message:
                    search_strategy = result.get('search_strategy', 'unknown')
                    search_message = result.get('search_message', '')
                
                # blob 데이터 디버깅
                blob_data = result.get('blob', '')
                print(f"    🔍 하이브리드 검색 blob 확인: {result.get('title', '제목없음')}")
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
                    'url': result.get('url'),  # URL 추가
                    'metadata': result.get('metadata', {}),
                    'search_types': [result.get('search_type', 'hybrid')],
                    'search_strategy': search_strategy,
                    'search_message': search_message
                })
            
            # 검색 결과가 없는 경우 메시지 추가
            if not formatted_results:
                formatted_results.append({
                    'title': '검색 결과 없음',
                    'content': '검색 결과가 없습니다. 다른 키워드를 시도해보세요.',
                    'similarity': 0.0,
                    'metadata': {'search_message': '검색 결과가 없습니다.'},
                    'search_types': ['none'],
                    'search_strategy': 'none',
                    'search_message': '검색 결과가 없습니다. 다른 키워드를 시도해보세요.'
                })
            
            # 검색 메시지 출력
            if search_message:
                print(f"💬 사용자 안내: {search_message}")
            
            return formatted_results
            
        except Exception as e:
            print(f"Search error: {e}")
            # 폴백: 기존 검색 방식 사용
            try:
                results = await self.hybrid_search(query, {}, max_results)
                
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        'id': result.get('id', ''),
                        'title': result.get('title', '제목 없음'),
                        'content': result.get('content', ''),
                        'blob': result.get('blob', ''),  # blob 데이터 추가
                        'allergens': result.get('allergens', []),
                        'ingredients': result.get('ingredients', []),
                        'similarity': result.get('hybrid_score', 0.0),
                        'url': result.get('url'),  # URL 추가
                        'metadata': result.get('metadata', {}),
                        'search_types': [result.get('search_type', 'hybrid')]
                    })
                
                return formatted_results
            except Exception as fallback_error:
                print(f"Fallback search error: {fallback_error}")
                return []

# 전역 하이브리드 검색 도구 인스턴스
hybrid_search_tool = HybridSearchTool()
