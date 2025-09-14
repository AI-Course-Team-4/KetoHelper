"""
방식 3: LLM 기반 전처리 + 임베딩 (Supabase 버전)
LLM을 사용하여 레시피 정보를 구조화하고 정규화한 후 임베딩
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.supabase_config import BaseEmbeddingApproachSupabase
from typing import Dict, Any
import openai
import json
import time

class LLMPreprocessingApproachSupabase(BaseEmbeddingApproachSupabase):
    """LLM 기반 전처리 + 임베딩 방식 (Supabase)"""

    def __init__(self, openai_api_key: str = None):
        super().__init__("llm_preprocessing")

        # OpenAI API 키 설정 (환경변수 또는 매개변수에서)
        if openai_api_key:
            openai.api_key = openai_api_key
        elif os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
        else:
            print("Warning: OpenAI API key not found. LLM preprocessing will be skipped.")
            self.use_llm = False
            return

        self.use_llm = True

    def llm_preprocess_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """LLM을 사용한 레시피 전처리"""
        if not self.use_llm:
            # LLM을 사용할 수 없는 경우 기본 전처리
            return self.basic_preprocess_recipe(recipe)

        try:
            # LLM에게 보낼 프롬프트 구성
            prompt = self._create_preprocessing_prompt(recipe)

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 레시피 정보를 구조화하고 정규화하는 전문가입니다. 주어진 레시피 정보를 분석하여 깔끔하게 정리해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            # LLM 응답 파싱
            llm_result = response.choices[0].message.content
            processed_data = self._parse_llm_response(llm_result)

            # 약간의 딜레이 (API 제한 고려)
            time.sleep(0.1)

            return processed_data

        except Exception as e:
            print(f"LLM preprocessing failed: {e}")
            # 실패 시 기본 전처리로 fallback
            return self.basic_preprocess_recipe(recipe)

    def _create_preprocessing_prompt(self, recipe: Dict[str, Any]) -> str:
        """LLM 전처리를 위한 프롬프트 생성"""
        ingredients_str = ""
        ingredients_data = recipe.get('ingredients', [])
        if isinstance(ingredients_data, str):
            try:
                ingredients_data = json.loads(ingredients_data)
            except:
                ingredients_data = []

        if ingredients_data:
            ingredients_list = []
            for ing in ingredients_data:
                if isinstance(ing, dict):
                    name = ing.get('name', '')
                    amount = ing.get('amount', '')
                    ingredients_list.append(f"{name} {amount}".strip())
                else:
                    ingredients_list.append(str(ing))
            ingredients_str = ", ".join(ingredients_list)

        steps_str = ""
        steps_data = recipe.get('steps', [])
        if isinstance(steps_data, str):
            try:
                steps_data = json.loads(steps_data)
            except:
                steps_data = []

        if steps_data:
            steps_list = []
            for step in steps_data:
                if isinstance(step, dict):
                    steps_list.append(step.get('text', ''))
                else:
                    steps_list.append(str(step))
            steps_str = ". ".join(steps_list)

        tags_data = recipe.get('tags', [])
        if isinstance(tags_data, str):
            try:
                tags_data = json.loads(tags_data)
            except:
                tags_data = []

        prompt = f"""
다음 레시피 정보를 분석하여 JSON 형태로 정리해주세요:

제목: {recipe.get('title', '')}
설명: {recipe.get('summary', '')}
재료: {ingredients_str}
조리순서: {steps_str}
태그: {', '.join([str(t) for t in tags_data])}
분량: {recipe.get('servings', '')}
조리시간: {recipe.get('cook_time', '')}
난이도: {recipe.get('difficulty', '')}

다음과 같은 JSON 형식으로 반환해주세요:
{{
    "normalized_title": "정규화된 제목",
    "key_ingredients": ["주요 재료1", "주요 재료2", "주요 재료3"],
    "cooking_method": "주요 조리방법 (예: 볶음, 끓임, 구움 등)",
    "cuisine_type": "요리 종류 (예: 한식, 양식, 중식 등)",
    "dish_category": "음식 분류 (예: 메인요리, 반찬, 디저트 등)",
    "flavor_profile": "맛 특징 (예: 매운맛, 달콤함, 담백함 등)",
    "simplified_steps": ["핵심 조리과정1", "핵심 조리과정2", "핵심 조리과정3"],
    "keywords": ["검색 키워드1", "키워드2", "키워드3"]
}}

