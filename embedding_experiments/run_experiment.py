"""
3가지 임베딩 방식 실험 실행 스크립트
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

from approach1_title_blob.approach1 import TitleBlobApproach
from approach2_no_title_blob.approach2 import NoTitleBlobApproach
from approach3_llm_preprocessing.approach3 import LLMPreprocessingApproach
from shared.evaluation import EmbeddingEvaluator
import time

def setup_experiments():
    """실험 환경 설정"""
    print("=== 임베딩 방식별 실험 시작 ===\n")

    # 1. Approach 1: Title + Blob
    print("1. Setting up Approach 1 (Title + Blob)...")
    approach1 = TitleBlobApproach()
    approach1.process_recipes_from_db()
    print("Approach 1 setup complete!\n")

    # 2. Approach 2: No Title + Blob
    print("2. Setting up Approach 2 (No Title + Blob)...")
    approach2 = NoTitleBlobApproach()
    approach2.process_recipes_from_db()
    print("Approach 2 setup complete!\n")

    # 3. Approach 3: LLM Preprocessing
    print("3. Setting up Approach 3 (LLM Preprocessing)...")
    # OpenAI API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Warning: OPENAI_API_KEY not found. Using basic preprocessing instead.")

    approach3 = LLMPreprocessingApproach(api_key)
    if approach3.use_llm:
        approach3.process_recipes_from_db(limit=30)  # LLM 사용으로 적은 수량
    else:
        approach3.process_recipes_from_db(limit=50)  # 기본 전처리로 더 많이
    print("Approach 3 setup complete!\n")

    return approach1, approach2, approach3

def run_evaluation(approach1, approach2, approach3):
    """평가 실행"""
    print("=== 성능 평가 시작 ===\n")

    evaluator = EmbeddingEvaluator()

    # 각 방식별 평가
    approaches = [
        (approach1, "title_blob"),
        (approach2, "no_title_blob"),
        (approach3, "llm_preprocessing")
    ]

    results = evaluator.compare_approaches(approaches)

    # 결과 출력
    print("\n=== 평가 결과 ===")
    for name, result in results.items():
        print(f"\n{name}:")
        print(f"  MRR: {result.mrr:.4f}")
        print(f"  MAP: {result.map_score:.4f}")
        print(f"  P@5: {result.precision_at_k.get(5, 0):.4f}")
        print(f"  R@5: {result.recall_at_k.get(5, 0):.4f}")
        print(f"  평균 응답시간: {result.avg_response_time:.4f}초")

    # 리포트 생성
    evaluator.generate_report(results)
    evaluator.plot_comparison(results)

    return results

def quick_test():
    """빠른 테스트 - 각 방식이 제대로 동작하는지 확인"""
    print("=== 빠른 동작 테스트 ===\n")

    # 각 방식 초기화
    approach1 = TitleBlobApproach()
    approach2 = NoTitleBlobApproach()
    approach3 = LLMPreprocessingApproach()

    test_queries = ["닭고기 요리", "볶음밥", "간단한 요리"]

    for i, approach in enumerate([approach1, approach2, approach3], 1):
        print(f"Approach {i} 테스트:")
        for query in test_queries:
            try:
                results = approach.search_similar_recipes(query, top_k=3)
                print(f"  '{query}' -> {len(results)} results found")
                if results:
                    print(f"    Top result: {results[0]['title']} (similarity: {results[0]['similarity']:.4f})")
            except Exception as e:
                print(f"  '{query}' -> Error: {e}")
        print()

def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="임베딩 방식 실험")
    parser.add_argument("--mode", choices=["setup", "eval", "full", "test"], default="full",
                        help="실행 모드: setup(설정만), eval(평가만), full(전체), test(빠른테스트)")

    args = parser.parse_args()

    try:
        if args.mode == "test":
            quick_test()

        elif args.mode == "setup":
            setup_experiments()

        elif args.mode == "eval":
            # 이미 설정된 방식들로 평가만 실행
            approach1 = TitleBlobApproach()
            approach2 = NoTitleBlobApproach()
            approach3 = LLMPreprocessingApproach()
            run_evaluation(approach1, approach2, approach3)

        elif args.mode == "full":
            # 전체 실험 실행
            approach1, approach2, approach3 = setup_experiments()
            results = run_evaluation(approach1, approach2, approach3)

            # 최종 결론
            print("\n" + "="*50)
            print("최종 결론:")

            best_overall = max(results.values(), key=lambda x: (x.mrr + x.map_score) / 2)
            fastest = min(results.values(), key=lambda x: x.avg_response_time)

            print(f"- 전반적으로 가장 우수한 방식: {best_overall.approach_name}")
            print(f"- 가장 빠른 방식: {fastest.approach_name}")

            if best_overall.approach_name != fastest.approach_name:
                print("- 성능과 속도 중 우선순위에 따라 선택하세요.")
            else:
                print("- 이 방식이 성능과 속도 모두 우수합니다.")

    except KeyboardInterrupt:
        print("\n실험이 중단되었습니다.")
    except Exception as e:
        print(f"실험 중 오류 발생: {e}")

if __name__ == "__main__":
    main()