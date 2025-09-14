"""
Supabase에서 실제 테이블 이름 찾기
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 파일 로드
load_dotenv()

def find_supabase_tables():
    """Supabase에서 실제 테이블 찾기"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            print("[ERROR] .env 파일 설정이 필요합니다")
            return

        supabase: Client = create_client(supabase_url, supabase_key)
        print("[SUCCESS] Supabase 연결 성공!")

        print("\n=== PostgreSQL 시스템 테이블로 테이블 목록 조회 시도 ===")

        # PostgreSQL information_schema를 통해 테이블 목록 조회 시도
        try:
            # RPC 함수로 테이블 목록 조회 (만약 함수가 있다면)
            result = supabase.rpc('get_table_names').execute()
            print(f"RPC 함수 결과: {result.data}")
        except Exception as e:
            print(f"[INFO] RPC 함수 없음: {str(e)[:100]}...")

        print("\n=== 다양한 테이블명 패턴 시도 ===")

        # 테이블 목록을 직접 조회하는 방법 시도
        try:
            print("PostgreSQL information_schema 직접 조회 시도...")
            # PostgreSQL 시스템 카탈로그로 테이블 목록 조회
            result = supabase.from_('information_schema.tables').select('table_name').eq('table_schema', 'public').execute()
            if result.data:
                print("실제 테이블 목록:")
                for table in result.data:
                    print(f"  - {table['table_name']}")
                return [table['table_name'] for table in result.data]
        except Exception as e:
            print(f"정보 스키마 조회 실패: {str(e)[:100]}...")

        # 더 많은 테이블명 패턴 시도
        possible_tables = [
            # 기본 레시피 테이블명들
            'recipes', 'recipe', 'Recipe', 'Recipes', 'RECIPES',
            'recipes_data', 'recipe_data', 'recipe_list', 'recipe_items',
            'crawled_recipes', 'scraped_recipes', 'recipe_crawler',
            'food_recipes', 'cooking_recipes', 'recipe_table',

            # 만개의레시피 관련
            'recipe_10000', 'ten_thousand_recipes', '10000recipe',
            'mankaereceipe', 'mankae_recipe', 'recipe_mankae',

            # 일반적인 음식 관련
            'food', 'foods', 'dish', 'dishes', 'menu', 'menus',
            'cooking', 'cook', 'meal', 'meals',

            # 다른 가능한 이름들
            'recipe_info', 'recipe_detail', 'recipe_master',
            'food_data', 'dish_data', 'cooking_data',
            'recipe_source', 'recipe_content', 'items', 'data',

            # public 스키마 명시적 접근
            'public.recipes', 'public.recipe', 'public.Recipe'
        ]

        existing_tables = []
        for table_name in possible_tables:
            try:
                # 매우 간단한 쿼리로 테이블 존재 확인
                result = supabase.table(table_name).select("*").limit(1).execute()

                if hasattr(result, 'data') and result.data is not None:
                    existing_tables.append(table_name)
                    count_result = supabase.table(table_name).select("*", count="exact").execute()
                    count = count_result.count if hasattr(count_result, 'count') else '?'
                    print(f"[FOUND] {table_name} - {count}개 레코드")

            except Exception as e:
                error_msg = str(e)
                if 'PGRST116' in error_msg:  # 테이블 존재하지만 컬럼이 없음
                    existing_tables.append(table_name)
                    print(f"[FOUND-EMPTY] {table_name} - 컬럼 없음")
                elif 'PGRST205' not in error_msg:  # 테이블이 없다는 오류가 아닌 경우
                    print(f"[MAYBE] {table_name} - 다른 오류: {error_msg[:50]}...")

        if existing_tables:
            print(f"\n=== 발견된 테이블들 ({len(existing_tables)}개) ===")
            for table in existing_tables:
                print(f"- {table}")
        else:
            print("\n[INFO] 접근 가능한 테이블을 찾지 못했습니다.")
            print("\nSupabase Dashboard에서 확인해주세요:")
            print("1. https://supabase.com/dashboard 접속")
            print("2. 프로젝트 선택")
            print("3. Table Editor에서 테이블 목록 확인")
            print("4. 테이블이 없다면 먼저 데이터를 업로드하거나 테이블을 생성해야 합니다")

        return existing_tables

    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        return []

if __name__ == "__main__":
    find_supabase_tables()