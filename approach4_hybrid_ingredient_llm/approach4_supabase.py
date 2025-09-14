#!/usr/bin/env python3
"""
Approach 4: 하이브리드 식재료 LLM 전처리
방식2의 비용 효율성 + 방식3의 LLM 전처리 능력 결합
"""

import os
import json
import time
import numpy as np
from typing import Dict, Any, List
from dotenv import load_dotenv

from shared.supabase_config import BaseEmbeddingApproachSupabase

# 환경변수 로드
load_dotenv('../.env')

class HybridIngredientLLMApproachSupabase(BaseEmbeddingApproachSupabase):
    """하이브리드 식재료 LLM 전처리 방식"""
    
    def __init__(self):
        super().__init__("hybrid_ingredient_llm")
        
    def preprocess_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """하이브리드 전처리 - 식재료는 LLM, 나머지는 방식2"""
        
        # 1. 기본 정보 전처리 (방식2 방식)
        basic_processed = self._basic_preprocess(recipe)
        
        # 2. 식재료 LLM 전처리
        llm_processed = self._llm_preprocess_ingredients(recipe)
        
        # 3. 결합
        return {
            'basic_info': basic_processed,
            'llm_metadata': llm_processed,
            'combined_blob': self._create_hybrid_blob(basic_processed, llm_processed)
        }
    
    def _basic_preprocess(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """기본 정보 전처리 (방식2 방식)"""
        # 제목 정규화
        title = self.normalize_text(recipe.get('title', ''))
        
        # 설명 정규화
        summary = self.normalize_text(recipe.get('summary', ''))
        
        # 태그 정규화
        tags = []
        tags_data = recipe.get('tags', [])
        if isinstance(tags_data, str):
            try:
                tags_data = json.loads(tags_data)
            except:
                tags_data = []
        
        for tag in tags_data:
            normalized_tag = self.normalize_text(str(tag))
            if normalized_tag:
                tags.append(normalized_tag)
        
        # 메타 정보
        meta_info = {
            'servings': recipe.get('servings', ''),
            'cook_time': recipe.get('cook_time', ''),
            'difficulty': recipe.get('difficulty', ''),
            'author': recipe.get('author', ''),
            'rating': recipe.get('rating', ''),
            'views': recipe.get('views', '')
        }
        
        return {
            'title': title,
            'summary': summary,
            'tags': tags,
            'meta_info': meta_info
        }
    
    def _llm_preprocess_ingredients(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """식재료 LLM 전처리"""
        try:
            # 식재료 추출
            ingredients_str = self._extract_ingredients_string(recipe)
            
            if not ingredients_str.strip():
                return self._fallback_ingredient_analysis(recipe)
            
            # LLM 프롬프트 생성
            prompt = self._create_ingredient_analysis_prompt(ingredients_str)
            
            # LLM 호출
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 식재료를 분석하여 요리 특성을 추론하는 전문가입니다. 주어진 식재료만으로 요리의 특성을 정확히 분석해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            # 응답 파싱
            llm_result = response.choices[0].message.content
            processed_data = self._parse_ingredient_analysis(llm_result)
            
            # 약간의 딜레이 (API 제한 고려)
            time.sleep(0.1)
            
            return processed_data
            
        except Exception as e:
            print(f"Ingredient LLM preprocessing failed: {e}")
            return self._fallback_ingredient_analysis(recipe)
    
    def _extract_ingredients_string(self, recipe: Dict[str, Any]) -> str:
        """식재료 문자열 추출"""
        ingredients_data = recipe.get('ingredients', [])
        if isinstance(ingredients_data, str):
            try:
                ingredients_data = json.loads(ingredients_data)
            except:
                ingredients_data = []
        
        ingredients_list = []
        for ing in ingredients_data:
            if isinstance(ing, dict):
                name = ing.get('name', '')
                amount = ing.get('amount', '')
                if name:
                    ingredients_list.append(f"{name} {amount}".strip())
            else:
                ingredients_list.append(str(ing))
        
        return ", ".join(ingredients_list)
    
    def _create_ingredient_analysis_prompt(self, ingredients_str: str) -> str:
        """식재료 분석 프롬프트 생성"""
        prompt = f"""
다음 식재료 목록을 분석하여 요리의 특성을 추론해주세요:

식재료: {ingredients_str}

다음과 같은 JSON 형식으로 반환해주세요:
{{
    "cuisine_type": "요리 종류 (예: 한식, 양식, 중식, 일식, 기타)",
    "cooking_method": "주요 조리방법 (예: 볶음, 끓임, 굽기, 튀김, 찜, 샐러드, 기타)",
    "dish_category": "음식 분류 (예: 메인요리, 반찬, 디저트, 간식, 국물요리, 기타)",
    "flavor_profile": "맛 특징 (예: 달콤함, 매움, 담백함, 짠맛, 신맛, 기타)",
    "nutrition_type": "영양 특성 (예: 고단백, 저탄수, 고칼로리, 저칼로리, 고섬유, 기타)",
    "meal_time": "식사 시간 (예: 아침, 점심, 저녁, 간식, 기타)",
    "key_ingredients": ["주요 재료1", "주요 재료2", "주요 재료3"],
    "ingredient_categories": ["단백질", "탄수화물", "지방", "채소", "조미료", "기타"],
    "dietary_tags": ["키토", "다이어트", "저탄수", "고단백", "비건", "기타"],
    "keywords": ["검색 키워드1", "키워드2", "키워드3"]
}}

불필요한 설명 없이 JSON만 반환해주세요.
"""
        return prompt
    
    def _parse_ingredient_analysis(self, llm_response: str) -> Dict[str, Any]:
        """LLM 식재료 분석 응답 파싱"""
        try:
            # JSON 부분만 추출
            start_idx = llm_response.find('{')
            end_idx = llm_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = llm_response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            return self._fallback_ingredient_analysis({})
    
    def _fallback_ingredient_analysis(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 실패 시 기본 분석"""
        # 식재료에서 기본 정보 추출
        ingredients_str = self._extract_ingredients_string(recipe)
        ingredients_list = [ing.strip() for ing in ingredients_str.split(',') if ing.strip()]
        
        return {
            'cuisine_type': '기타',
            'cooking_method': '기타',
            'dish_category': '기타',
            'flavor_profile': '기타',
            'nutrition_type': '기타',
            'meal_time': '기타',
            'key_ingredients': ingredients_list[:5],
            'ingredient_categories': ['기타'],
            'dietary_tags': ['기타'],
            'keywords': ingredients_list[:3]
        }
    
    def _create_hybrid_blob(self, basic_info: Dict[str, Any], llm_metadata: Dict[str, Any]) -> str:
        """자연어 형태의 하이브리드 blob 생성"""
        blob_parts = []
        
        # 1. 요리 특성들을 자연어로 연결
        characteristics = []
        if llm_metadata.get('cuisine_type'):
            characteristics.append(llm_metadata['cuisine_type'])
        if llm_metadata.get('cooking_method'):
            characteristics.append(llm_metadata['cooking_method'])
        if llm_metadata.get('dish_category'):
            characteristics.append(llm_metadata['dish_category'])
        if llm_metadata.get('flavor_profile'):
            # 맛을 자연어로 변환
            flavor = llm_metadata['flavor_profile']
            if flavor == '담백함':
                characteristics.append('담백한')
            elif flavor == '달콤함':
                characteristics.append('달콤한')
            elif flavor == '매움':
                characteristics.append('매운')
            else:
                characteristics.append(f'{flavor}한')
            characteristics.append('맛')
        
        if llm_metadata.get('nutrition_type'):
            characteristics.append(llm_metadata['nutrition_type'])
        
        if characteristics:
            blob_parts.append(" ".join(characteristics))
        
        # 2. 주요 재료 (자연어 형태)
        if llm_metadata.get('key_ingredients'):
            ingredients_text = ", ".join(llm_metadata['key_ingredients'])
            blob_parts.append(f"주요 재료: {ingredients_text}")
        
        # 3. 설명
        if basic_info.get('summary'):
            blob_parts.append(f"설명: {basic_info['summary']}")
        
        return "\n".join(blob_parts)
    
    def create_blob_content(self, recipe: Dict[str, Any], processed_content: Dict[str, Any]) -> str:
        """최종 blob 콘텐츠 생성"""
        return processed_content.get('combined_blob', '')
    
    def save_recipe_embedding(self, recipe: Dict[str, Any]) -> bool:
        """하이브리드 방식용 레시피 임베딩 저장"""
        try:
            # 전처리
            processed_content = self.preprocess_recipe(recipe)

            # blob 콘텐츠 생성
            blob_content = self.create_blob_content(recipe, processed_content)

            # OpenAI text-embedding-3-small로 임베딩 생성
            embedding = self._get_openai_embedding(blob_content)

            # 하이브리드 방식 전용 데이터 구조
            data = {
                'recipe_id': recipe.get('source_recipe_id', ''),
                'title': recipe.get('title', ''),
                'raw_ingredients': recipe.get('ingredients', []),
                'normalized_ingredients': processed_content['llm_metadata'].get('key_ingredients', []),
                'llm_metadata': processed_content['llm_metadata'],
                'basic_metadata': processed_content['basic_info'],
                'structured_blob': blob_content,
                'embedding': embedding,
                'metadata': {
                    'approach': self.approach_name,
                    'blob_length': len(blob_content),
                    'has_title': bool(recipe.get('title', '').strip()),
                    'ingredient_count': len(recipe.get('ingredients', [])),
                    'llm_analysis_success': bool(processed_content['llm_metadata'].get('cuisine_type'))
                }
            }

            result = self.supabase.table(self.table_name).upsert(data, on_conflict='recipe_id').execute()

            return True

        except Exception as e:
            print(f"Error saving recipe {recipe.get('source_recipe_id', 'unknown')}: {e}")
            return False
    
    def search_similar_recipes(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """하이브리드 방식용 유사 레시피 검색"""
        try:
            # 쿼리 임베딩 (OpenAI text-embedding-3-small)
            query_embedding = self._get_openai_embedding(query)

            # 하이브리드 방식 전용 검색 함수 사용
            result = self.supabase.rpc('search_hybrid_recipes', {
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
            return self._fallback_search(query_embedding, top_k)
    
    def _fallback_search(self, query_embedding, top_k: int) -> List[Dict[str, Any]]:
        """하이브리드 방식용 백업 검색 방법"""
        try:
            result = self.supabase.table(self.table_name).select('*').execute()

            results = []
            # query_embedding을 numpy array로 변환
            query_embedding = np.array(query_embedding)
            
            for row in result.data:
                # embedding이 문자열인 경우 파싱
                embedding_data = row['embedding']
                if isinstance(embedding_data, str):
                    try:
                        import json
                        embedding_data = json.loads(embedding_data)
                    except:
                        # JSON 파싱 실패 시 스킵
                        continue
                
                # 데이터 타입을 float로 변환
                stored_embedding = np.array(embedding_data, dtype=np.float32)
                query_embedding_float = query_embedding.astype(np.float32)

                # 코사인 유사도 계산
                similarity = np.dot(query_embedding_float, stored_embedding)

                results.append({
                    'recipe_id': row['recipe_id'],
                    'title': row['title'],
                    'structured_blob': row['structured_blob'],
                    'llm_metadata': row['llm_metadata'],
                    'basic_metadata': row['basic_metadata'],
                    'similarity': float(similarity)
                })

            # 유사도 순으로 정렬하고 상위 k개 반환
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]

        except Exception as e:
            print(f"Error in fallback search: {e}")
            return []

if __name__ == "__main__":
    try:
        approach4 = HybridIngredientLLMApproachSupabase()
        approach4.load_recipes_from_supabase(limit=20)  # 테스트용으로 20개
        print("Approach 4 (Hybrid Ingredient LLM) Supabase setup complete!")
    except Exception as e:
        print(f"Error: {e}")
        print("Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
