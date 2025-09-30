"""
개선된 키워드 추출을 사용한 메뉴 임베딩 생성 스크립트
- 음식 도메인 특화 키워드 사전 사용
- keto_scores.score >= 5인 메뉴만 대상
- content_blob: {"name": "메뉴명", "keywords": ["키워드1", "키워드2"]}
- 임베딩: "메뉴명 키워드1 키워드2"
"""

import os
import sys
import asyncio
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv()

import argparse
from infrastructure.database.connection import db_pool

# OpenAI 임베딩
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


@dataclass
class EmbeddingConfig:
    model_name: str = "text-embedding-3-small"
    algorithm_version: str = "RAG-v1.0"
    dimension: int = 1536
    batch_size: int = 100
    limit: int = 1000
    offset: int = 0


# 대폭 확장된 음식 도메인 키워드 사전
KETO_FRIENDLY_KEYWORDS = {
    # 생선/해산물 (확장)
    '회': {'weight': 25, 'confidence': 0.9},
    '생선회': {'weight': 30, 'confidence': 0.95},
    '연어': {'weight': 25, 'confidence': 0.9},
    '참치': {'weight': 22, 'confidence': 0.85},
    '굴비': {'weight': 20, 'confidence': 0.8},
    '고등어': {'weight': 20, 'confidence': 0.8},
    '삼치': {'weight': 20, 'confidence': 0.8},
    '갈치': {'weight': 20, 'confidence': 0.8},
    '조기': {'weight': 18, 'confidence': 0.8},
    '북어': {'weight': 18, 'confidence': 0.8},
    '생선': {'weight': 18, 'confidence': 0.75},
    '새우': {'weight': 18, 'confidence': 0.8},
    # '게': {'weight': 18, 'confidence': 0.8},  # 제거 (카라아게에서 잘못 매칭)
    '낙지': {'weight': 15, 'confidence': 0.75},
    '오징어': {'weight': 15, 'confidence': 0.75},
    '전복': {'weight': 20, 'confidence': 0.8},
    '조개': {'weight': 15, 'confidence': 0.75},
    # '굴': {'weight': 15, 'confidence': 0.8},  # 제거 (굴비와 중복)
    '홍합': {'weight': 15, 'confidence': 0.75},
    '해물': {'weight': 15, 'confidence': 0.7},
    '꼼장어': {'weight': 18, 'confidence': 0.8},
    
    # 육류 (대폭 확장)
    '닭': {'weight': 18, 'confidence': 0.8},
    '치킨': {'weight': 18, 'confidence': 0.8},
    '스테이크': {'weight': 25, 'confidence': 0.9},
    '베이컨': {'weight': 20, 'confidence': 0.85},
    '삼겹살': {'weight': 22, 'confidence': 0.85},
    '갈비': {'weight': 20, 'confidence': 0.8},
    '소고기': {'weight': 22, 'confidence': 0.85},
    '돼지고기': {'weight': 20, 'confidence': 0.8},
    '등심': {'weight': 22, 'confidence': 0.85},
    '안심': {'weight': 22, 'confidence': 0.85},
    '채끝': {'weight': 20, 'confidence': 0.8},
    '목살': {'weight': 20, 'confidence': 0.8},
    '항정살': {'weight': 22, 'confidence': 0.8},
    '소시지': {'weight': 18, 'confidence': 0.75},
    '햄': {'weight': 15, 'confidence': 0.7},
    '제육': {'weight': 18, 'confidence': 0.8},
    '육회': {'weight': 25, 'confidence': 0.9},
    '구이': {'weight': 15, 'confidence': 0.7},
    '찜': {'weight': 12, 'confidence': 0.65},
    '볶음': {'weight': 10, 'confidence': 0.6},
    
    # 계란/유제품
    '계란': {'weight': 18, 'confidence': 0.8},
    '달걀': {'weight': 18, 'confidence': 0.8},
    '치즈': {'weight': 15, 'confidence': 0.8},
    '모짜렐라': {'weight': 15, 'confidence': 0.8},
    '버터': {'weight': 20, 'confidence': 0.8},
    
    # 야채/기타 (확장)
    '샐러드': {'weight': 20, 'confidence': 0.85},
    '양배추': {'weight': 15, 'confidence': 0.8},
    '브로콜리': {'weight': 15, 'confidence': 0.8},
    '시금치': {'weight': 12, 'confidence': 0.75},
    '버섯': {'weight': 12, 'confidence': 0.75},
    '표고버섯': {'weight': 12, 'confidence': 0.75},
    '느타리버섯': {'weight': 12, 'confidence': 0.75},
    '아보카도': {'weight': 25, 'confidence': 0.9},
    '견과류': {'weight': 18, 'confidence': 0.8},
    '올리브': {'weight': 15, 'confidence': 0.8},
    '김치': {'weight': 10, 'confidence': 0.7},
    '나물': {'weight': 8, 'confidence': 0.65},
    '콩나물': {'weight': 8, 'confidence': 0.65},
    
    # 두부류 (추가)
    '두부': {'weight': 12, 'confidence': 0.75},
    '순두부': {'weight': 12, 'confidence': 0.75},
    '손두부': {'weight': 12, 'confidence': 0.75},
    
    # 키토 특화
    '키토': {'weight': 30, 'confidence': 0.95},
    '저탄수': {'weight': 25, 'confidence': 0.9},
    '무탄수': {'weight': 30, 'confidence': 0.95},
}

