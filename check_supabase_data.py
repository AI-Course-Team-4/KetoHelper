"""
Supabase 데이터베이스 구조 및 데이터 확인
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from pprint import pprint

# .env 파일 로드
load_dotenv()

def check_supabase_connection():
    """Supabase 연결 확인"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            print("[ERROR] .env 파일에 환경변수가 설정되지 않았습니다:")
            print("SUPABASE_URL:", "[OK]" if supabase_url else "[MISSING]")
            print("SUPABASE_ANON_KEY:", "[OK]" if supabase_key else "[MISSING]")
            print("\n.env 파일을 생성하고 다음과 같이 설정해주세요:")
            print("SUPABASE_URL=https://your-project-ref.supabase.co")
            print("SUPABASE_ANON_KEY=your-anon-key-here")
            print("OPENAI_API_KEY=your-openai-api-key-here  # 방식3용 (선택사항)")
            print("\n.env.example 파일을 참고하여 .env 파일을 만드세요!")
            return None

        supabase: Client = create_client(supabase_url, supabase_key)
        print("[SUCCESS] Supabase 연결 성공!")
        return supabase

    except Exception as e:
        print(f"[ERROR] Supabase 연결 실패: {e}")
        return None

def get_all_tables(supabase):
    """모든 테이블 목록 조회"""
    try:
        print("\n=== 테이블 목록 조회 ===")

        # Supabase에서 직접 테이블 목록을 가져오는 방법이 제한적이므로
        # 일반적으로 사용되는 테이블명들을 시도해보겠습니다
        possible_tables = [
            'recipes', 'recipe', 'recipes_data', 'crawled_recipes', 'recipe_items',
            'Recipe', 'Recipes', 'recipe_list', 'recipe_table', 'food_recipes',
            'recipe_crawler', 'scraped_recipes', 'menu', 'dish', 'food',
            'recipe_10000', 'ten_thousand_recipes', 'cooking_recipes'
        ]

        existing_tables = []
        for table_name in possible_tables:
            try:
                result = supabase.table(table_name).select("*").limit(1).execute()
                if result.data is not None:
                    existing_tables.append(table_name)
                    print(f"[OK] {table_name} - 존재함")
                else:
                    print(f"[NO] {table_name} - 존재하지 않거나 접근 불가")
            except Exception as e:
                print(f"[ERROR] {table_name} - 오류: {str(e)[:50]}...")

        return existing_tables

    except Exception as e:
        print(f"[ERROR] 테이블 목록 조회 실패: {e}")
        return []

def analyze_table_structure(supabase, table_name):
    """특정 테이블의 구조 및 데이터 분석"""
    try:
        print(f"\n=== {table_name} 테이블 분석 ===")

        # 샘플 데이터 조회
        result = supabase.table(table_name).select("*").limit(3).execute()

        if not result.data:
            print(f"[EMPTY] {table_name} 테이블이 비어있습니다.")
            return None

        total_count_result = supabase.table(table_name).select("*", count="exact").execute()
        total_count = total_count_result.count if hasattr(total_count_result, 'count') else len(result.data)

        print(f"총 레코드 수: {total_count}")
        print(f"샘플 데이터 ({len(result.data)}개):")

        # 첫 번째 레코드의 스키마 분석
        if result.data:
            first_record = result.data[0]
            print(f"\n스키마 구조:")

            for key, value in first_record.items():
                value_type = type(value).__name__
                if isinstance(value, str) and len(value) > 100:
                    value_preview = value[:100] + "..."
                elif isinstance(value, (list, dict)):
                    try:
                        value_preview = json.dumps(value, ensure_ascii=False)[:100] + "..."
                    except:
                        value_preview = str(value)[:100] + "..."
                else:
                    value_preview = str(value)

                print(f"  {key:20} ({value_type:10}) : {value_preview}")

        print(f"\n전체 샘플 데이터:")
        for i, record in enumerate(result.data, 1):
            print(f"\n--- 레코드 {i} ---")
            pprint(record, width=100, depth=2)

        return result.data

    except Exception as e:
        print(f"[ERROR] {table_name} 테이블 분석 실패: {e}")
        return None

def check_recipes_data_format(supabase, table_name):
    """레시피 데이터 형식 상세 분석"""
    try:
        print(f"\n=== {table_name} 레시피 데이터 형식 분석 ===")

        result = supabase.table(table_name).select("*").limit(5).execute()

        if not result.data:
            return

        # 필드별 데이터 타입 및 내용 분석
        field_analysis = {}

        for record in result.data:
            for field, value in record.items():
                if field not in field_analysis:
                    field_analysis[field] = {
                        'type': set(),
                        'sample_values': [],
                        'null_count': 0,
                        'is_json': False
                    }

                if value is None:
                    field_analysis[field]['null_count'] += 1
                else:
                    field_analysis[field]['type'].add(type(value).__name__)

                    # JSON 형태인지 확인
                    if isinstance(value, str):
                        try:
                            json.loads(value)
                            field_analysis[field]['is_json'] = True
                        except:
                            pass

                    # 샘플 값 저장 (최대 3개)
                    if len(field_analysis[field]['sample_values']) < 3:
                        if isinstance(value, str) and len(value) > 200:
                            field_analysis[field]['sample_values'].append(value[:200] + "...")
                        else:
                            field_analysis[field]['sample_values'].append(value)

        print(f"\n필드별 상세 분석:")
        for field, analysis in field_analysis.items():
            print(f"\n- {field}:")
            print(f"  타입: {', '.join(analysis['type'])}")
            print(f"  NULL 개수: {analysis['null_count']}/{len(result.data)}")
            print(f"  JSON 형태: {'예' if analysis['is_json'] else '아니오'}")
            print(f"  샘플 값:")
            for i, sample in enumerate(analysis['sample_values'], 1):
                print(f"    {i}. {sample}")

    except Exception as e:
        print(f"[ERROR] 레시피 데이터 형식 분석 실패: {e}")

def main():
    """메인 실행 함수"""
    print("Supabase 데이터베이스 구조 확인 시작")

    # Supabase 연결
    supabase = check_supabase_connection()
    if not supabase:
        return

    # 모든 테이블 목록 조회
    tables = get_all_tables(supabase)

    if not tables:
        print("\n[NO TABLES] 접근 가능한 테이블이 없습니다.")
        return

    # 각 테이블 분석
    for table_name in tables:
        analyze_table_structure(supabase, table_name)
        check_recipes_data_format(supabase, table_name)

    print(f"\n[COMPLETE] 총 {len(tables)}개 테이블 분석 완료!")
    print(f"발견된 테이블: {', '.join(tables)}")

if __name__ == "__main__":
    main()