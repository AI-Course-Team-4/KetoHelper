#!/usr/bin/env python3
"""
Enhanced Blob Approach - Supabase 구현
더 풍부한 콘텐츠로 임베딩하여 검색 정확도 향상
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# .env 파일 로드
load_dotenv('../.env')

class EnhancedBlobApproachSupabase:
    """Enhanced Blob 방식 - 더 풍부한 콘텐츠로 임베딩"""

    def __init__(self):
        self.approach_name = "enhanced_blob"
        self.table_name = "recipes_enhanced_blob"
        
        # OpenAI 클라이언트 설정
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_model = 'text-embedding-3-small'
        self.embedding_dimension = 1536

        # Supabase 클라이언트 설정
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL과 SUPABASE_ANON_KEY 환경변수가 필요합니다.")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    def normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        if not text:
            return ""

        # 기본 정규화
        text = text.strip()
        text = ' '.join(text.split())  # 여러 공백을 하나로

        # 특수문자 정리
        replacements = {
            '·': ' ', '∙': ' ', '※': '', '★': '', '♥': '', '♡': '',
            '[': '', ']': '', '(': '', ')': '', '{': '', '}': '',
            '!': '', '?': '', '~': '', '`': '', '"': '', "'": ''
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text.strip()

    def _llm_enhance_content(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """LLM을 사용하여 콘텐츠 강화 및 정규화"""
        try:
            # 원본 데이터 수집
            title = recipe.get('title', '')
            description = recipe.get('summary', '')
            tags = recipe.get('tags', [])
            ingredients = recipe.get('ingredients', [])
            
            # 태그 정규화
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            
            # 재료 정보 정규화
            ingredients_text = ""
            if isinstance(ingredients, list):
                ingredients_text = ", ".join([str(ing) for ing in ingredients])
            elif isinstance(ingredients, str):
                ingredients_text = ingredients

            # LLM 프롬프트 생성
            prompt = f"""
다음 레시피 정보를 분석하여 구조화된 콘텐츠를 생성해주세요:

제목: {title}
설명: {description}
태그: {tags}
재료: {ingredients_text}

다음 형식으로 구조화해주세요:
1. 요리 종류 (한식, 중식, 일식, 양식, 기타)
2. 요리 방법 (굽기, 끓이기, 볶기, 튀기기, 찜, 기타)
3. 음식 카테고리 (메인요리, 간식, 디저트, 음료, 기타)
4. 맛 프로필 (달콤함, 매움, 담백함, 짠맛, 신맛, 기타)
5. 영양 특성 (고단백, 저탄수, 저칼로리, 고섬유, 기타)
6. 정규화된 제목 (마케팅 단어 제거)
7. 정규화된 설명 (핵심 내용만)
8. 정규화된 재료 (주요 재료만)
9. 정규화된 태그 (핵심 키워드만)