HIGH_CARB_KEYWORDS = {
    # 주식류
    '밥': {'weight': -60, 'confidence': 0.9},
    '쌀': {'weight': -55, 'confidence': 0.85},
    '현미': {'weight': -50, 'confidence': 0.8},
    '잡곡': {'weight': -45, 'confidence': 0.8},
    
    # 면류
    '면': {'weight': -55, 'confidence': 0.85},
    '국수': {'weight': -60, 'confidence': 0.9},
    '라면': {'weight': -65, 'confidence': 0.9},
    '냉면': {'weight': -60, 'confidence': 0.9},
    '비빔냉면': {'weight': -60, 'confidence': 0.9},
    '파스타': {'weight': -60, 'confidence': 0.9},
    '우동': {'weight': -60, 'confidence': 0.9},
    '소바': {'weight': -55, 'confidence': 0.85},
    
    # 빵/떡류
    '빵': {'weight': -55, 'confidence': 0.85},
    '샌드위치': {'weight': -55, 'confidence': 0.85},
    '떡': {'weight': -65, 'confidence': 0.9},
    '토스트': {'weight': -50, 'confidence': 0.8},
    '베이글': {'weight': -55, 'confidence': 0.85},
    
    # 초밥/김밥
    '니기리': {'weight': -70, 'confidence': 0.9},
    '초밥': {'weight': -65, 'confidence': 0.9},
    '김밥': {'weight': -60, 'confidence': 0.9},
    
    # 기타 고탄수화물
    '피자': {'weight': -65, 'confidence': 0.9},
    '감자': {'weight': -45, 'confidence': 0.8},
    '고구마': {'weight': -40, 'confidence': 0.8},
}


def extract_keywords_improved(text: str) -> List[Dict[str, Any]]:
    """개선된 키워드 추출 - 긴 키워드 우선, 위치 겹침 방지"""
    text = text.lower().strip()
    found_keywords = []
    
    # 모든 키워드를 하나의 딕셔너리로 합치고 길이순 정렬
    all_keywords = {}
    for keyword, info in KETO_FRIENDLY_KEYWORDS.items():
        all_keywords[keyword] = {'type': 'keto_friendly', 'weight': info['weight'], 'confidence': info['confidence']}
    for keyword, info in HIGH_CARB_KEYWORDS.items():
        all_keywords[keyword] = {'type': 'high_carb', 'weight': info['weight'], 'confidence': info['confidence']}
    
    # 키워드를 길이순으로 정렬 (긴 것부터)
    sorted_keywords = sorted(all_keywords.keys(), key=len, reverse=True)
    
    used_positions = set()  # 이미 매칭된 위치들
    
    for keyword in sorted_keywords:
        start_pos = 0
        while True:
            pos = text.find(keyword, start_pos)
            if pos == -1:
                break
            
            # 이미 사용된 위치와 겹치는지 확인
            keyword_positions = set(range(pos, pos + len(keyword)))
            if not keyword_positions.intersection(used_positions):
                info = all_keywords[keyword]
                found_keywords.append({
                    'keyword': keyword,
                    'type': info['type'],
                    'weight': info['weight'],
                    'confidence': info['confidence']
                })
                used_positions.update(keyword_positions)
                break  # 같은 키워드는 한 번만
            
            start_pos = pos + 1
    
    return found_keywords


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def create_content_blob(name: str, keywords: List[str]) -> str:
    """메뉴명 + 키워드로 content_blob JSON 생성 (구조화된 정보 + 임베딩 텍스트)"""
    unique_keywords = []
    seen = set()
    for k in keywords:
        if k and k not in seen:
            seen.add(k)
            unique_keywords.append(k)
    
    # 임베딩 텍스트 생성
    if unique_keywords:
        embedding_text = f"{name} {' '.join(unique_keywords)}"
    else:
        embedding_text = name
    
    blob_obj = {
        "name": name,
        "keywords": unique_keywords,
        "embedding_text": embedding_text
    }
    
    return json.dumps(blob_obj, ensure_ascii=False, separators=(',', ':'))


