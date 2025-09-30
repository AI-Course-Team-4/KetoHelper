#!/usr/bin/env python3
"""
DB의 기존 메뉴를 불러와 키토 점수를 계산하고 `keto_scores` 테이블에 upsert합니다.

기본 동작
- 대상: 아직 `keto_scores`에 레코드가 없는 메뉴들(미채점 메뉴)
- 배치: 기본 200개씩 처리

요구사항
- Supabase 연결: infrastructure.database.supabase_connection.SupabaseConnection 사용
- 스코어러: services.scorer.keto_scorer.KetoScorer 사용

실행
  python -m scripts.score_existing_menus
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.domain.menu import Menu
from services.scorer.keto_scorer import KetoScorer
from infrastructure.database.supabase_connection import SupabaseConnection
from config.settings import settings


BATCH_SIZE_DEFAULT = 200
RULE_VERSION_DEFAULT = getattr(settings, 'KETO_RULE_VERSION', 'v1.0') if hasattr(settings, 'KETO_RULE_VERSION') else 'v1.0'


async def score_batch(scorer: KetoScorer, supabase, menus: List[Dict[str, Any]]) -> int:
    """메뉴 배치를 채점하고 `keto_scores`에 upsert한다. 반환: 처리 건수"""
    processed = 0

    for m in menus:
        try:
            menu_obj = Menu(
                name=m.get('name'),
                price=m.get('price'),
                description=m.get('description'),
                restaurant_id=m.get('restaurant_id')
            )
            menu_obj.id = m.get('id')

            keto_score = await scorer.calculate_score(menu_obj)

            penalty_keywords = [
                kw for kw in keto_score.detected_keywords
                if any(r.impact < 0 for r in keto_score.reasons if r.keyword == kw)
            ]
            bonus_keywords = [
                kw for kw in keto_score.detected_keywords
                if any(r.impact > 0 for r in keto_score.reasons if r.keyword == kw)
            ]

            keto_score_data = {
                'menu_id': m['id'],
                'score': max(0, min(100, int(keto_score.final_score))),
                'reasons_json': {
                    'reasons': [
                        {
                            'rule_id': reason.rule_id,
                            'keyword': reason.keyword,
                            'impact': reason.impact,
                            'explanation': reason.explanation
                        } for reason in keto_score.reasons
                    ],
                    'applied_rules': keto_score.applied_rules,
                    'raw_score': keto_score.raw_score,
                    'final_score': keto_score.final_score,
                    'penalty_keywords': penalty_keywords,
                    'bonus_keywords': bonus_keywords,
                    'confidence': float(keto_score.confidence)
                },
                'rule_version': RULE_VERSION_DEFAULT
            }

            existing = supabase.table('keto_scores').select('id').eq('menu_id', m['id']).execute()
            if existing.data:
                score_id = existing.data[0]['id']
                supabase.table('keto_scores').update(keto_score_data).eq('id', score_id).execute()
                print(f"   🔄 업데이트: {m.get('name')} -> {keto_score.final_score}점")
            else:
                supabase.table('keto_scores').insert(keto_score_data).execute()
                print(f"   ✅ 생성: {m.get('name')} -> {keto_score.final_score}점")

            processed += 1
        except Exception as e:
            print(f"   ❌ 실패: {m.get('name', 'Unknown')} - {e}")

    return processed


async def score_existing_menus(batch_size: int = BATCH_SIZE_DEFAULT, force_rescore: bool = False, limit: Optional[int] = None, force_all: bool = False):
    print("🧮 기존 메뉴 채점 시작")

    # Supabase 연결
    supabase_conn = SupabaseConnection()
    await supabase_conn.initialize()
    supabase = supabase_conn.client
    print("✅ Supabase 연결 성공")

    # 스코어러
    scorer = KetoScorer(settings)
    print("✅ 스코어러 초기화 완료")

    # 전체 메뉴 수 및 기본 데이터 조회
    menus_resp = supabase.table('menu').select('id,updated_at').execute()
    all_menus = menus_resp.data or []
    all_menu_ids = [row['id'] for row in all_menus]
    if not all_menu_ids:
        print("⚠️  처리할 메뉴가 없습니다")
        return

    # 이미 채점된 메뉴 ID 및 최신 업데이트 시각 수집
    scored_resp = supabase.table('keto_scores').select('menu_id,updated_at').execute()
    scored_data = scored_resp.data or []
    scored_ids = set([row['menu_id'] for row in scored_data])
    scored_map = {row['menu_id']: row['updated_at'] for row in scored_data}

    # 대상 메뉴 ID 계산
    if force_all:
        # 전 메뉴를 대상으로 강제 재채점
        target_ids = list(all_menu_ids)
    elif force_rescore:
        # 재채점: 점수 미존재 + (메뉴.updated_at > 점수.updated_at) 둘 다 포함
        target_ids = []
        for m in all_menus:
            mid = m['id']
            if mid not in scored_ids:
                target_ids.append(mid)
            else:
                # 메뉴가 점수보다 최근에 업데이트되었으면 재채점
                menu_updated = m.get('updated_at')
                score_updated = scored_map.get(mid)
                if menu_updated and score_updated and menu_updated > score_updated:
                    target_ids.append(mid)
    else:
        # 기본: 점수 미존재만
        target_ids = [mid for mid in all_menu_ids if mid not in scored_ids]
    total_targets = len(target_ids)
    if total_targets == 0:
        print("✅ 미채점 메뉴가 없습니다")
        return

    if limit is not None and total_targets > limit:
        target_ids = target_ids[:limit]
        total_targets = len(target_ids)

    print(f"📋 대상 메뉴: {total_targets}개 (배치 {batch_size}개) | 전체 {len(all_menu_ids)}개, 채점됨 {len(scored_ids)}개 | 모드: {'force_all' if force_all else ('force_rescore' if force_rescore else 'new_only')}")

    processed_total = 0
    for start in range(0, total_targets, batch_size):
        end = min(start + batch_size, total_targets)
        batch_ids = target_ids[start:end]

        # 배치 상세 정보 조회
        batch_resp = supabase.table('menu').select(
            'id,name,price,description,restaurant_id,updated_at'
        ).in_('id', batch_ids).execute()
        menus = batch_resp.data or []

        print(f"\n🔄 배치 {start // batch_size + 1}: {len(menus)}개 메뉴 채점 중...")
        processed = await score_batch(scorer, supabase, menus)
        processed_total += processed
        print(f"   📊 누적 처리: {processed_total}/{total_targets}")

    print(f"\n🎉 완료: 총 {processed_total}개 메뉴 채점 및 저장")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score existing menus into keto_scores")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE_DEFAULT, help="배치 크기")
    parser.add_argument("--force-rescore", action="store_true", help="재채점 수행: 메뉴가 점수보다 최신이면 다시 채점")
    parser.add_argument("--limit", type=int, default=None, help="최대 처리 개수 제한")
    parser.add_argument("--force-all", action="store_true", help="업데이트 여부 무시하고 전 메뉴 강제 재채점")
    args = parser.parse_args()

    asyncio.run(score_existing_menus(batch_size=args.batch_size, force_rescore=args.force_rescore, limit=args.limit, force_all=args.force_all))



