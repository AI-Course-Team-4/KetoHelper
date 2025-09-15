"""
Supabase 기반 3가지 임베딩 방식 실험 실행 스크립트
"""

import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.abspath('.'))

# .env 파일 로드
load_dotenv()

from approach1_title_blob.approach1_supabase import TitleBlobApproachSupabase
from approach2_no_title_blob.approach2_supabase import NoTitleBlobApproachSupabase
from approach3_llm_preprocessing.approach3_supabase import LLMPreprocessingApproachSupabase
from shared.evaluation import EmbeddingEvaluator
import time

def check_environment():
    """환경변수 확인"""
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("다음 환경변수가 .env 파일에 설정되지 않았습니다:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\n.env 파일을 생성하고 다음과 같이 설정해주세요:")
        print("SUPABASE_URL=https://your-project-ref.supabase.co")
        print("SUPABASE_ANON_KEY=your-anon-key-here")
        print("OPENAI_API_KEY=your-openai-api-key-here  # LLM 방식용 (선택사항)")
        print("\n.env.example 파일을 참고하세요!")
        return False

    return True

def setup_supabase_tables():
    """Supabase 테이블 설정 안내"""
    print("=== Supabase 테이블 설정 안내 ===")
    print("\n다음 SQL을 Supabase SQL Editor에서 실행해주세요:")
    print("\n1. pgvector 확장 활성화:")
    print("CREATE EXTENSION IF NOT EXISTS vector;")

    table_names = ['recipes_title_blob', 'recipes_no_title_blob', 'recipes_llm_preprocessing']

    for table_name in table_names:
        print(f"\n2. {table_name} 테이블 생성:")
        print(f"""
CREATE TABLE {table_name} (
    id BIGSERIAL PRIMARY KEY,
    recipe_id TEXT UNIQUE,
    title TEXT,
    processed_content TEXT,
    raw_content JSONB,
    embedding vector(768),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);

-- 벡터 유사도 검색을 위한 인덱스 생성
CREATE INDEX ON {table_name} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
""")

    print("\n3. 벡터 검색 함수 생성:")
    print("""
CREATE OR REPLACE FUNCTION search_recipes(
  query_embedding vector(768),
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
""")

def setup_experiments():
    """실험 환경 설정"""
    print("=== Supabase 기반 임베딩 방식별 실험 시작 ===\n")

    approaches = []

    # 1. Approach 1: Title + Blob
    print("1. Setting up Approach 1 (Title + Blob)...")
    try:
        approach1 = TitleBlobApproachSupabase()
        approach1.load_recipes_from_supabase(limit=50)
        approaches.append((approach1, "title_blob"))
        print("Approach 1 setup complete!\n")
    except Exception as e:
        print(f"Approach 1 setup failed: {e}\n")

    # 2. Approach 2: No Title + Blob
    print("2. Setting up Approach 2 (No Title + Blob)...")
    try:
        approach2 = NoTitleBlobApproachSupabase()
        approach2.load_recipes_from_supabase(limit=50)
        approaches.append((approach2, "no_title_blob"))
        print("Approach 2 setup complete!\n")
    except Exception as e:
        print(f"Approach 2 setup failed: {e}\n")

    # 3. Approach 3: LLM Preprocessing
    print("3. Setting up Approach 3 (LLM Preprocessing)...")
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Warning: OPENAI_API_KEY not found. Using basic preprocessing instead.")

        approach3 = LLMPreprocessingApproachSupabase(api_key)
        if approach3.use_llm:
            approach3.load_recipes_from_supabase(limit=30)  # LLM 사용으로 적은 수량
        else:
            approach3.load_recipes_from_supabase(limit=50)  # 기본 전처리로 더 많이

        approaches.append((approach3, "llm_preprocessing"))
        print("Approach 3 setup complete!\n")
    except Exception as e:
        print(f"Approach 3 setup failed: {e}\n")

    return approaches