def create_embedding_text(name: str, keywords: List[str]) -> str:
    """임베딩용 텍스트 생성"""
    unique_keywords = []
    seen = set()
    for k in keywords:
        if k and k not in seen:
            seen.add(k)
            unique_keywords.append(k)
    
    if not unique_keywords:
        return name.strip()
    
    return f"{name} {' '.join(unique_keywords)}".strip()


async def fetch_menus_with_keto_filter(supa, limit: int, offset: int, min_score: int = 5) -> List[Dict[str, Any]]:
    """keto_scores.score >= min_score인 메뉴들 조회"""
    # 1) keto_scores에서 score >= min_score인 menu_id 조회
    keto_res = supa.client.table('keto_scores').select('menu_id,score').gte('score', min_score).range(offset, offset + limit - 1).execute()
    keto_data = keto_res.data or []
    
    if not keto_data:
        return []
    
    menu_ids = [row['menu_id'] for row in keto_data]
    
    # 2) menu 테이블에서 해당 메뉴들 조회
    menu_res = supa.client.table('menu').select('id,name,description').in_('id', menu_ids).execute()
    menu_data = menu_res.data or []
    
    # 3) 조인
    menu_map = {m['id']: m for m in menu_data}
    result = []
    for keto in keto_data:
        menu_id = keto['menu_id']
        if menu_id in menu_map:
            menu = menu_map[menu_id]
            result.append({
                'id': menu_id,
                'name': menu.get('name', ''),
                'description': menu.get('description'),
                'keto_score': keto.get('score', 0)
            })
    
    return result


def ensure_openai_client() -> OpenAI:
    if OpenAI is None:
        raise RuntimeError("openai 라이브러리가 설치되어 있지 않습니다. pip install openai 필요")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 환경변수가 필요합니다.")
    return OpenAI(api_key=api_key)


def embed_texts(client: OpenAI, texts: List[str], model_name: str) -> List[List[float]]:
    if not texts:
        return []
    
    print(f"🔄 OpenAI API 호출 중... (모델: {model_name}, 텍스트 개수: {len(texts)})")
    import time
    start_time = time.time()
    
    resp = client.embeddings.create(model=model_name, input=texts)
    
    end_time = time.time()
    print(f"✅ OpenAI API 응답 완료 (소요시간: {end_time - start_time:.2f}초)")
    print(f"📊 응답 데이터: {len(resp.data)}개 임베딩, 차원: {len(resp.data[0].embedding) if resp.data else 0}")
    
    return [d.embedding for d in resp.data]


