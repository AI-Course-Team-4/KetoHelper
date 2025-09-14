"""
방식 1: 레시피명 + blob 임베딩
레시피 제목을 포함하여 모든 정보를 하나의 blob으로 만들어 임베딩
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.base_config import BaseEmbeddingApproach
from typing import Dict, Any
import re

class TitleBlobApproach(BaseEmbeddingApproach):
    """레시피명 + blob 임베딩 방식"""

    def __init__(self):
        super().__init__("title_blob", "embeddings_comparison.db")

    def preprocess_recipe(self, recipe: Dict[str, Any]) -> str:
        """레시피 전처리 - 기본 정규화만 적용"""
        title = self.normalize_text(recipe.get('title', ''))
        summary = self.normalize_text(recipe.get('summary', ''))

        # 재료 전처리
        ingredients = []
        for ingredient in recipe.get('ingredients', []):
            name = self.normalize_text(ingredient.get('name', ''))
            amount = self.normalize_text(ingredient.get('amount', ''))
            if name:
                if amount:
                    ingredients.append(f"{name} {amount}")
                else:
                    ingredients.append(name)

        # 조리순서 전처리
        steps = []
        for step in recipe.get('steps', []):
            step_text = self.normalize_text(step.get('text', ''))
            if step_text:
                steps.append(step_text)

        # 태그 전처리
        tags = [self.normalize_text(tag) for tag in recipe.get('tags', []) if self.normalize_text(tag)]

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

    def process_recipes_from_db(self, source_db_path: str = "recipes.db"):
        """기존 레시피 DB에서 데이터를 읽어와서 처리"""
        import sqlite3
        import json

        try:
            # 소스 DB 연결
            source_conn = sqlite3.connect(source_db_path)
            source_cursor = source_conn.cursor()

            source_cursor.execute('SELECT * FROM recipes LIMIT 100')  # 테스트용으로 100개만
            rows = source_cursor.fetchall()

            # 컬럼명 가져오기
            column_names = [description[0] for description in source_cursor.description]

            processed_count = 0
            for row in rows:
                # 딕셔너리로 변환
                recipe = dict(zip(column_names, row))

                # JSON 필드들 파싱
                for field in ['ingredients', 'steps', 'tags', 'images']:
                    if recipe.get(field):
                        try:
                            recipe[field] = json.loads(recipe[field])
                        except:
                            recipe[field] = []

                # 임베딩 처리 및 저장
                if self.save_recipe_embedding(recipe):
                    processed_count += 1

                if processed_count % 10 == 0:
                    print(f"Processed {processed_count} recipes...")

            source_conn.close()
            print(f"Total processed: {processed_count} recipes")

        except Exception as e:
            print(f"Error processing recipes: {e}")

if __name__ == "__main__":
    approach1 = TitleBlobApproach()
    approach1.process_recipes_from_db()
    print("Approach 1 (Title + Blob) setup complete!")