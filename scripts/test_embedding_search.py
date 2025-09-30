#!/usr/bin/env python3
"""
임베딩 기반 메뉴 검색 테스트 스크립트

사용법:
    python scripts/test_embedding_search.py "고기구이"
    python scripts/test_embedding_search.py "해물요리" --top-k 10
    python scripts/test_embedding_search.py "키토 친화적인 음식" --show-details
"""

import asyncio
import argparse
import json
import numpy as np
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
import os

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# OpenAI 임포트
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from infrastructure.database.connection import db_pool

# 환경변수 로드
load_dotenv()


def ensure_openai_client() -> OpenAI:
    if OpenAI is None:
        raise RuntimeError("openai 라이브러리가 설치되어 있지 않습니다. pip install openai 필요")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 환경변수가 필요합니다.")
    return OpenAI(api_key=api_key)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """두 벡터 간의 코사인 유사도 계산"""
    a_np = np.array(a)
    b_np = np.array(b)
    
    dot_product = np.dot(a_np, b_np)
    norm_a = np.linalg.norm(a_np)
    norm_b = np.linalg.norm(b_np)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


async def get_menu_embeddings(supa, model_name: str = "text-embedding-3-small") -> List[Dict[str, Any]]:
    """DB에서 모든 메뉴 임베딩 가져오기"""
    result = supa.client.table('menu_embedding').select(
        'menu_id,embedding,content_blob,model_name'
    ).eq('model_name', model_name).execute()
    
    return result.data


async def get_menu_details(supa, menu_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """메뉴 상세 정보 가져오기 (메뉴명, 키토점수 포함)"""
    # 메뉴 기본 정보
    menu_result = supa.client.table('menu').select('id,name,description').in_('id', menu_ids).execute()
    menu_map = {m['id']: m for m in menu_result.data}
    
    # 키토 점수 정보
    keto_result = supa.client.table('keto_scores').select('menu_id,score').in_('menu_id', menu_ids).execute()
    keto_map = {k['menu_id']: k['score'] for k in keto_result.data}
    
    # 결합
    for menu_id in menu_map:
        menu_map[menu_id]['keto_score'] = keto_map.get(menu_id, 0)
    
    return menu_map


def embed_query(client: OpenAI, query: str, model_name: str) -> List[float]:
    """검색 쿼리를 임베딩으로 변환"""
    print(f"🔄 검색 쿼리 임베딩 중: '{query}'")
    resp = client.embeddings.create(model=model_name, input=[query])
    return resp.data[0].embedding


async def search_menus(
    query: str, 
    top_k: int = 5, 
    model_name: str = "text-embedding-3-small",
    min_similarity: float = 0.0
) -> List[Dict[str, Any]]:
    """임베딩 기반 메뉴 검색"""
    
    # OpenAI 클라이언트 초기화
    openai_client = ensure_openai_client()
    
    # DB 연결
    await db_pool.initialize()
    supa = db_pool.supabase
    
    try:
        # 1. 검색 쿼리 임베딩
        query_embedding = embed_query(openai_client, query, model_name)
        
        # 2. 모든 메뉴 임베딩 가져오기
        print("📊 메뉴 임베딩 데이터 로딩 중...")
        menu_embeddings = await get_menu_embeddings(supa, model_name)
        print(f"✅ {len(menu_embeddings)}개 메뉴 임베딩 로딩 완료")
        
        if not menu_embeddings:
            print("❌ 임베딩 데이터가 없습니다.")
            return []
        
        # 3. 코사인 유사도 계산
        similarities = []
        for menu_emb in menu_embeddings:
            if not menu_emb['embedding']:
                continue
            
            # 임베딩이 문자열인 경우 파싱
            embedding = menu_emb['embedding']
            if isinstance(embedding, str):
                try:
                    # JSON 문자열인 경우
                    embedding = json.loads(embedding)
                except:
                    # 다른 형식인 경우 스킵
                    continue
            
            if not isinstance(embedding, list):
                continue
                
            similarity = cosine_similarity(query_embedding, embedding)
            if similarity >= min_similarity:
                similarities.append({
                    'menu_id': menu_emb['menu_id'],
                    'similarity': similarity,
                    'content_blob': menu_emb['content_blob']
                })
        
        # 4. 유사도 순으로 정렬
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = similarities[:top_k]
        
        # 5. 메뉴 상세 정보 가져오기
        menu_ids = [r['menu_id'] for r in top_results]
        menu_details = await get_menu_details(supa, menu_ids)
        
        # 6. 결과 조합
        final_results = []
        for result in top_results:
            menu_id = result['menu_id']
            if menu_id in menu_details:
                menu_info = menu_details[menu_id]
                final_results.append({
                    'menu_id': menu_id,
                    'name': menu_info['name'],
                    'description': menu_info.get('description', ''),
                    'keto_score': menu_info['keto_score'],
                    'similarity': result['similarity'],
                    'content_blob': result['content_blob']
                })
        
        return final_results
        
    finally:
        await db_pool.close()


def print_search_results(results: List[Dict[str, Any]], query: str, show_details: bool = False):
    """검색 결과를 예쁘게 출력"""
    print(f"\n🔍 검색 쿼리: '{query}'")
    print(f"📊 검색 결과: {len(results)}개")
    print("=" * 80)
    
    if not results:
        print("❌ 검색 결과가 없습니다.")
        return
    
    for i, result in enumerate(results, 1):
        similarity_pct = result['similarity'] * 100
        
        print(f"\n[{i}] {result['name']}")
        print(f"    🎯 유사도: {similarity_pct:.1f}%")
        print(f"    🥑 키토점수: {result['keto_score']}점")
        
        if show_details:
            if result['content_blob']:
                try:
                    blob = json.loads(result['content_blob'])
                    if blob.get('keywords'):
                        print(f"    🏷️ 키워드: {', '.join(blob['keywords'])}")
                    if blob.get('embedding_text'):
                        print(f"    📝 임베딩 텍스트: '{blob['embedding_text']}'")
                except:
                    pass
            
            if result['description']:
                desc = result['description'][:100] + '...' if len(result['description']) > 100 else result['description']
                print(f"    📄 설명: {desc}")


async def main():
    parser = argparse.ArgumentParser(description="임베딩 기반 메뉴 검색")
    parser.add_argument("query", help="검색할 쿼리 (예: '고기구이', '해물요리')")
    parser.add_argument("--top-k", type=int, default=10, help="상위 몇 개 결과를 보여줄지 (기본: 10)")
    parser.add_argument("--model-name", default="text-embedding-3-small", help="사용할 임베딩 모델")
    parser.add_argument("--min-similarity", type=float, default=0.0, help="최소 유사도 임계값 (0.0-1.0)")
    parser.add_argument("--show-details", action="store_true", help="상세 정보 표시")
    
    args = parser.parse_args()
    
    try:
        results = await search_menus(
            query=args.query,
            top_k=args.top_k,
            model_name=args.model_name,
            min_similarity=args.min_similarity
        )
        
        print_search_results(results, args.query, args.show_details)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