JSON 형식으로 응답해주세요:
{{
    "cuisine_type": "요리 종류",
    "cooking_method": "요리 방법", 
    "dish_category": "음식 카테고리",
    "flavor_profile": "맛 프로필",
    "nutrition_type": "영양 특성",
    "normalized_title": "정규화된 제목",
    "normalized_description": "정규화된 설명",
    "normalized_ingredients": ["정규화된", "재료", "목록"],
    "normalized_tags": ["정규화된", "태그", "목록"]
}}
"""

            # LLM 호출
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 레시피를 분석하여 구조화된 콘텐츠를 생성하는 전문가입니다. 마케팅 단어를 제거하고 핵심 정보만 추출해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            # 응답 파싱
            llm_result = response.choices[0].message.content
            
            # JSON 파싱 시도
            try:
                enhanced_data = json.loads(llm_result)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본값 사용
                enhanced_data = {
                    "cuisine_type": "기타",
                    "cooking_method": "기타",
                    "dish_category": "기타",
                    "flavor_profile": "기타",
                    "nutrition_type": "기타",
                    "normalized_title": self.normalize_text(title),
                    "normalized_description": self.normalize_text(description),
                    "normalized_ingredients": [self.normalize_text(ing) for ing in ingredients[:5]] if isinstance(ingredients, list) else [],
                    "normalized_tags": [self.normalize_text(tag) for tag in tags[:5]] if isinstance(tags, list) else []
                }

            # 약간의 딜레이 (API 제한 고려)
            time.sleep(0.1)
            
            return enhanced_data

        except Exception as e:
            print(f"LLM 콘텐츠 강화 실패: {e}")
            # 실패 시 기본값 반환
            return {
                "cuisine_type": "기타",
                "cooking_method": "기타", 
                "dish_category": "기타",
                "flavor_profile": "기타",
                "nutrition_type": "기타",
                "normalized_title": self.normalize_text(recipe.get('title', '')),
                "normalized_description": self.normalize_text(recipe.get('summary', '')),
                "normalized_ingredients": [],
                "normalized_tags": []
            }

    def create_enhanced_blob(self, recipe: Dict[str, Any], enhanced_data: Dict[str, Any]) -> str:
        """Enhanced Blob 콘텐츠 생성"""
        blob_parts = []
        
        # 1. 요리 특성들
        characteristics = []
        if enhanced_data.get('cuisine_type'):
            characteristics.append(enhanced_data['cuisine_type'])
        if enhanced_data.get('cooking_method'):
            characteristics.append(enhanced_data['cooking_method'])
        if enhanced_data.get('dish_category'):
            characteristics.append(enhanced_data['dish_category'])
        if enhanced_data.get('flavor_profile'):
            characteristics.append(enhanced_data['flavor_profile'])
        if enhanced_data.get('nutrition_type'):
            characteristics.append(enhanced_data['nutrition_type'])
        
        if characteristics:
            blob_parts.append(" ".join(characteristics))
        
        # 2. 정규화된 제목
        if enhanced_data.get('normalized_title'):
            blob_parts.append(f"제목: {enhanced_data['normalized_title']}")
        
        # 3. 정규화된 설명
        if enhanced_data.get('normalized_description'):
            blob_parts.append(f"설명: {enhanced_data['normalized_description']}")
        
        # 4. 정규화된 재료
        if enhanced_data.get('normalized_ingredients'):
            ingredients_text = ", ".join(enhanced_data['normalized_ingredients'])
            blob_parts.append(f"주요 재료: {ingredients_text}")
        
        # 5. 정규화된 태그
        if enhanced_data.get('normalized_tags'):
            tags_text = ", ".join(enhanced_data['normalized_tags'])
            blob_parts.append(f"태그: {tags_text}")
        
        return "\n".join(blob_parts)

    def _get_openai_embedding(self, text: str) -> List[float]:
        """OpenAI text-embedding-3-small로 임베딩 생성"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI embedding error: {e}")
            return [0.0] * self.embedding_dimension

    def save_recipe_embedding(self, recipe: Dict[str, Any]) -> bool:
        """Enhanced Blob 방식용 레시피 임베딩 저장"""
        try:
            # LLM 콘텐츠 강화
            enhanced_data = self._llm_enhance_content(recipe)
            
            # Enhanced Blob 생성
            enhanced_blob = self.create_enhanced_blob(recipe, enhanced_data)
            
            # OpenAI text-embedding-3-small로 임베딩 생성
            embedding = self._get_openai_embedding(enhanced_blob)
            
            # Enhanced Blob 방식 전용 데이터 구조
            data = {
                'recipe_id': recipe.get('source_recipe_id', ''),
                'title': recipe.get('title', ''),
                'description': recipe.get('summary', ''),
                'tags': recipe.get('tags', []),
                'ingredients': recipe.get('ingredients', []),
                'cooking_method': enhanced_data.get('cooking_method', ''),
                'enhanced_blob': enhanced_blob,
                'embedding': embedding,
                'metadata': {
                    'approach': self.approach_name,
                    'blob_length': len(enhanced_blob),
                    'has_title': bool(recipe.get('title', '').strip()),
                    'ingredient_count': len(recipe.get('ingredients', [])),
                    'enhanced_data': enhanced_data
                }
            }

            result = self.supabase.table(self.table_name).upsert(data, on_conflict='recipe_id').execute()
            return True

        except Exception as e:
            print(f"Error saving recipe {recipe.get('source_recipe_id', 'unknown')}: {e}")
            return False

    def search_similar_recipes(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Enhanced Blob 방식용 유사 레시피 검색"""
        try:
            # 쿼리 임베딩 (OpenAI text-embedding-3-small)
            query_embedding = self._get_openai_embedding(query)

            # Enhanced Blob 방식 전용 검색 함수 사용
            result = self.supabase.rpc('search_enhanced_recipes', {
                'query_embedding': query_embedding,
                'match_count': top_k
            }).execute()

            if result.data:
                return result.data
            else:
                # fallback: 모든 데이터를 가져와서 클라이언트에서 계산
                return self._fallback_search(query_embedding, top_k)

        except Exception as e:
            print(f"Error in search: {e}")
            # fallback 검색
            query_embedding = self._get_openai_embedding(query)
            return self._fallback_search(query_embedding, top_k)

    def _fallback_search(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """백업 검색 방법 - 모든 데이터를 가져와서 클라이언트에서 유사도 계산"""
        try:
            import numpy as np
            result = self.supabase.table(self.table_name).select('*').execute()

            results = []
            query_embedding = np.array(query_embedding, dtype=np.float32)
            
            for row in result.data:
                embedding_data = row.get('embedding')
                if not embedding_data:
                    continue
                
                # embedding이 문자열인 경우 파싱
                if isinstance(embedding_data, str):
                    try:
                        embedding_data = json.loads(embedding_data)
                    except:
                        continue
                
                stored_embedding = np.array(embedding_data, dtype=np.float32)
                
                # 코사인 유사도 계산
                norm_query = np.linalg.norm(query_embedding)
                norm_stored = np.linalg.norm(stored_embedding)
                
                if norm_query == 0 or norm_stored == 0:
                    similarity = 0.0
                else:
                    similarity = np.dot(query_embedding, stored_embedding) / (norm_query * norm_stored)

                results.append({
                    'recipe_id': row['recipe_id'],
                    'title': row['title'],
                    'enhanced_blob': row.get('enhanced_blob', ''),
                    'metadata': row.get('metadata', {}),
                    'similarity': float(similarity)
                })

            # 유사도 기준 정렬 후 top_k 반환
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]

        except Exception as e:
            print(f"Error in fallback search: {e}")
            return []

    def load_recipes_from_supabase(self, source_table: str = "recipes_keto_raw", limit: int = 100):
        """Supabase의 기존 레시피 테이블에서 데이터 로드"""
        try:
            result = self.supabase.table(source_table).select('*').limit(limit).execute()

            processed_count = 0
            for recipe in result.data:
                # Enhanced Blob 처리 및 저장
                if self.save_recipe_embedding(recipe):
                    processed_count += 1

                if processed_count % 10 == 0:
                    print(f"Processed {processed_count} recipes...")

            print(f"Total processed: {processed_count} recipes")

        except Exception as e:
            print(f"Error loading recipes from Supabase: {e}")

if __name__ == "__main__":
    # 테스트 실행
    approach = EnhancedBlobApproachSupabase()
    print("Enhanced Blob Approach 초기화 완료")
    
    # 샘플 레시피로 테스트
    sample_recipe = {
        'source_recipe_id': 'test_001',
        'title': '키토제닉] 고소한맛 가득 아몬드 머핀 - No 설탕, No 코코아, No 밀가루',
        'summary': '아몬드 가루로 만든 고소한 머핀',
        'tags': ['키토', '다이어트', '저탄수'],
        'ingredients': ['아몬드 가루', '계란', '스테비아']
    }
    
    # 저장 테스트
    if approach.save_recipe_embedding(sample_recipe):
        print("✅ 샘플 레시피 저장 성공")
        
        # 검색 테스트
        results = approach.search_similar_recipes("아몬드 머핀", 3)
        print(f"🔍 검색 결과: {len(results)}개")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['title'][:50]}... ({result['similarity']*100:.1f}%)")
    else:
        print("❌ 샘플 레시피 저장 실패")