def quick_test():
    """빠른 테스트 - 각 방식이 제대로 동작하는지 확인"""
    print("=== Supabase 연결 및 빠른 동작 테스트 ===\n")

    if not check_environment():
        return

    test_queries = ["닭고기 요리", "볶음밥", "간단한 요리"]

    approaches_info = [
        (TitleBlobApproachSupabase, "Approach 1 (Title + Blob)"),
        (NoTitleBlobApproachSupabase, "Approach 2 (No Title + Blob)"),
        (LLMPreprocessingApproachSupabase, "Approach 3 (LLM Preprocessing)")
    ]

    for approach_class, name in approaches_info:
        print(f"{name} 테스트:")
        try:
            if approach_class == LLMPreprocessingApproachSupabase:
                approach = approach_class(os.getenv('OPENAI_API_KEY'))
            else:
                approach = approach_class()

            for query in test_queries:
                try:
                    results = approach.search_similar_recipes(query, top_k=3)
                    print(f"  '{query}' -> {len(results)} results found")
                    if results:
                        print(f"    Top result: {results[0]['title']} (similarity: {results[0]['similarity']:.4f})")
                except Exception as e:
                    print(f"  '{query}' -> Search error: {e}")
        except Exception as e:
            print(f"  Initialization error: {e}")
        print()

def run_evaluation(approaches):
    """평가 실행"""
    if not approaches:
        print("설정된 방식이 없습니다. 먼저 setup을 실행해주세요.")
        return {}

    print("=== 성능 평가 시작 ===\n")

    # Supabase 버전의 평가기는 별도로 구현 필요
    # 여기서는 기본 검색 테스트만 수행
    test_queries = ["닭고기 요리", "볶음밥", "파스타", "매운 요리", "간단한 요리"]

    results = {}
    for approach, name in approaches:
        print(f"{name} 평가 중...")

        total_results = 0
        avg_similarity = 0
        start_time = time.time()

        for query in test_queries:
            try:
                search_results = approach.search_similar_recipes(query, top_k=5)
                total_results += len(search_results)
                if search_results:
                    avg_similarity += sum(r['similarity'] for r in search_results) / len(search_results)
            except Exception as e:
                print(f"  Query '{query}' failed: {e}")

        end_time = time.time()

        results[name] = {
            'total_results': total_results,
            'avg_similarity': avg_similarity / len(test_queries) if test_queries else 0,
            'avg_response_time': (end_time - start_time) / len(test_queries)
        }

        print(f"  - 총 검색 결과: {total_results}")
        print(f"  - 평균 유사도: {results[name]['avg_similarity']:.4f}")
        print(f"  - 평균 응답시간: {results[name]['avg_response_time']:.4f}초\n")

    return results

def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Supabase 기반 임베딩 방식 실험")
    parser.add_argument("--mode", choices=["setup", "eval", "full", "test", "init"], default="test",
                        help="실행 모드: init(테이블 설정 안내), test(빠른테스트), setup(설정만), eval(평가만), full(전체)")

    args = parser.parse_args()

    try:
        if args.mode == "init":
            setup_supabase_tables()

        elif args.mode == "test":
            quick_test()

        elif args.mode == "setup":
            if not check_environment():
                return
            approaches = setup_experiments()

        elif args.mode == "eval":
            if not check_environment():
                return
            # 이미 설정된 방식들로 평가만 실행
            approaches = [
                (TitleBlobApproachSupabase(), "title_blob"),
                (NoTitleBlobApproachSupabase(), "no_title_blob"),
                (LLMPreprocessingApproachSupabase(), "llm_preprocessing")
            ]
            results = run_evaluation(approaches)

        elif args.mode == "full":
            if not check_environment():
                return
            # 전체 실험 실행
            approaches = setup_experiments()
            results = run_evaluation(approaches)

            # 최종 결론
            if results:
                print("\n" + "="*50)
                print("최종 결과 요약:")
                for name, result in results.items():
                    print(f"- {name}: 평균 유사도 {result['avg_similarity']:.4f}, "
                          f"응답시간 {result['avg_response_time']:.4f}초")

    except KeyboardInterrupt:
        print("\n실험이 중단되었습니다.")
    except Exception as e:
        print(f"실험 중 오류 발생: {e}")

if __name__ == "__main__":
    main()