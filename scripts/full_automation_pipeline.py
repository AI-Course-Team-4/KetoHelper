#!/usr/bin/env python3
"""
완전 자동화 키토 헬퍼 파이프라인
1. 강남역 주변 레스토랑 30개 크롤링
2. 메뉴 데이터 수집
3. 키토 점수 자동 계산
4. Supabase 저장
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.domain.menu import Menu
from core.domain.restaurant import Restaurant, Address
from services.scorer.keto_scorer import KetoScorer
from infrastructure.database.supabase_connection import SupabaseConnection
from config.settings import settings
from config.crawler_config import register_crawlers
from services.crawler.crawler_factory import crawler_factory

async def full_automation_pipeline():
    """완전 자동화 키토 헬퍼 파이프라인"""
    print("🚀 완전 자동화 키토 헬퍼 파이프라인 시작")
    print("=" * 60)
    
    # 결과 저장용
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"data/reports/full_automation_{timestamp}.json"
    
    try:
        # 1단계: 크롤러 초기화
        print("\n🕷️  1단계: 크롤러 초기화")
        register_crawlers()
        crawler = crawler_factory.create('diningcode')
        await crawler.initialize()
        print("✅ DiningcodeCrawler 초기화 완료")
        
        # 2단계: 강남역 주변 레스토랑 30개 검색
        print("\n🔍 2단계: 강남역 주변 레스토랑 검색")
        search_keywords = ["강남역 맛집"]
        target_count = 30
        
        print(f"   검색어: {search_keywords}")
        print(f"   목표 개수: {target_count}개")
        
        # 검색 결과 가져오기 (URL 목록)
        restaurant_urls = await crawler.crawl_restaurant_list(
            keywords=search_keywords,
            max_pages=5  # 충분한 결과를 얻기 위해 5페이지까지
        )
        
        # 목표 개수만큼 제한
        restaurant_urls = restaurant_urls[:target_count]
        
        print(f"✅ {len(restaurant_urls)}개 레스토랑 URL 검색 완료")
        
        # 3단계: 상세 정보 크롤링
        print(f"\n📊 3단계: 레스토랑 상세 정보 크롤링")
        
        crawled_data = []
        successful_crawls = 0
        
        for i, restaurant_url in enumerate(restaurant_urls, 1):
            print(f"\n[{i}/{len(restaurant_urls)}] {restaurant_url} 크롤링 중...")
            
            try:
                # 상세 정보 크롤링
                detail_result = await crawler.crawl_restaurant_detail(restaurant_url)
                
                if detail_result and detail_result.success:
                    crawled_data.append(detail_result.data)
                    successful_crawls += 1
                    
                    menu_count = len(detail_result.data.get('menus', []))
                    restaurant_name = detail_result.data.get('restaurant', {}).get('name', 'Unknown')
                    print(f"   ✅ 성공: {restaurant_name}, {menu_count}개 메뉴 수집")
                else:
                    error_msg = detail_result.error if detail_result else "상세 정보 없음"
                    print(f"   ❌ 실패: {error_msg}")
                    
            except Exception as e:
                print(f"   ❌ 크롤링 실패: {e}")
                continue
                
            # 진행률 표시
            if i % 5 == 0:
                print(f"📈 진행률: {i}/{len(restaurant_urls)} ({i/len(restaurant_urls)*100:.1f}%)")
        
        print(f"\n✅ 크롤링 완료: {successful_crawls}개 레스토랑, 총 {sum(len(r.get('menus', [])) for r in crawled_data)}개 메뉴")
        
        # 중간 결과 저장
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(crawled_data, f, ensure_ascii=False, indent=2)
        print(f"📁 크롤링 결과 저장: {report_file}")
        
        # 4단계: Supabase 연결 및 데이터 업로드
        print(f"\n💾 4단계: Supabase 데이터 업로드")
        
        supabase_conn = SupabaseConnection()
        await supabase_conn.initialize()
        supabase = supabase_conn.client
        print("✅ Supabase 연결 성공")
        
        # 5단계: 키토 스코어러 초기화
        print(f"\n🧮 5단계: 키토 스코어러 초기화")
        scorer = KetoScorer(settings)
        print("✅ 키토 스코어러 초기화 완료")
        
        # 6단계: 레스토랑 데이터 업로드
        print(f"\n🏪 6단계: 레스토랑 데이터 업로드")
        
        restaurant_count = 0
        restaurant_mapping = {}  # 원본 이름 → UUID 매핑
        
        for item in crawled_data:
            restaurant_info = item['restaurant']
            
            try:
                # 기존 레스토랑 체크 (source_url 기준)
                source_url = restaurant_info.get('source_url', '')
                existing_restaurant = supabase.table('restaurant').select('id, name').eq('source_url', source_url).execute()
                
                if existing_restaurant.data:
                    # 기존 레스토랑이 있으면 해당 ID 사용
                    restaurant_id = existing_restaurant.data[0]['id']
                    restaurant_name = existing_restaurant.data[0]['name']
                    restaurant_mapping[restaurant_info['name']] = restaurant_id
                    print(f"   🔄 기존 레스토랑 발견: {restaurant_name} (ID: {restaurant_id})")
                else:
                    # 새 레스토랑 생성
                    address = Address(
                        addr_road=restaurant_info['address'],
                        latitude=37.5665,  # 강남역 중심 좌표
                        longitude=127.0286
                    )
                    
                    restaurant = Restaurant(
                        name=restaurant_info['name'],
                        address=address,
                        phone=restaurant_info.get('phone'),
                        source=restaurant_info.get('source_name', 'diningcode'),
                        source_url=source_url
                    )
                    
                    # DB 저장 데이터 준비
                    restaurant_data = {
                        'id': str(restaurant.id),
                        'name': restaurant.name,
                        'addr_road': restaurant.address.addr_road,
                        'lat': restaurant.address.latitude,
                        'lng': restaurant.address.longitude,
                        'source': restaurant_info.get('source_name', 'diningcode'),
                        'source_url': source_url
                    }
                    
                    # 선택적 필드 추가
                    if restaurant.phone:
                        restaurant_data['phone'] = restaurant.phone
                    
                    # Supabase에 저장
                    restaurant_result = supabase.table('restaurant').insert(restaurant_data).execute()
                    restaurant_mapping[restaurant_info['name']] = str(restaurant.id)
                    restaurant_count += 1
                    
                    print(f"   ✅ [{restaurant_count}] {restaurant.name}")
                
            except Exception as e:
                print(f"   ❌ 레스토랑 저장 실패: {restaurant_info['name']} - {e}")
                continue
        
        print(f"✅ 총 {restaurant_count}개 레스토랑 업로드 완료")
        
        # 7단계: 메뉴 데이터 업로드 및 키토 점수 계산
        print(f"\n🍽️  7단계: 메뉴 업로드 및 키토 점수 계산")
        
        menu_count = 0
        keto_score_count = 0
        score_stats = []
        
        for item in crawled_data:
            restaurant_info = item['restaurant']
            restaurant_name = restaurant_info['name']
            
            # 레스토랑 ID 찾기
            if restaurant_name not in restaurant_mapping:
                print(f"   ⚠️  레스토랑 ID를 찾을 수 없음: {restaurant_name}")
                continue
                
            restaurant_id = restaurant_mapping[restaurant_name]
            
            # 메뉴들 처리
            for menu_info in item.get('menus', []):
                try:
                    # 중복 메뉴 체크 먼저
                    existing_menu = supabase.table('menu').select('id').eq('restaurant_id', restaurant_id).eq('name', menu_info['name']).execute()
                    
                    if existing_menu.data:
                        # 기존 메뉴가 있으면 해당 ID 사용
                        menu_id = existing_menu.data[0]['id']
                        print(f"   🔄 기존 메뉴 발견: {menu_info['name']} (ID: {menu_id})")
                    else:
                        # 새 메뉴 생성
                        menu = Menu(
                            name=menu_info['name'],
                            price=menu_info.get('price'),
                            description=menu_info.get('description'),
                            restaurant_id=restaurant_id
                        )
                        menu_id = str(menu.id)
                        
                        # 메뉴 DB 저장
                        menu_data = {
                            'id': menu_id,
                            'name': menu_info['name'],
                            'price': menu_info.get('price'),
                            'description': menu_info.get('description'),
                            'restaurant_id': restaurant_id,
                            'currency': 'KRW'
                        }
                        
                        menu_result = supabase.table('menu').insert(menu_data).execute()
                    menu_count += 1
                    
                    # 키토 점수 계산을 위한 Menu 객체 생성
                    menu_for_scoring = Menu(
                        name=menu_info['name'],
                        price=menu_info.get('price'),
                        description=menu_info.get('description'),
                        restaurant_id=restaurant_id
                    )
                    menu_for_scoring.id = menu_id  # 실제 DB ID 사용
                    
                    # 키토 점수 계산
                    keto_score = await scorer.calculate_score(menu_for_scoring)
                    
                    # 키토 점수 데이터 준비
                    penalty_keywords = [
                        kw for kw in keto_score.detected_keywords 
                        if any(r.impact < 0 for r in keto_score.reasons if r.keyword == kw)
                    ]
                    bonus_keywords = [
                        kw for kw in keto_score.detected_keywords 
                        if any(r.impact > 0 for r in keto_score.reasons if r.keyword == kw)
                    ]
                    
                    keto_score_data = {
                        'menu_id': menu_id,
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
                        'rule_version': 'v1.0'
                    }
                    
                    # 키토 점수 중복 체크 후 저장
                    existing_score = supabase.table('keto_scores').select('id').eq('menu_id', menu_id).execute()
                    
                    if existing_score.data:
                        # 기존 점수가 있으면 업데이트
                        score_id = existing_score.data[0]['id']
                        keto_result = supabase.table('keto_scores').update(keto_score_data).eq('id', score_id).execute()
                        print(f"   🔄 키토 점수 업데이트: {menu_info['name']} -> {keto_score.final_score}점")
                    else:
                        # 새로운 점수 생성
                        keto_result = supabase.table('keto_scores').insert(keto_score_data).execute()
                        print(f"   ✅ 키토 점수 생성: {menu_info['name']} -> {keto_score.final_score}점")
                    keto_score_count += 1
                    score_stats.append(keto_score.final_score)
                    
                    # 진행률 표시
                    if menu_count % 20 == 0:
                        print(f"   📊 진행률: {menu_count}개 메뉴 처리 완료...")
                        
                except Exception as e:
                    print(f"   ❌ 메뉴/점수 저장 실패: {menu_info['name']} - {e}")
                    continue
        
        print(f"✅ 총 {menu_count}개 메뉴, {keto_score_count}개 키토 점수 저장 완료")
        
        # 8단계: 최종 결과 요약
        print(f"\n📊 8단계: 최종 결과 요약")
        print("=" * 60)
        print(f"🏪 레스토랑: {restaurant_count}개")
        print(f"🍽️  메뉴: {menu_count}개")
        print(f"🧮 키토 점수: {keto_score_count}개")
        
        if score_stats:
            print(f"\n📈 키토 점수 통계:")
            print(f"   평균: {sum(score_stats)/len(score_stats):.1f}점")
            print(f"   최고: {max(score_stats):.1f}점")
            print(f"   최저: {min(score_stats):.1f}점")
            
            # 카테고리별 분포
            categories = {
                "키토 권장 (80점 이상)": len([s for s in score_stats if s >= 80]),
                "조건부 키토 (50-79점)": len([s for s in score_stats if 50 <= s < 80]),
                "키토 주의 (20-49점)": len([s for s in score_stats if 20 <= s < 50]),
                "키토 비추천 (20점 미만)": len([s for s in score_stats if s < 20])
            }
            
            print(f"\n🏷️  카테고리 분포:")
            for category, count in categories.items():
                percentage = count / len(score_stats) * 100
                print(f"   {category}: {count}개 ({percentage:.1f}%)")
        
        # 9단계: 샘플 데이터 확인
        print(f"\n🔍 9단계: 저장된 데이터 샘플 확인")
        
        # 상위 키토 점수 메뉴들 조회
        sample_query = """
            id,
            menu:menu_id(name, price, restaurant:restaurant_id(name)),
            score,
            reasons_json
        """
        
        sample_result = supabase.table('keto_scores').select(sample_query).order('score', desc=True).limit(5).execute()
        
        if sample_result.data:
            print("✅ 상위 5개 키토 점수:")
            for item in sample_result.data:
                menu_info = item.get('menu', {})
                restaurant_info = menu_info.get('restaurant', {})
                menu_name = menu_info.get('name', 'N/A')
                price = menu_info.get('price', 'N/A')
                restaurant_name = restaurant_info.get('name', 'N/A')
                score = item.get('score', 0)
                reasons = item.get('reasons_json', {})
                confidence = reasons.get('confidence', 0)
                
                print(f"   📋 {menu_name} - {restaurant_name}")
                print(f"      점수: {score}점 (신뢰도: {confidence:.2f})")
                print(f"      가격: {price}원")
                print()
        
        print("🎉 완전 자동화 키토 헬퍼 파이프라인 완료!")
        print("=" * 60)
        
        # 크롤러 정리
        if hasattr(crawler, 'close'):
            await crawler.close()
        
    except Exception as e:
        print(f"❌ 파이프라인 실패: {e}")
        import traceback
        traceback.print_exc()
        
        # 크롤러 정리 (에러 시에도)
        try:
            if hasattr(crawler, 'close'):
                await crawler.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(full_automation_pipeline())
