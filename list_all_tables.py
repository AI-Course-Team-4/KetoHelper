"""
Supabase 테이블 목록을 다양한 방법으로 조회
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# .env 파일 로드
load_dotenv()

def list_supabase_tables():
    """모든 가능한 방법으로 Supabase 테이블 목록 조회"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        supabase: Client = create_client(supabase_url, supabase_key)
        print("Supabase 연결 성공!")

        # 방법 1: RPC로 테이블 목록 조회
        try:
            print("\n=== 방법 1: RPC 함수 시도 ===")
            result = supabase.rpc('get_all_tables', {}).execute()
            print(f"RPC 결과: {result}")
        except Exception as e:
            print(f"RPC 실패: {e}")

        # 방법 2: PostgREST API 직접 호출
        try:
            print("\n=== 방법 2: REST API 메타데이터 조회 ===")
            # PostgREST의 메타데이터 엔드포인트 사용
            import requests

            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
            }

            # OpenAPI 스펙 조회로 테이블 목록 확인
            response = requests.get(f'{supabase_url}/rest/v1/', headers=headers)
            if response.status_code == 200:
                # OpenAPI 응답에서 paths 섹션에 테이블명들이 있음
                spec = response.json()
                if 'paths' in spec:
                    tables = []
                    for path in spec['paths'].keys():
                        if path.startswith('/') and not path.startswith('/rpc/'):
                            table_name = path.strip('/')
                            if table_name and '/' not in table_name:
                                tables.append(table_name)

                    if tables:
                        print("발견된 테이블들:")
                        for table in sorted(set(tables)):
                            print(f"  - {table}")
                        return tables
                    else:
                        print("OpenAPI 스펙에서 테이블을 찾을 수 없음")
                else:
                    print("OpenAPI 스펙에 paths가 없음")
            else:
                print(f"OpenAPI 조회 실패: {response.status_code}")

        except Exception as e:
            print(f"REST API 조회 실패: {e}")

        # 방법 3: 알려진 패턴들로 무차별 시도
        print("\n=== 방법 3: 패턴 기반 검색 ===")
        test_patterns = [
            # 단순 이름들
            'recipes', 'recipe', 'Recipe', 'data', 'items', 'content',
            # 조합 이름들
            'recipe_data', 'recipes_data', 'recipe_list', 'recipe_items',
            'crawled_recipes', 'scraped_recipes', 'food_data',
            # 특수 문자 포함
            'recipe-data', 'recipe_crawler', 'cooking_data'
        ]

        found_tables = []
        for pattern in test_patterns:
            try:
                # 가장 간단한 쿼리로 테이블 존재 확인
                result = supabase.table(pattern).select('*').limit(1).execute()

                # 응답 구조 확인
                if hasattr(result, 'data'):
                    found_tables.append(pattern)
                    print(f"[FOUND] {pattern}")

                    # 레코드 수 확인
                    try:
                        count_result = supabase.table(pattern).select('*', count='exact').execute()
                        count = getattr(count_result, 'count', 'unknown')
                        print(f"  -> 레코드 수: {count}")
                    except:
                        print(f"  -> 레코드 수 확인 불가")

            except Exception as e:
                error_str = str(e)
                if 'PGRST205' not in error_str:  # 테이블 없음 오류가 아닌 경우
                    print(f"[MAYBE] {pattern} - 다른 오류: {error_str[:50]}...")

        if found_tables:
            print(f"\n총 {len(found_tables)}개 테이블 발견!")
            return found_tables
        else:
            print("\n테이블을 찾을 수 없습니다.")
            print("\nSupabase Dashboard에서 직접 확인해보세요:")
            print("1. Dashboard → Table Editor")
            print("2. 실제 테이블명을 여기에 알려주시면 분석해드리겠습니다")
            return []

    except Exception as e:
        print(f"전체 오류: {e}")
        return []

if __name__ == "__main__":
    list_supabase_tables()