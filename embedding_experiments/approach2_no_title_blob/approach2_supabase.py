"""
방식 2: 제목 제외 blob 임베딩 (Supabase 버전)
레시피 제목을 제외하고 재료, 조리순서 등의 정보만으로 blob을 만들어 임베딩
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.supabase_config import BaseEmbeddingApproachSupabase
from typing import Dict, Any

class NoTitleBlobApproachSupabase(BaseEmbeddingApproachSupabase):
    """제목 제외 blob 임베딩 방식 (Supabase)"""

    def __init__(self):
        super().__init__("no_title_blob")

    def preprocess_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """레시피 전처리 - 제목 제외"""
        summary = self.normalize_text(recipe.get('summary', ''))

        # 재료 전처리
        ingredients = []
        ingredients_data = recipe.get('ingredients', [])
        if isinstance(ingredients_data, str):
            try:
                import json
                ingredients_data = json.loads(ingredients_data)
            except:
                ingredients_data = []

        for ingredient in ingredients_data:
            if isinstance(ingredient, dict):
                name = self.normalize_text(ingredient.get('name', ''))
                amount = self.normalize_text(ingredient.get('amount', ''))
            else:
                name = self.normalize_text(str(ingredient))
                amount = ''

            if name:
                if amount:
                    ingredients.append(f"{name} {amount}")
                else:
                    ingredients.append(name)

        # 조리순서 전처리
        steps = []
        steps_data = recipe.get('steps', [])
        if isinstance(steps_data, str):
            try:
                import json
                steps_data = json.loads(steps_data)
            except:
                steps_data = []

        for step in steps_data:
            if isinstance(step, dict):
                step_text = self.normalize_text(step.get('text', ''))
            else:
                step_text = self.normalize_text(str(step))

            if step_text:
                steps.append(step_text)

        # 태그 전처리
        tags = []
        tags_data = recipe.get('tags', [])
        if isinstance(tags_data, str):
            try:
                import json
                tags_data = json.loads(tags_data)
            except:
                tags_data = []

        for tag in tags_data:
            normalized_tag = self.normalize_text(str(tag))
            if normalized_tag:
                tags.append(normalized_tag)

        return {
            'summary': summary,
            'ingredients': ingredients,
            'steps': steps,
            'tags': tags
        }

    def create_blob_content(self, recipe: Dict[str, Any], processed_content: Dict[str, Any]) -> str:
        """blob 콘텐츠 생성 - 제목과 조리순서 제외, 식재료 중심"""
        blob_parts = []

        # 1. 재료 (가장 중요한 요소로 맨 앞에)
        if processed_content['ingredients']:
            ingredients_text = ", ".join(processed_content['ingredients'])
            blob_parts.append(f"재료: {ingredients_text}")

        # 2. 요약/설명
        if processed_content['summary']:
            blob_parts.append(f"설명: {processed_content['summary']}")

        # 3. 태그
        if processed_content['tags']:
            tags_text = ", ".join(processed_content['tags'])
            blob_parts.append(f"태그: {tags_text}")

        # 4. 추가 메타정보
        meta_info = []
        if recipe.get('servings'):
            meta_info.append(f"분량: {recipe['servings']}")
        if recipe.get('cook_time'):
            meta_info.append(f"조리시간: {recipe['cook_time']}")
        if recipe.get('difficulty'):
            meta_info.append(f"난이도: {recipe['difficulty']}")
        if recipe.get('author'):
            meta_info.append(f"작성자: {recipe['author']}")

        if meta_info:
            blob_parts.append(" ".join(meta_info))

        return " | ".join(blob_parts)

if __name__ == "__main__":
    try:
        approach2 = NoTitleBlobApproachSupabase()
        approach2.load_recipes_from_supabase(limit=50)  # 테스트용으로 50개
        print("Approach 2 (No Title Blob) Supabase setup complete!")
    except Exception as e:
        print(f"Error: {e}")
        print("Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")