"""
레스토랑 대표메뉴와 대표 키토점수를 재계산하여 `restaurant` 테이블에 반영하는 스크립트.

동작:
1) 모든 레스토랑의 `representative_menu_name`, `representative_keto_score`를 NULL로 초기화
2) 각 레스토랑의 메뉴를 조회 → 각 메뉴의 최신 키토점수(가장 최근 created_at) 조회
3) 최고 점수 메뉴를 대표 메뉴로 선택하여 레스토랑에 업데이트

사용법 (PowerShell):
  pwsh -NoProfile -File scripts/recompute_restaurant_representatives.py

주의: Supabase 인증 정보는 `config.settings`에 설정되어 있어야 함
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from infrastructure.database.connection import db_pool


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


async def fetch_all_restaurants(batch_size: int = 500) -> List[Dict[str, Any]]:
    """모든 레스토랑을 배치로 조회"""
    restaurants: List[Dict[str, Any]] = []
    offset = 0

    while True:
        batch = await asyncio.to_thread(
            lambda: db_pool.supabase.client
            .table('restaurant')
            .select('*')
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        data = batch.data or []
        if not data:
            break
        restaurants.extend(data)
        offset += batch_size

    return restaurants


async def fetch_menus_for_restaurant(restaurant_id: str) -> List[Dict[str, Any]]:
    """레스토랑의 모든 메뉴 조회"""
    result = await asyncio.to_thread(
        lambda: db_pool.supabase.client
        .table('menu')
        .select('*')
        .eq('restaurant_id', restaurant_id)
        .execute()
    )
    return result.data or []


async def fetch_latest_keto_score(menu_id: str) -> Optional[Dict[str, Any]]:
    """메뉴의 최신(가장 최근 created_at) 키토점수 1건 조회"""
    result = await asyncio.to_thread(
        lambda: db_pool.supabase.client
        .table('keto_scores')
        .select('*')
        .eq('menu_id', menu_id)
        .order('created_at', desc=True)
        .limit(1)
        .execute()
    )
    data = result.data or []
    return data[0] if data else None


async def pick_representative_menu(menus: List[Dict[str, Any]]) -> Optional[Tuple[str, int]]:
    """메뉴 리스트에서 최신 점수 기준 최고 점수 메뉴를 대표로 선정.

    반환: (대표메뉴명, 대표점수) 또는 None
    """
    best_name: Optional[str] = None
    best_score: Optional[int] = None

    for menu in menus:
        menu_id = menu.get('id')
        menu_name = menu.get('name')
        if not menu_id or not menu_name:
            continue

        latest_score = await fetch_latest_keto_score(menu_id)
        if not latest_score:
            continue

        score_value = latest_score.get('score')
        if score_value is None:
            continue

        if (best_score is None) or (int(score_value) > int(best_score)):
            best_score = int(score_value)
            best_name = str(menu_name)

    if best_name is None or best_score is None:
        return None
    return best_name, best_score


async def clear_representatives() -> None:
    """모든 레스토랑의 대표 필드를 NULL로 초기화"""
    # Supabase는 전체 업데이트에 조건이 필요하므로 항상 참인 조건으로 우회
    await asyncio.to_thread(
        lambda: db_pool.supabase.client
        .table('restaurant')
        .update({
            'representative_menu_name': None,
            'representative_keto_score': None
        })
        .neq('id', '00000000-0000-0000-0000-000000000000')
        .execute()
    )


async def update_restaurant_representative(restaurant_id: str, menu_name: str, score: int) -> None:
    """단일 레스토랑의 대표값 업데이트"""
    await asyncio.to_thread(
        lambda: db_pool.supabase.client
        .table('restaurant')
        .update({
            'representative_menu_name': menu_name,
            'representative_keto_score': int(score)
        })
        .eq('id', restaurant_id)
        .execute()
    )


async def recompute_all() -> None:
    await db_pool.initialize()

    logger.info("Clearing existing representative fields ...")
    await clear_representatives()

    logger.info("Fetching restaurants ...")
    restaurants = await fetch_all_restaurants()
    logger.info(f"Total restaurants: {len(restaurants)}")

    updated = 0
    skipped = 0

    for r in restaurants:
        rid = r.get('id')
        if not rid:
            skipped += 1
            continue

        menus = await fetch_menus_for_restaurant(rid)
        if not menus:
            skipped += 1
            continue

        representative = await pick_representative_menu(menus)
        if not representative:
            skipped += 1
            continue

        rep_name, rep_score = representative
        await update_restaurant_representative(rid, rep_name, rep_score)
        updated += 1

        if updated % 50 == 0:
            logger.info(f"Updated {updated} restaurants so far ...")

    logger.info(f"Done. Updated: {updated}, Skipped: {skipped}")


def main():
    asyncio.run(recompute_all())


if __name__ == "__main__":
    main()


