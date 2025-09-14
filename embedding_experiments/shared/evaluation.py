"""
임베딩 방식별 성능 평가 프레임워크
"""

import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Tuple
import random
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns

@dataclass
class EvaluationResult:
    """평가 결과"""
    approach_name: str
    precision_at_k: Dict[int, float]  # P@K
    recall_at_k: Dict[int, float]     # R@K
    mrr: float                        # Mean Reciprocal Rank
    map_score: float                  # Mean Average Precision
    avg_response_time: float          # 평균 응답 시간

class EmbeddingEvaluator:
    """임베딩 방식 평가기"""

    def __init__(self, db_path: str = "embeddings_comparison.db"):
        self.db_path = db_path
        self.test_queries = self._generate_test_queries()
        self.golden_sets = {}

    def _generate_test_queries(self) -> List[Dict[str, Any]]:
        """30개의 테스트 쿼리 생성"""
        queries = [
            # 재료 기반 쿼리
            {"query": "닭고기 요리", "type": "ingredient", "expected_keywords": ["닭", "치킨"]},
            {"query": "소고기 스테이크", "type": "ingredient", "expected_keywords": ["소고기", "스테이크"]},
            {"query": "돼지고기 김치찜", "type": "ingredient", "expected_keywords": ["돼지고기", "김치"]},
            {"query": "새우 볶음", "type": "ingredient", "expected_keywords": ["새우", "볶음"]},
            {"query": "감자 요리", "type": "ingredient", "expected_keywords": ["감자"]},
            {"query": "고구마 맛탕", "type": "ingredient", "expected_keywords": ["고구마", "맛탕"]},
            {"query": "버섯 볶음", "type": "ingredient", "expected_keywords": ["버섯", "볶음"]},
            {"query": "두부 조림", "type": "ingredient", "expected_keywords": ["두부", "조림"]},
            {"query": "계란 요리", "type": "ingredient", "expected_keywords": ["계란", "달걀"]},
            {"query": "치즈 요리", "type": "ingredient", "expected_keywords": ["치즈"]},

            # 요리 종류/방법 기반 쿼리
            {"query": "볶음밥", "type": "dish", "expected_keywords": ["볶음밥", "볶음"]},
            {"query": "찌개", "type": "dish", "expected_keywords": ["찌개", "국"]},
            {"query": "국물 요리", "type": "dish", "expected_keywords": ["국", "찌개", "탕"]},
            {"query": "샐러드", "type": "dish", "expected_keywords": ["샐러드", "상추"]},
            {"query": "파스타", "type": "dish", "expected_keywords": ["파스타", "면"]},
            {"query": "디저트", "type": "dish", "expected_keywords": ["케이크", "쿠키", "디저트"]},
            {"query": "구이 요리", "type": "cooking_method", "expected_keywords": ["구이", "굽"]},
            {"query": "튀김 요리", "type": "cooking_method", "expected_keywords": ["튀김", "튀기"]},
            {"query": "찜 요리", "type": "cooking_method", "expected_keywords": ["찜", "찌"]},
            {"query": "볶음 요리", "type": "cooking_method", "expected_keywords": ["볶음", "볶"]},

            # 특성 기반 쿼리
            {"query": "매운 요리", "type": "flavor", "expected_keywords": ["매운", "고추", "청양고추"]},
            {"query": "달콤한 음식", "type": "flavor", "expected_keywords": ["달콤", "설탕", "꿀"]},
            {"query": "간단한 요리", "type": "difficulty", "expected_keywords": ["간단", "쉬운"]},
            {"query": "한식", "type": "cuisine", "expected_keywords": ["김치", "된장", "고추장"]},
            {"query": "양식", "type": "cuisine", "expected_keywords": ["파스타", "스테이크", "샐러드"]},

            # 상황별 쿼리
            {"query": "아침 식사", "type": "meal", "expected_keywords": ["토스트", "계란", "시리얼"]},
            {"query": "저녁 메뉴", "type": "meal", "expected_keywords": ["밥", "국", "찌개"]},
            {"query": "다이어트 음식", "type": "health", "expected_keywords": ["샐러드", "닭가슴살", "두부"]},
            {"query": "아이 간식", "type": "target", "expected_keywords": ["과자", "우유", "과일"]},
            {"query": "혼밥 메뉴", "type": "situation", "expected_keywords": ["1인분", "간단"]}
        ]
        return queries

    def create_golden_set(self, approach_name: str, table_name: str, size: int = 50) -> Dict[str, List[str]]:
        """각 방식별 골든셋 생성"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 해당 테이블에서 랜덤 샘플링
            cursor.execute(f'''
                SELECT recipe_id, title, processed_content
                FROM {table_name}
                ORDER BY RANDOM()
                LIMIT {size}
            ''')

            golden_set = {}
            for recipe_id, title, processed_content in cursor.fetchall():
                # 각 레시피에 대해 관련 쿼리들 매핑
                relevant_queries = []
                title_lower = title.lower() if title else ""
                content_lower = processed_content.lower() if processed_content else ""

                for query_data in self.test_queries:
                    query = query_data["query"]
                    keywords = query_data["expected_keywords"]

                    # 키워드 매칭으로 관련성 판단
                    is_relevant = False
                    for keyword in keywords:
                        if keyword.lower() in title_lower or keyword.lower() in content_lower:
                            is_relevant = True
                            break

                    if is_relevant:
                        relevant_queries.append(query)

                if relevant_queries:
                    golden_set[recipe_id] = relevant_queries

            conn.close()
            return golden_set

        except Exception as e:
            print(f"Error creating golden set for {approach_name}: {e}")
            return {}

    def evaluate_approach(self, approach, approach_name: str, k_values: List[int] = [1, 3, 5, 10]) -> EvaluationResult:
        """특정 방식의 성능 평가"""
        import time

        precision_at_k = {k: [] for k in k_values}
        recall_at_k = {k: [] for k in k_values}
        reciprocal_ranks = []
        average_precisions = []
        response_times = []

        # 골든셋이 없으면 생성
        if approach_name not in self.golden_sets:
            self.golden_sets[approach_name] = self.create_golden_set(approach_name, approach.table_name)

        golden_set = self.golden_sets[approach_name]

        for query_data in self.test_queries:
            query = query_data["query"]

            # 검색 시간 측정
            start_time = time.time()
            search_results = approach.search_similar_recipes(query, top_k=max(k_values))
            end_time = time.time()

            response_times.append(end_time - start_time)

            # 관련 문서 찾기
            relevant_docs = set()
            for recipe_id, queries in golden_set.items():
                if query in queries:
                    relevant_docs.add(recipe_id)

            if not relevant_docs:
                continue

            # 검색 결과에서 관련 문서 찾기
            retrieved_docs = [result['recipe_id'] for result in search_results]

            # Precision@K, Recall@K 계산
            for k in k_values:
                retrieved_at_k = set(retrieved_docs[:k])
                relevant_retrieved_at_k = retrieved_at_k & relevant_docs

                precision = len(relevant_retrieved_at_k) / k if k > 0 else 0
                recall = len(relevant_retrieved_at_k) / len(relevant_docs) if len(relevant_docs) > 0 else 0

                precision_at_k[k].append(precision)
                recall_at_k[k].append(recall)

            # MRR 계산
            for i, doc_id in enumerate(retrieved_docs):
                if doc_id in relevant_docs:
                    reciprocal_ranks.append(1.0 / (i + 1))
                    break
            else:
                reciprocal_ranks.append(0.0)

            # MAP 계산
            relevant_retrieved = []
            precision_sum = 0
            for i, doc_id in enumerate(retrieved_docs):
                if doc_id in relevant_docs:
                    relevant_retrieved.append(i + 1)
                    precision_sum += len(relevant_retrieved) / (i + 1)

            if relevant_retrieved:
                avg_precision = precision_sum / len(relevant_docs)
            else:
                avg_precision = 0.0
            average_precisions.append(avg_precision)

        # 평균 계산
        avg_precision_at_k = {k: np.mean(precision_at_k[k]) for k in k_values}
        avg_recall_at_k = {k: np.mean(recall_at_k[k]) for k in k_values}
        mrr = np.mean(reciprocal_ranks)
        map_score = np.mean(average_precisions)
        avg_response_time = np.mean(response_times)

        return EvaluationResult(
            approach_name=approach_name,
            precision_at_k=avg_precision_at_k,
            recall_at_k=avg_recall_at_k,
            mrr=mrr,
            map_score=map_score,
            avg_response_time=avg_response_time
        )

    def compare_approaches(self, approaches: List[Tuple[Any, str]]) -> Dict[str, EvaluationResult]:
        """여러 방식 비교"""
        results = {}

        for approach, name in approaches:
            print(f"Evaluating {name}...")
            result = self.evaluate_approach(approach, name)
            results[name] = result
            print(f"Completed evaluation for {name}")

        return results

    def generate_report(self, results: Dict[str, EvaluationResult], output_path: str = "embedding_experiments/evaluation_report.txt"):
        """평가 결과 리포트 생성"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== 임베딩 방식별 성능 비교 결과 ===\n\n")

            # 전체 요약
            f.write("1. 전체 성능 요약\n")
            f.write("-" * 50 + "\n")

            for name, result in results.items():
                f.write(f"\n{name}:\n")
                f.write(f"  - MRR: {result.mrr:.4f}\n")
                f.write(f"  - MAP: {result.map_score:.4f}\n")
                f.write(f"  - P@5: {result.precision_at_k.get(5, 0):.4f}\n")
                f.write(f"  - R@5: {result.recall_at_k.get(5, 0):.4f}\n")
                f.write(f"  - 평균 응답시간: {result.avg_response_time:.4f}초\n")

            # 상세 성능
            f.write("\n\n2. 상세 성능 지표\n")
            f.write("-" * 50 + "\n")

            for name, result in results.items():
                f.write(f"\n=== {name} ===\n")
                f.write("Precision@K:\n")
                for k, precision in result.precision_at_k.items():
                    f.write(f"  P@{k}: {precision:.4f}\n")

                f.write("Recall@K:\n")
                for k, recall in result.recall_at_k.items():
                    f.write(f"  R@{k}: {recall:.4f}\n")

            # 결론
            f.write("\n\n3. 결론 및 권장사항\n")
            f.write("-" * 50 + "\n")

            # 최고 성능 방식 찾기
            best_mrr = max(results.values(), key=lambda x: x.mrr)
            best_map = max(results.values(), key=lambda x: x.map_score)
            fastest = min(results.values(), key=lambda x: x.avg_response_time)

            f.write(f"- 최고 MRR: {best_mrr.approach_name} ({best_mrr.mrr:.4f})\n")
            f.write(f"- 최고 MAP: {best_map.approach_name} ({best_map.map_score:.4f})\n")
            f.write(f"- 가장 빠른 응답: {fastest.approach_name} ({fastest.avg_response_time:.4f}초)\n")

        print(f"평가 리포트가 {output_path}에 저장되었습니다.")

    def plot_comparison(self, results: Dict[str, EvaluationResult], output_path: str = "embedding_experiments/comparison_plot.png"):
        """성능 비교 그래프 생성"""
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.family'] = 'DejaVu Sans'

            fig, axes = plt.subplots(2, 2, figsize=(15, 10))

            approaches = list(results.keys())

            # MRR 비교
            mrr_scores = [results[name].mrr for name in approaches]
            axes[0, 0].bar(approaches, mrr_scores)
            axes[0, 0].set_title('MRR Comparison')
            axes[0, 0].set_ylabel('MRR Score')

            # MAP 비교
            map_scores = [results[name].map_score for name in approaches]
            axes[0, 1].bar(approaches, map_scores)
            axes[0, 1].set_title('MAP Comparison')
            axes[0, 1].set_ylabel('MAP Score')

            # Precision@K 비교
            k_values = [1, 3, 5, 10]
            x = np.arange(len(k_values))
            width = 0.25

            for i, name in enumerate(approaches):
                precision_values = [results[name].precision_at_k[k] for k in k_values]
                axes[1, 0].bar(x + i * width, precision_values, width, label=name)

            axes[1, 0].set_title('Precision@K Comparison')
            axes[1, 0].set_ylabel('Precision Score')
            axes[1, 0].set_xticks(x + width)
            axes[1, 0].set_xticklabels([f'P@{k}' for k in k_values])
            axes[1, 0].legend()

            # 응답시간 비교
            response_times = [results[name].avg_response_time for name in approaches]
            axes[1, 1].bar(approaches, response_times)
            axes[1, 1].set_title('Average Response Time')
            axes[1, 1].set_ylabel('Time (seconds)')

            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            print(f"비교 그래프가 {output_path}에 저장되었습니다.")

        except Exception as e:
            print(f"그래프 생성 실패: {e}")

if __name__ == "__main__":
    evaluator = EmbeddingEvaluator()
    print("Evaluation framework created!")
    print(f"Generated {len(evaluator.test_queries)} test queries")