async def upsert_embeddings(supa, rows: List[Dict[str, Any]]):
    if not rows:
        return
    supa.client.table('menu_embedding').upsert(rows, on_conflict="menu_id,model_name,algorithm_version").execute()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", default="text-embedding-3-small")
    parser.add_argument("--algorithm-version", default="RAG-v1.0")
    parser.add_argument("--dimension", type=int, default=1536)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--min-keto-score", type=int, default=20)
    parser.add_argument("--recompute-all", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="실제 임베딩 없이 키워드 추출만 테스트")
    args = parser.parse_args()

    cfg = EmbeddingConfig(
        model_name=args.model_name,
        algorithm_version=args.algorithm_version,
        dimension=args.dimension,
        batch_size=args.batch_size,
        limit=args.limit,
        offset=args.offset,
    )

    # DB 초기화
    await db_pool.initialize()
    supa = db_pool.supabase

    # OpenAI 클라이언트 (dry-run이 아닐 때만)
    openai_client = None
    if not args.dry_run:
        openai_client = ensure_openai_client()

    print(f"🔍 keto_scores.score >= {args.min_keto_score}인 메뉴 조회 중...")
    
    # 메뉴 조회
    menus = await fetch_menus_with_keto_filter(supa, cfg.limit, cfg.offset, args.min_keto_score)
    
    if not menus:
        print("❌ 조건에 맞는 메뉴가 없습니다.")
        await db_pool.close()
        return

    print(f"✅ {len(menus)}개 메뉴 발견")

    # 기존 레코드 해시 조회 (중복 방지용)
    menu_ids = [m['id'] for m in menus]
    existing_map: Dict[Tuple[str, str, str], str] = {}
    res_existing = supa.client.table('menu_embedding').select('menu_id,model_name,algorithm_version,content_hash').in_('menu_id', menu_ids).eq('model_name', cfg.model_name).eq('algorithm_version', cfg.algorithm_version).execute()
    for row in res_existing.data or []:
        existing_map[(row['menu_id'], row['model_name'], row['algorithm_version'])] = row.get('content_hash') or ""

    texts: List[str] = []
    meta: List[Tuple[str, str]] = []  # (menu_id, content_hash)
    blobs: List[str] = []

    print("\n" + "=" * 80)
    print("키워드 추출 및 blob 생성")
    print("=" * 80)

    for i, menu in enumerate(menus, 1):
        menu_id = menu['id']
        name = menu['name']
        
        # 개선된 키워드 추출
        keyword_matches = extract_keywords_improved(name)
        keywords = [match['keyword'] for match in keyword_matches]
        
        if args.dry_run or i <= 10:  # 처음 10개는 상세 출력
            print(f"\n[{i}] {name} (키토점수: {menu['keto_score']})")
            if keyword_matches:
                for match in keyword_matches:
                    print(f"  ✓ {match['keyword']} ({match['type']}, 가중치: {match['weight']})")
            else:
                print("  - 키워드 없음")

        # content_blob 생성
        content_blob = create_content_blob(name, keywords)
        content_hash = sha256_hex(content_blob)
        
        # 기존 해시와 비교
        existed_hash = existing_map.get((menu_id, cfg.model_name, cfg.algorithm_version))
        if existed_hash and existed_hash == content_hash and not args.recompute_all:
            if args.dry_run or i <= 10:
                print(f"  → 스킵 (기존과 동일)")
            continue

        # 임베딩용 텍스트
        embedding_text = create_embedding_text(name, keywords)
        
        if args.dry_run or i <= 10:
            print(f"  → blob: {content_blob}")
            print(f"  → 임베딩 텍스트: '{embedding_text}'")

        texts.append(embedding_text)
        meta.append((menu_id, content_hash))
        blobs.append(content_blob)

    if args.dry_run:
        print(f"\n✅ Dry-run 완료. 총 {len(texts)}개 메뉴가 임베딩 대상입니다.")
        await db_pool.close()
        return

    if not texts:
        print("❌ 처리할 메뉴가 없습니다.")
        await db_pool.close()
        return

    # 배치 임베딩 생성
    print(f"\n🚀 {len(texts)}개 메뉴 임베딩 생성 중...")
    embeddings = embed_texts(openai_client, texts, cfg.model_name)
    
    # DB에 upsert
    rows = []
    for (menu_id, content_hash), emb, content_blob in zip(meta, embeddings, blobs):
        rows.append({
            'menu_id': menu_id,
            'model_name': cfg.model_name,
            'dimension': cfg.dimension,
            'algorithm_version': cfg.algorithm_version,
            'embedding': emb,
            'content_hash': content_hash,
            'content_blob': content_blob,
        })
    
    await upsert_embeddings(supa, rows)
    print(f"✅ {len(rows)}개 임베딩 upsert 완료")

    await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
