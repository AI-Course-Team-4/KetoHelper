#!/usr/bin/env python3
"""
하이브리드 검색 엔진 - 키워드 + 벡터 + 하드필터
"""

import sys
sys.path.append('src')

from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from typing import List, Dict, Optional, Tuple
import numpy as np
from openai import AsyncOpenAI
import os
import asyncio
from synonym_dictionary import expand_query_with_synonyms, normalize_query
from query_preprocessor import preprocess_for_keyword_search, preprocess_for_vector_search

# Supabase 클라이언트 초기화
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# OpenAI 클라이언트 초기화
openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class HybridSearchEngine:
    """하이브리드 검색 엔진 클래스"""
    
    def __init__(self):
        self.supabase = supabase
        self.openai_client = openai_client
    
    def apply_hard_filter(self, recipes: List[Dict], disliked_ingredients: List[str] = None, allergies: List[str] = None) -> List[Dict]:
        """하드필터 적용"""
        if not disliked_ingredients and not allergies:
            return recipes
        
        excluded_ingredients = (disliked_ingredients or []) + (allergies or [])
        filtered_recipes = []
        
        for recipe in recipes:
            ingredients = recipe.get('ingredients', [])
            has_excluded = False
            
            for ingredient in ingredients:
                if isinstance(ingredient, dict):
                    ingredient_name = ingredient.get('name', '').lower()
                    
                    for excluded in excluded_ingredients:
                        if excluded.lower() in ingredient_name:
                            has_excluded = True
                            break
                    
                    if has_excluded:
                        break
            
            if not has_excluded:
                filtered_recipes.append(recipe)
        
        return filtered_recipes
    
    def keyword_search(self, query: str, recipes: List[Dict], limit: int = 10) -> List[Tuple[Dict, float]]:
        """키워드 검색 (search_blob 기반) - 쿼리 전처리 + 동의어 확장"""
        # 쿼리 전처리 (불용어 제거, 핵심 키워드 추출, 동의어 확장)
        processed_query = preprocess_for_keyword_search(query)
        query_terms = processed_query.lower().split()
        
        scored_recipes = []
        
        for recipe in recipes:
            search_blob = recipe.get('search_blob', '').lower()
            title = recipe.get('title', '').lower()
            
            # 동의어 확장된 키워드 매칭 점수 계산
            score = 0
            
            # 각 쿼리 용어에 대해 점수 계산
            for term in query_terms:
                # 제목에서 매칭 (높은 가중치)
                if term in title:
                    score += 3
                
                # search_blob에서 매칭 (기본 가중치)
                if term in search_blob:
                    score += 1
            
            if score > 0:
                scored_recipes.append((recipe, score))
        
        # 점수순 정렬
        scored_recipes.sort(key=lambda x: x[1], reverse=True)
        return scored_recipes[:limit]
    
    async def vector_search(self, query: str, recipes: List[Dict], limit: int = 10) -> List[Tuple[Dict, float]]:
        """벡터 검색 (임베딩 기반) - 쿼리 전처리 포함"""
        try:
            # 쿼리 전처리 (벡터 검색용 - 간결하게)
            processed_query = preprocess_for_vector_search(query)
            print(f"   🔄 쿼리 임베딩 생성 중: '{processed_query}' (원본: '{query}')")
            # 전처리된 쿼리로 임베딩 생성
            query_embedding = await self.generate_embedding(processed_query)
            if not query_embedding:
                print(f"   ❌ 쿼리 임베딩 생성 실패")
                return []
            
            print(f"   ✅ 쿼리 임베딩 생성 완료 (차원: {len(query_embedding)})")
            scored_recipes = []
            
            for recipe in recipes:
                recipe_embedding = recipe.get('embedding')
                if not recipe_embedding:
                    continue
                
                # 코사인 유사도 계산
                similarity = self.cosine_similarity(query_embedding, recipe_embedding)
                scored_recipes.append((recipe, similarity))
            
            print(f"   📊 {len(scored_recipes)}개 레시피 유사도 계산 완료")
            # 유사도순 정렬
            scored_recipes.sort(key=lambda x: x[1], reverse=True)
            return scored_recipes[:limit]
            
        except Exception as e:
            print(f"❌ 벡터 검색 실패: {str(e)}")
            return []
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """OpenAI API로 임베딩 생성"""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ 임베딩 생성 실패: {str(e)}")
            return None
    
    def cosine_similarity(self, vec1: List[float], vec2) -> float:
        """코사인 유사도 계산"""
        try:
            # vec2가 문자열인 경우 파싱
            if isinstance(vec2, str):
                # PostgreSQL 배열 형태의 문자열을 파싱
                vec2_str = vec2.strip('[]')
                vec2 = [float(x.strip()) for x in vec2_str.split(',') if x.strip()]
            
            # 벡터를 numpy 배열로 변환
            a = np.array(vec1, dtype=float)
            b = np.array(vec2, dtype=float)
            
            # 코사인 유사도 계산
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0
            
            return dot_product / (norm_a * norm_b)
        except Exception as e:
            print(f"❌ 코사인 유사도 계산 실패: {str(e)}")
            return 0
    
    async def hybrid_search(
        self,
        query: str,
        disliked_ingredients: List[str] = None,
        allergies: List[str] = None,
        search_type: str = "hybrid",  # "keyword", "vector", "hybrid"
        limit: int = 10
    ) -> List[Dict]:
        """
        하이브리드 검색
        
        Args:
            query: 검색 쿼리
            disliked_ingredients: 비선호 식재료
            allergies: 알러지 식재료
            search_type: 검색 타입
            limit: 결과 수
            
        Returns:
            검색 결과 레시피 리스트
        """
        print(f"🔍 하이브리드 검색 시작: '{query}'")
        print(f"   - 검색 타입: {search_type}")
        print(f"   - 비선호 식재료: {disliked_ingredients or []}")
        print(f"   - 알러지 식재료: {allergies or []}")
        
        # 1. 기본 데이터 로드 (임베딩이 있는 레시피만)
        try:
            response = self.supabase.table('recipes_keto_raw').select('*').not_.is_('embedding', 'null').execute()
            all_recipes = response.data if response.data else []
            print(f"   - 전체 레시피: {len(all_recipes)}개")
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {str(e)}")
            return []
        
        # 2. 하드필터 적용
        filtered_recipes = self.apply_hard_filter(all_recipes, disliked_ingredients, allergies)
        print(f"   - 하드필터 후: {len(filtered_recipes)}개")
        
        if not filtered_recipes:
            print("   ⚠️ 하드필터 후 레시피가 없습니다.")
            return []
        
        # 3. 검색 타입에 따른 검색 실행
        if search_type == "keyword":
            scored_results = self.keyword_search(query, filtered_recipes, limit)
            results = []
            # 키워드 점수 정규화 (최대 점수 기준)
            max_keyword_score = max([score for _, score in scored_results]) if scored_results else 1
            for recipe, score in scored_results:
                normalized_score = score / max_keyword_score if max_keyword_score > 0 else 0
                recipe['_search_scores'] = {'keyword': normalized_score, 'vector': 0, 'hybrid': normalized_score}
                results.append(recipe)
            
        elif search_type == "vector":
            scored_results = await self.vector_search(query, filtered_recipes, limit)
            results = []
            # 벡터 점수는 이미 0-1 범위이므로 그대로 사용
            for recipe, score in scored_results:
                recipe['_search_scores'] = {'keyword': 0, 'vector': score, 'hybrid': score}
                results.append(recipe)
            
        elif search_type == "hybrid":
            # 키워드 검색
            keyword_results = self.keyword_search(query, filtered_recipes, limit * 2)
            # 벡터 검색
            vector_results = await self.vector_search(query, filtered_recipes, limit * 2)
            
            # 키워드 점수 정규화
            max_keyword_score = max([score for _, score in keyword_results]) if keyword_results else 1
            normalized_keyword_scores = {recipe['id']: score / max_keyword_score if max_keyword_score > 0 else 0 
                                       for recipe, score in keyword_results}
            
            # 벡터 점수는 이미 0-1 범위
            vector_scores = {recipe['id']: score for recipe, score in vector_results}
            
            # 하이브리드 점수 계산 (키워드 60%, 벡터 40%)
            hybrid_scores = {}
            for recipe_id in set(normalized_keyword_scores.keys()) | set(vector_scores.keys()):
                keyword_score = normalized_keyword_scores.get(recipe_id, 0)
                vector_score = vector_scores.get(recipe_id, 0)
                hybrid_scores[recipe_id] = keyword_score * 0.6 + vector_score * 0.4
            
            # 하이브리드 점수순 정렬
            all_recipes = {recipe['id']: recipe for recipe, _ in keyword_results + vector_results}
            sorted_recipe_ids = sorted(hybrid_scores.keys(), key=lambda x: hybrid_scores[x], reverse=True)
            
            # 결과 생성
            results = []
            for recipe_id in sorted_recipe_ids[:limit]:
                recipe = all_recipes[recipe_id]
                recipe['_search_scores'] = {
                    'hybrid': hybrid_scores[recipe_id],
                    'keyword': normalized_keyword_scores.get(recipe_id, 0),
                    'vector': vector_scores.get(recipe_id, 0)
                }
                results.append(recipe)
        
        else:
            print(f"❌ 잘못된 검색 타입: {search_type}")
            return []
        
        print(f"✅ 검색 완료: {len(results)}개 레시피 발견")
        return results[:limit]

