import json
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY

class SupabaseClient:
    """Supabase 클라이언트"""

    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def create_crawl_run(self, query: str, page_start: int = 1, page_end: Optional[int] = None) -> str:
        """크롤링 실행 이력 생성"""
        try:
            data = {
                'query': query,
                'page_start': page_start,
                'page_end': page_end,
                'started_at': datetime.now().isoformat(),
            }

            result = self.client.table('crawl_runs').insert(data).execute()
            return result.data[0]['run_id']
        except Exception as e:
            print(f"Failed to create crawl run: {e}")
            raise

    async def update_crawl_run(self, run_id: str, **kwargs) -> bool:
        """크롤링 실행 이력 업데이트"""
        try:
            if 'finished_at' not in kwargs:
                kwargs['finished_at'] = datetime.now().isoformat()

            self.client.table('crawl_runs').update(kwargs).eq('run_id', run_id).execute()
            return True
        except Exception as e:
            print(f"Failed to update crawl run {run_id}: {e}")
            return False

    async def upsert_recipe(self, recipe_data: Dict) -> bool:
        """레시피 데이터 업서트 (중복 시 업데이트)"""
        try:
            # JSON 필드 변환 (한글 직접 저장)
            if 'ingredients' in recipe_data and recipe_data['ingredients']:
                recipe_data['ingredients'] = json.dumps(recipe_data['ingredients'], ensure_ascii=False)
            if 'steps' in recipe_data and recipe_data['steps']:
                recipe_data['steps'] = json.dumps(recipe_data['steps'], ensure_ascii=False)

            # 타임스탬프 설정
            recipe_data['fetched_at'] = datetime.now().isoformat()

            # UPSERT 실행
            self.client.table('recipes_keto_raw').upsert(recipe_data).execute()
            return True
        except Exception as e:
            print(f"Failed to upsert recipe {recipe_data.get('source_url', 'unknown')}: {e}")
            return False

    async def get_existing_recipe_urls(self) -> set:
        """기존에 저장된 레시피 URL 목록 조회"""
        try:
            result = self.client.table('recipes_keto_raw').select('source_url').execute()
            return {row['source_url'] for row in result.data}
        except Exception as e:
            print(f"Failed to get existing recipe URLs: {e}")
            return set()

    async def get_recipe_count(self) -> int:
        """저장된 레시피 수 조회"""
        try:
            result = self.client.table('recipes_keto_raw').select('*', count='exact').execute()
            return result.count
        except Exception as e:
            print(f"Failed to get recipe count: {e}")
            return 0

    async def get_field_completeness_stats(self) -> Dict[str, float]:
        """필드 완성도 통계 조회"""
        try:
            result = self.client.table('recipes_keto_raw').select('*').execute()
            if not result.data:
                return {}

            total_count = len(result.data)
            field_stats = {}

            key_fields = ['title', 'ingredients', 'steps', 'source_url']
            for field in key_fields:
                non_null_count = sum(1 for row in result.data if row.get(field))
                field_stats[field] = (non_null_count / total_count) * 100

            return field_stats
        except Exception as e:
            print(f"Failed to get field completeness stats: {e}")
            return {}

    async def execute_ddl(self) -> bool:
        """데이터베이스 스키마 생성"""
        ddl_sql = """
        -- 확장 설치
        create extension if not exists pgcrypto;
        create extension if not exists pg_trgm;
        create extension if not exists vector;

        -- 레시피 테이블 (크롤링용)
        create table if not exists recipes_keto_raw (
          id uuid primary key default gen_random_uuid(),
          source_site text not null default '10000recipe',
          source_url text not null unique,
          source_recipe_id text,
          title text,
          author text,
          rating numeric,
          views int,
          servings text,
          cook_time text,
          difficulty text,
          summary text,
          tags text[],
          ingredients jsonb,
          steps jsonb,
          images text[],
          fetched_at timestamptz not null default now(),
          -- 검색용 생성열
          search_blob text generated always as (
            lower(
              coalesce(title,'') || ' ' ||
              array_to_string(tags,' ') || ' ' ||
              coalesce(summary,'') || ' ' ||
              array_to_string((select array_agg(value::text)
                from jsonb_array_elements_text(ingredients)),' ') || ' ' ||
              array_to_string((select array_agg(s->>'text')
                from jsonb_array_elements(steps) s),' ')
            )
          ) stored,
          embedding vector(1536)
        );

        -- 크롤링 실행 이력 테이블
        create table if not exists crawl_runs (
          run_id uuid primary key default gen_random_uuid(),
          query text not null,
          started_at timestamptz not null default now(),
          finished_at timestamptz,
          page_start int,
          page_end int,
          inserted_count int default 0,
          updated_count int default 0,
          error_count int default 0,
          notes text
        );

        -- 인덱스 생성
        create index if not exists idx_recipes_tags on recipes_keto_raw using gin(tags);
        create index if not exists idx_recipes_ingredients on recipes_keto_raw using gin(ingredients);
        create index if not exists idx_recipes_trgm on recipes_keto_raw using gin (search_blob gin_trgm_ops);
        """

        try:
            # Note: Supabase Python client doesn't directly support DDL execution
            # This would need to be run manually in Supabase SQL editor
            print("DDL SQL ready to execute in Supabase SQL editor:")
            print(ddl_sql)
            return True
        except Exception as e:
            print(f"DDL execution info: {e}")
            return False