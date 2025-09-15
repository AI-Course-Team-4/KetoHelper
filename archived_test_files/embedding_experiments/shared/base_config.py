"""
공통 설정 및 기본 클래스들
"""

import os
import json
import sqlite3
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import numpy as np
from sentence_transformers import SentenceTransformer

class BaseEmbeddingApproach(ABC):
    """임베딩 방식 기본 클래스"""

    def __init__(self, approach_name: str, db_path: str):
        self.approach_name = approach_name
        self.db_path = db_path
        self.model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        self.table_name = f"recipes_{approach_name.replace(' ', '_').lower()}"
        self.setup_database()

    def setup_database(self):
        """데이터베이스 테이블 설정"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id TEXT UNIQUE,
                title TEXT,
                processed_content TEXT,
                raw_content TEXT,
                embedding BLOB,
                metadata TEXT
            )
        ''')

        conn.commit()
        conn.close()

    @abstractmethod
    def preprocess_recipe(self, recipe: Dict[str, Any]) -> str:
        """레시피 전처리 (각 방식별로 구현)"""
        pass

    @abstractmethod
    def create_blob_content(self, recipe: Dict[str, Any], processed_content: str) -> str:
        """blob 콘텐츠 생성 (각 방식별로 구현)"""
        pass

    def normalize_text(self, text: str) -> str:
        """기본 텍스트 정규화"""
        if not text:
            return ""

        # 기본 정규화
        text = text.strip()
        text = ' '.join(text.split())  # 여러 공백을 하나로

        # 특수문자 정리
        replacements = {
            '·': ' ',
            '∙': ' ',
            '※': '',
            '★': '',
            '♥': '',
            '♡': '',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text.strip()

    def save_recipe_embedding(self, recipe: Dict[str, Any]) -> bool:
        """레시피 임베딩 저장"""
        try:
            # 전처리
            processed_content = self.preprocess_recipe(recipe)

            # blob 콘텐츠 생성
            blob_content = self.create_blob_content(recipe, processed_content)

            # 임베딩 생성
            embedding = self.model.encode(blob_content, normalize_embeddings=True)

            # 데이터베이스 저장
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(f'''
                INSERT OR REPLACE INTO {self.table_name}
                (recipe_id, title, processed_content, raw_content, embedding, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                recipe.get('source_recipe_id', ''),
                recipe.get('title', ''),
                processed_content,
                json.dumps(recipe, ensure_ascii=False),
                embedding.tobytes(),
                json.dumps({
                    'approach': self.approach_name,
                    'blob_length': len(blob_content),
                    'has_title': bool(recipe.get('title', '').strip())
                }, ensure_ascii=False)
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error saving recipe {recipe.get('source_recipe_id', 'unknown')}: {e}")
            return False

    def search_similar_recipes(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """유사 레시피 검색"""
        try:
            # 쿼리 임베딩
            query_embedding = self.model.encode(query, normalize_embeddings=True)

            # 데이터베이스에서 모든 임베딩 가져오기
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(f'''
                SELECT recipe_id, title, processed_content, raw_content, embedding, metadata
                FROM {self.table_name}
            ''')

            results = []
            for row in cursor.fetchall():
                recipe_id, title, processed_content, raw_content, embedding_blob, metadata = row

                # 임베딩 복원
                stored_embedding = np.frombuffer(embedding_blob, dtype=np.float32)

                # 코사인 유사도 계산
                similarity = np.dot(query_embedding, stored_embedding)

                results.append({
                    'recipe_id': recipe_id,
                    'title': title,
                    'processed_content': processed_content,
                    'raw_content': json.loads(raw_content),
                    'metadata': json.loads(metadata),
                    'similarity': float(similarity)
                })

            conn.close()

            # 유사도 기준 정렬 후 top_k 반환
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]

        except Exception as e:
            print(f"Error in search: {e}")
            return []

# 공통 설정
EMBEDDING_CONFIG = {
    'model_name': 'jhgan/ko-sroberta-multitask',
    'golden_set_size': 50,
    'test_query_size': 30,
    'top_k_results': 10,
    'similarity_threshold': 0.7
}

# 데이터베이스 경로
DATABASE_PATH = "embeddings_comparison.db"