async def test_hybrid_search():
    """하이브리드 검색 테스트"""
    print("🧪 하이브리드 검색 테스트 시작")
    
    search_engine = HybridSearchEngine()
    
    # 테스트 케이스 1: 키워드 검색
    print("\n📋 테스트 1: 키워드 검색 - '김밥'")
    results1 = await search_engine.hybrid_search("김밥", search_type="keyword", limit=3)
    for i, recipe in enumerate(results1, 1):
        print(f"   [{i}] {recipe.get('title', 'Unknown')[:50]}...")
    
    # 테스트 이스 2: 벡터 검색
    print("\n📋 테스트 2: 벡터 검색 - '간단한 달걀 요리'")
    results2 = await search_engine.hybrid_search("간단한 달걀 요리", search_type="vector", limit=3)
    for i, recipe in enumerate(results2, 1):
        print(f"   [{i}] {recipe.get('title', 'Unknown')[:50]}...")
    
    # 테스트 케이스 3: 하이브리드 검색
    print("\n📋 테스트 3: 하이브리드 검색 - '달콤한 디저트'")
    results3 = await search_engine.hybrid_search("달콤한 디저트", search_type="hybrid", limit=3)
    for i, recipe in enumerate(results3, 1):
        print(f"   [{i}] {recipe.get('title', 'Unknown')[:50]}...")
    
    # 테스트 케이스 4: 하드필터 + 하이브리드 검색
    print("\n📋 테스트 4: 하드필터 + 하이브리드 검색 - '김밥' (마늘 제외)")
    results4 = await search_engine.hybrid_search(
        "김밥", 
        disliked_ingredients=['마늘'],
        search_type="hybrid", 
        limit=3
    )
    for i, recipe in enumerate(results4, 1):
        print(f"   [{i}] {recipe.get('title', 'Unknown')[:50]}...")

if __name__ == "__main__":
    asyncio.run(test_hybrid_search())
