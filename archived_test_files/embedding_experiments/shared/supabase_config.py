"""
Supabase 연결 및 설정
"""

import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import numpy as np
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from openai import OpenAI
import json

# .env 파일 로드
load_dotenv()

class BaseEmbeddingApproachSupabase(ABC):
    """Supabase를 사용하는 임베딩 방식 기본 클래스"""

    def __init__(self, approach_name: str):
        self.approach_name = approach_name
        # OpenAI text-embedding-3-small 모델 사용
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_model = 'text-embedding-3-small'
        self.embedding_dimension = 1536  # text-embedding-3-small 차원
        self.table_name = f"recipes_{approach_name.replace(' ', '_').lower()}"

        # Supabase 클라이언트 설정
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL과 SUPABASE_ANON_KEY 환경변수가 필요합니다.")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.setup_table()

    def setup_table(self):
        """Supabase 테이블 설정"""
        try:
            # 테이블이 이미 존재하는지 확인
            result = self.supabase.table(self.table_name).select("*").limit(1).execute()
            print(f"Table {self.table_name} already exists")
        except Exception:
            print(f"Creating table {self.table_name}...")
            # 테이블 생성은 Supabase 대시보드에서 수동으로 생성하거나
            # SQL을 통해 생성해야 합니다.
            print(f"Please create table {self.table_name} with the following columns:")
            print("""
            CREATE TABLE {table_name} (
                id BIGSERIAL PRIMARY KEY,
                recipe_id TEXT UNIQUE,
                title TEXT,
                processed_content TEXT,
                raw_content JSONB,
                embedding vector(1536),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT now()
            );

            -- 벡터 유사도 검색을 위한 인덱스 생성
            CREATE INDEX ON {table_name} USING ivfflat (embedding vector_cosine_ops);
            """.format(table_name=self.table_name))

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
            # 실패 시 1536차원 0벡터 반환
            return [0.0] * self.embedding_dimension

    def save_recipe_embedding(self, recipe: Dict[str, Any]) -> bool:
        """레시피 임베딩 저장"""
        try:
            # 전처리
            processed_content = self.preprocess_recipe(recipe)

            # blob 콘텐츠 생성
            blob_content = self.create_blob_content(recipe, processed_content)

            # OpenAI text-embedding-3-small로 임베딩 생성
            embedding = self._get_openai_embedding(blob_content)

            # Supabase에 저장
            data = {
                'recipe_id': recipe.get('source_recipe_id', ''),
                'title': recipe.get('title', ''),
                'processed_content': processed_content,
                'raw_content': recipe,
                'embedding': embedding,  # OpenAI API는 이미 list를 반환
                'metadata': {
                    'approach': self.approach_name,
                    'blob_length': len(blob_content),
                    'has_title': bool(recipe.get('title', '').strip())
                }
            }

            result = self.supabase.table(self.table_name).upsert(data, on_conflict='recipe_id').execute()

            return True

        except Exception as e:
            print(f"Error saving recipe {recipe.get('source_recipe_id', 'unknown')}: {e}")
            return False

    def search_similar_recipes(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """유사 레시피 검색 - OpenAI 임베딩 사용"""
        try:
            # 쿼리 임베딩 (OpenAI text-embedding-3-small)
            query_embedding = self._get_openai_embedding(query)

            # Supabase에서 벡터 유사도 검색
            # pgvector의 cosine similarity 검색 사용
            result = self.supabase.rpc('search_recipes', {
                'query_embedding': query_embedding,  # 이미 list이므로 .tolist() 제거
                'table_name': self.table_name,
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
        """백업 검색 방법 - 모든 데이터를 가져와서 클라이언트에서 유사도 계산"""
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
                    'processed_content': row['processed_content'],
                    'raw_content': row['raw_content'],
                    'metadata': row['metadata'],
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
                # 임베딩 처리 및 저장
                if self.save_recipe_embedding(recipe):
                    processed_count += 1

                if processed_count % 10 == 0:
                    print(f"Processed {processed_count} recipes...")

            print(f"Total processed: {processed_count} recipes")

        except Exception as e:
            print(f"Error loading recipes from Supabase: {e}")

# 공통 설정
EMBEDDING_CONFIG = {
    'model_name': 'text-embedding-3-small',
    'embedding_dimension': 1536,
    'golden_set_size': 50,
    'test_query_size': 30,
    'top_k_results': 10,
    'similarity_threshold': 0.7
}

# Supabase 벡터 검색을 위한 SQL 함수 (Supabase에 수동으로 생성 필요)
VECTOR_SEARCH_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION search_recipes(
  query_embedding vector(1536),
  table_name text,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  recipe_id text,
  title text,
  processed_content text,
  raw_content jsonb,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  EXECUTE format('
    SELECT r.recipe_id, r.title, r.processed_content, r.raw_content, r.metadata,
           1 - (r.embedding <=> $1) as similarity
    FROM %I r
    ORDER BY r.embedding <=> $1
    LIMIT $2
  ', table_name)
  USING query_embedding, match_count;
END;
$$;
"""