불필요한 설명 없이 JSON만 반환해주세요.
"""
        return prompt

    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """LLM 응답 파싱"""
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
            return {}

    def basic_preprocess_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """기본 전처리 (LLM 없이)"""
        title = self.normalize_text(recipe.get('title', ''))

        # 재료에서 주요 재료 추출
        key_ingredients = []
        ingredients_data = recipe.get('ingredients', [])
        if isinstance(ingredients_data, str):
            try:
                ingredients_data = json.loads(ingredients_data)
            except:
                ingredients_data = []

        for ingredient in ingredients_data[:5]:  # 상위 5개만
            if isinstance(ingredient, dict):
                name = self.normalize_text(ingredient.get('name', ''))
            else:
                name = self.normalize_text(str(ingredient))

            if name and len(name) > 1:
                key_ingredients.append(name)

        return {
            'normalized_title': title,
            'key_ingredients': key_ingredients,
            'cooking_method': '',
            'cuisine_type': '',
            'dish_category': '',
            'flavor_profile': '',
            'simplified_steps': [],
            'keywords': key_ingredients[:3]
        }

    def preprocess_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """레시피 전처리 - LLM 사용"""
        return self.llm_preprocess_recipe(recipe)

    def create_blob_content(self, recipe: Dict[str, Any], processed_content: Dict[str, Any]) -> str:
        """blob 콘텐츠 생성 - LLM 전처리된 구조화된 정보 사용"""
        blob_parts = []

        # 1. 정규화된 제목
        if processed_content.get('normalized_title'):
            blob_parts.append(f"요리명: {processed_content['normalized_title']}")

        # 2. 주요 재료
        if processed_content.get('key_ingredients'):
            ingredients_text = ", ".join(processed_content['key_ingredients'])
            blob_parts.append(f"주요재료: {ingredients_text}")

        # 3. 조리방법
        if processed_content.get('cooking_method'):
            blob_parts.append(f"조리법: {processed_content['cooking_method']}")

        # 4. 요리 종류
        if processed_content.get('cuisine_type'):
            blob_parts.append(f"종류: {processed_content['cuisine_type']}")

        # 5. 음식 분류
        if processed_content.get('dish_category'):
            blob_parts.append(f"분류: {processed_content['dish_category']}")

        # 6. 맛 특징
        if processed_content.get('flavor_profile'):
            blob_parts.append(f"맛: {processed_content['flavor_profile']}")

        # 7. 핵심 조리과정
        if processed_content.get('simplified_steps'):
            steps_text = ". ".join(processed_content['simplified_steps'])
            blob_parts.append(f"과정: {steps_text}")

        # 8. 키워드
        if processed_content.get('keywords'):
            keywords_text = ", ".join(processed_content['keywords'])
            blob_parts.append(f"키워드: {keywords_text}")

        # 9. 메타정보
        meta_info = []
        if recipe.get('servings'):
            meta_info.append(f"분량: {recipe['servings']}")
        if recipe.get('cook_time'):
            meta_info.append(f"시간: {recipe['cook_time']}")
        if recipe.get('difficulty'):
            meta_info.append(f"난이도: {recipe['difficulty']}")

        if meta_info:
            blob_parts.append(" ".join(meta_info))

        return " | ".join(blob_parts)

if __name__ == "__main__":
    try:
        approach3 = LLMPreprocessingApproachSupabase()
        if approach3.use_llm:
            approach3.load_recipes_from_supabase(limit=30)  # LLM 사용으로 더 적은 수량
            print("Approach 3 (LLM Preprocessing) Supabase setup complete!")
        else:
            print("Approach 3 requires OpenAI API key. Skipping LLM preprocessing.")
    except Exception as e:
        print(f"Error: {e}")
        print("Please set SUPABASE_URL, SUPABASE_ANON_KEY, and OPENAI_API_KEY environment variables")