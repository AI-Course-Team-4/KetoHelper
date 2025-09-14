"""
방식 1: 레시피명 + blob 임베딩 (Supabase 버전)
레시피 제목을 포함하여 모든 정보를 하나의 blob으로 만들어 임베딩
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.supabase_config import BaseEmbeddingApproachSupabase
from typing import Dict, Any

class TitleBlobApproachSupabase(BaseEmbeddingApproachSupabase):
    """레시피명 + blob 임베딩 방식 (Supabase)"""

    def __init__(self):
        super().__init__("title_blob")

    def preprocess_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """레시피 전처리 - 기본 정규화만 적용"""
        title = self.normalize_text(recipe.get('title', ''))
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
            'title': title,
            'summary': summary,
            'ingredients': ingredients,
            'steps': steps,
            'tags': tags
        }

    def create_blob_content(self, recipe: Dict[str, Any], processed_content: Dict[str, Any]) -> str:
        """blob 콘텐츠 생성 - 제목과 식재료만 포함"""
        blob_parts = []

        # 1. 제목 (가장 중요하므로 맨 앞에)
        if processed_content['title']:
            blob_parts.append(f"제목: {processed_content['title']}")

        # 2. 재료 (두 번째로 중요한 요소)
        if processed_content['ingredients']:
            ingredients_text = ", ".join(processed_content['ingredients'])
            blob_parts.append(f"재료: {ingredients_text}")

        return " | ".join(blob_parts)

if __name__ == "__main__":
    try:
        approach1 = TitleBlobApproachSupabase()
        approach1.load_recipes_from_supabase(limit=50)  # 테스트용으로 50개
        print("Approach 1 (Title + Blob) Supabase setup complete!")
    except Exception as e:
        print(f"Error: {e}")
        print("Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")