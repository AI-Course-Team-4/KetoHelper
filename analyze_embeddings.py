#!/usr/bin/env python3
"""
임베딩 품질 분석 스크립트
왜 해산물 검색에서 교자만두가 높은 유사도를 보이는지 분석합니다.
"""

import os
import sys
import numpy as np
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def calculate_cosine_similarity(vec1, vec2):
    """코사인 유사도 계산"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0
    
    return dot_product / (norm1 * norm2)

def analyze_search_results():
    """검색 결과 상세 분석"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        from src.database import DatabaseManager
        from src.embedding import EmbeddingGenerator
        
        print("🔍 임베딩 품질 분석 시작...")
        db = DatabaseManager()
        embedding_gen = EmbeddingGenerator(db)
        
        # 분석할 검색어들
        test_queries = [
            "해산물",
            "교자만두", 
            "가츠산도",
            "얼큰해물칼국수"
        ]
        
        query_embeddings = {}
        
        # 각 검색어의 임베딩 생성
        print("\n📊 검색어별 임베딩 생성 중...")
        for query in test_queries:
            embedding = embedding_gen.generate_embedding(query)
            query_embeddings[query] = embedding
            print(f"✅ '{query}' 임베딩 생성 완료")
        
        # 메뉴 데이터 로드
        print("\n📊 메뉴 데이터 로드 중...")
        result = db.client.table('menus')\
            .select('*, restaurants(*)')\
            .not_.is_('embedding', 'null')\
            .execute()
        
        print(f"✅ {len(result.data)}개 메뉴 로드 완료")
        
        # 특정 메뉴들 찾기
        target_menus = {}
        for menu in result.data:
            menu_name = menu.get('name', '')
            if '교자만두' in menu_name:
                target_menus['교자만두'] = menu
            elif '가츠산도' in menu_name:
                target_menus['가츠산도'] = menu
            elif '해물칼국수' in menu_name:
                target_menus['얼큰해물칼국수'] = menu
        
        print(f"\n🎯 분석 대상 메뉴: {list(target_menus.keys())}")
        
        # 상세 분석
        print("\n" + "="*80)
        print("🔬 상세 유사도 분석")
        print("="*80)
        
        for query_name, query_embedding in query_embeddings.items():
            print(f"\n🔍 검색어: '{query_name}'")
            print("-" * 50)
            
            menu_similarities = []
            
            for menu_name, menu in target_menus.items():
                menu_embedding = menu.get('embedding')
                if menu_embedding:
                    try:
                        # 임베딩 변환
                        if isinstance(menu_embedding, str):
                            menu_embedding = menu_embedding.strip('[]').split(',')
                            menu_embedding = [float(x.strip()) for x in menu_embedding]
                        elif isinstance(menu_embedding, list):
                            menu_embedding = [float(x) for x in menu_embedding]
                        
                        # 유사도 계산
                        similarity = calculate_cosine_similarity(query_embedding, menu_embedding)
                        menu_similarities.append((similarity, menu_name, menu))
                        
                    except Exception as e:
                        print(f"⚠️ {menu_name} 임베딩 변환 오류: {e}")
            
            # 유사도 순 정렬
            menu_similarities.sort(key=lambda x: x[0], reverse=True)
            
            # 결과 출력
            for i, (similarity, menu_name, menu) in enumerate(menu_similarities, 1):
                restaurant = menu.get('restaurants', {}) or {}
                print(f"  {i}. {menu_name}")
                print(f"     🎯 유사도: {similarity:.4f} ({similarity*100:.2f}%)")
                print(f"     📄 메뉴텍스트: {menu.get('menu_text', 'N/A')}")
                print()
        
        # 크로스 분석 - 서로 다른 검색어들 간의 유사도
        print("\n" + "="*80)
        print("🔄 검색어 간 유사도 분석")
        print("="*80)
        
        query_names = list(query_embeddings.keys())
        for i, query1 in enumerate(query_names):
            for query2 in query_names[i+1:]:
                similarity = calculate_cosine_similarity(
                    query_embeddings[query1], 
                    query_embeddings[query2]
                )
                print(f"'{query1}' vs '{query2}': {similarity:.4f} ({similarity*100:.2f}%)")
        
        # 임베딩 차원 분석
        print(f"\n📐 임베딩 차원 정보:")
        for query, embedding in query_embeddings.items():
            print(f"  {query}: {len(embedding)}차원")
            print(f"    평균값: {np.mean(embedding):.6f}")
            print(f"    표준편차: {np.std(embedding):.6f}")
            print(f"    최대값: {np.max(embedding):.6f}")
            print(f"    최소값: {np.min(embedding):.6f}")
            print()
            
    except Exception as e:
        print(f"❌ 분석 중 오류: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("🔬 임베딩 품질 분석 도구")
    print("=" * 50)
    analyze_search_results()

if __name__ == "__main__":
    main()
