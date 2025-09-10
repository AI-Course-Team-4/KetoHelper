"""
검색 평가 스크립트

- 테스트셋: tests/testset.json
- 지표: Precision@1/3, MRR, 결과 다양성(레스토랑 다양성), 평균 응답시간
- 대상: 벡터, 키워드, 하이브리드
- 하이브리드 그리드서치: rrf_k, 가중치
"""

import os
import time
import json
from typing import List, Dict, Any, Tuple
from statistics import mean
from dotenv import load_dotenv
from loguru import logger

from src.vector_searcher import VectorSearcher
from src.keyword_searcher import KeywordSearcher
from src.hybrid_searcher import HybridSearcher, HybridSearchConfig


def load_testset(path: str = "tests/testset.json") -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def precision_at_k(results: List[Dict[str, Any]], must: List[str], should: List[str], k: int = 3) -> float:
    if not results:
        return 0.0
    top_k = results[:k]
    hits = 0
    for item in top_k:
        text = f"{item.get('menu_name','')} {item.get('combined_text','')} {item.get('short_description','')}".lower()
        # must 모두 만족
        if all(m.lower() in text for m in must):
            hits += 1
        else:
            # must 없으면 should 중 하나라도 만족
            if not must and any(s.lower() in text for s in should):
                hits += 1
    return hits / k


def mrr(results: List[Dict[str, Any]], must: List[str], should: List[str]) -> float:
    if not results:
        return 0.0
    for rank, item in enumerate(results, 1):
        text = f"{item.get('menu_name','')} {item.get('combined_text','')} {item.get('short_description','')}".lower()
        if all(m.lower() in text for m in must) or (not must and any(s.lower() in text for s in should)):
            return 1.0 / rank
    return 0.0


def diversity(restaurants: List[str]) -> float:
    if not restaurants:
        return 0.0
    unique = len(set(restaurants))
    return unique / len(restaurants)


def evaluate_method(name: str, search_fn, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
    p1_list, p3_list, mrr_list, time_list, diversity_list = [], [], [], [], []
    for q in queries:
        query = q["query"]
        must = q.get("must", [])
        should = q.get("should", [])
        start = time.time()
        results = search_fn(query)
        elapsed = time.time() - start
        time_list.append(elapsed)
        
        p1_list.append(precision_at_k(results, must, should, k=1))
        p3_list.append(precision_at_k(results, must, should, k=3))
        mrr_list.append(mrr(results, must, should))
        diversity_list.append(diversity([r.get('restaurant_name','') for r in results[:5]]))
    return {
        "name": name,
        "P@1": round(mean(p1_list), 3),
        "P@3": round(mean(p3_list), 3),
        "MRR": round(mean(mrr_list), 3),
        "Diversity@5": round(mean(diversity_list), 3),
        "Latency(s)": round(mean(time_list), 3)
    }


def main():
    load_dotenv()
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not all([supabase_url, supabase_key, openai_api_key]):
        print("환경변수 부족")
        return

    testset = load_testset()

    # 검색기 준비
    vector = VectorSearcher()
    keyword = KeywordSearcher(supabase_url, supabase_key)

    def vector_fn(q: str):
        return vector.search_similar_menus(q, match_count=10, match_threshold=0.1)

    def keyword_fn(q: str):
        return keyword.search_menus(q, limit=10)

    # 그리드 정의
    ks = [20, 60, 100]
    weights = [(0.6, 0.4), (0.7, 0.3), (0.5, 0.5)]

    # 단일 방법 평가
    vec_report = evaluate_method("vector", vector_fn, testset)
    key_report = evaluate_method("keyword", keyword_fn, testset)

    print("\n=== 단일 방법 성능 ===")
    print(vec_report)
    print(key_report)

    # 하이브리드 평가 그리드서치
    print("\n=== 하이브리드 그리드서치 ===")
    best = None
    for k in ks:
        for vw, kw in weights:
            config = HybridSearchConfig(
                rrf_k=k,
                vector_weight=vw,
                keyword_weight=kw,
                final_results_count=10
            )
            hybrid = HybridSearcher(supabase_url, supabase_key, openai_api_key, config)
            def hybrid_fn(q: str):
                rows = hybrid.search(q)
                # search() 결과는 {'data':..., 'hybrid_score':...} 구조 → data만 추출
                return [r['data'] for r in rows]
            report = evaluate_method(f"hybrid(k={k},vw={vw})", hybrid_fn, testset)
            print(report)
            if best is None or report["P@3"] > best["P@3"] or (report["P@3"] == best["P@3"] and report["P@1"] > best["P@1"]):
                best = report

    print("\n=== 베스트 설정 (P@3 기준) ===")
    print(best)


if __name__ == "__main__":
    main()
