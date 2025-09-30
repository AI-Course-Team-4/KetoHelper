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
from services.processor.data_processor import DataProcessor
from services.processor.side_dish_classifier import SideDishClassifier
from services.processor.geocoding_service import GeocodingService
from services.cache.cache_manager import CacheManager
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
        # 1단계: 크롤러 초기화 (기존 httpx 버전, 페이지 수 대폭 증가)
        print("\n🕷️  1단계: httpx 크롤러 초기화 (페이지 수 대폭 증가)")
        register_crawlers()
        crawler = crawler_factory.create('diningcode')
        await crawler.initialize()
        print("✅ DiningcodeCrawler 초기화 완료")
        
        # 2단계: 강남역 주변 레스토랑 대량 수집 (키워드 + 지역 확장)
        print("\n🔍 2단계: 강남역 주변 레스토랑 대량 크롤링")
        
        # 강남역 다이어트 관련 핵심 키워드 (2개만)
        search_keywords = [
            "다이어트 강남",
            "저탄고지 강남"
        ]
        target_count = 50  # 목표 50개 (저탄고지 레스토랑 확보)
        
        print(f"   검색어: {search_keywords}")
        print(f"   목표 개수: {target_count}개")
        
        # Rate Limiter를 더 빠르게 조정 (속도 최적화)
        from infrastructure.external.rate_limiter import create_conservative_rate_limiter
        crawler.rate_limiter = create_conservative_rate_limiter(0.1)  # 0.1초 간격으로 빠르게
        
        # 키워드 확장으로 검색 결과 가져오기 (URL 목록)
        restaurant_urls = await crawler.crawl_restaurant_list(
            keywords=search_keywords,
            max_pages=1,  # 각 키워드당 1페이지씩 (20개씩, 빠른 실행)
            target_count=target_count  # 목표 개수
        )
        
        print(f"✅ {len(restaurant_urls)}개 레스토랑 URL 검색 완료")
        
        # 3단계: 상세 정보 크롤링 (병렬 처리로 속도 향상)
        print(f"\n📊 3단계: 레스토랑 상세 정보 크롤링 (병렬 처리)")
        
        crawled_data = []
        successful_crawls = 0
        
        # 병렬 처리로 5개씩 동시에 크롤링
        batch_size = 5
        for batch_start in range(0, len(restaurant_urls), batch_size):
            batch_end = min(batch_start + batch_size, len(restaurant_urls))
            batch_urls = restaurant_urls[batch_start:batch_end]
            
            print(f"\n🔄 배치 {batch_start//batch_size + 1}: {len(batch_urls)}개 식당 병렬 크롤링 중...")
            
            # 병렬로 크롤링
            tasks = [crawler.crawl_restaurant_detail(url) for url in batch_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 처리
            for i, (url, result) in enumerate(zip(batch_urls, results)):
                try:
                    if isinstance(result, Exception):
                        print(f"   ❌ {url}: {result}")
                        continue
                        
                    if result and result.success:
                        crawled_data.append(result.data)
                        successful_crawls += 1
                        
                        menu_count = len(result.data.get('menus', []))
                        restaurant_name = result.data.get('restaurant', {}).get('name', 'Unknown')
                        print(f"   ✅ {restaurant_name}: {menu_count}개 메뉴")
                    else:
                        error_msg = result.error if result else "상세 정보 없음"
                        print(f"   ❌ {url}: {error_msg}")
                        
                except Exception as e:
                    print(f"   ❌ {url}: {e}")
            
            # 진행률 표시
            print(f"📈 진행률: {batch_end}/{len(restaurant_urls)} ({batch_end/len(restaurant_urls)*100:.1f}%)")
        
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
        
        # 5단계: 데이터 처리기 및 키토 스코어러 초기화
        print(f"\n🔧 5단계: 데이터 처리기 초기화")
        data_processor = DataProcessor()
        print("✅ 데이터 처리기 초기화 완료")
        
        print(f"\n🧮 6단계: 키토 스코어러 초기화")
        scorer = KetoScorer(settings)
        print("✅ 키토 스코어러 초기화 완료")
        
        print(f"\n🍽️  7단계: 사이드 분류기 초기화")
        side_classifier = SideDishClassifier(industry="general")
        print("✅ 사이드 분류기 초기화 완료")
        
        print(f"\n🗺️  7.5단계: 지오코딩 서비스 초기화")
        cache_manager = CacheManager()
        geocoding_service = GeocodingService(cache_manager)
        print("✅ 지오코딩 서비스 초기화 완료")
        
        # 8단계: 레스토랑 데이터 업로드
        print(f"\n🏪 8단계: 레스토랑 데이터 업로드")
        
        restaurant_count = 0
        restaurant_mapping = {}  # 원본 이름 → UUID 매핑
        geocoding_stats = {"success": 0, "failed": 0}  # 지오코딩 통계
        
        for item in crawled_data:
            restaurant_info = item['restaurant']
            
            try:
                # 식당명 전처리 적용
                cleaned_restaurant_name = data_processor._clean_restaurant_name(restaurant_info['name'])
                
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
                    # 새 레스토랑 생성 - 실제 지오코딩 수행
                    address_text = restaurant_info['address']
                    print(f"   🗺️  지오코딩 중: {address_text}")
                    
                    # 실제 지오코딩 수행
                    try:
                        geocoding_result = await geocoding_service.geocode(address_text)
                        
                        if geocoding_result:
                            latitude = geocoding_result['lat']
                            longitude = geocoding_result['lng']
                            addr_norm = geocoding_result['formatted_address']
                            geocoding_stats["success"] += 1
                            print(f"   ✅ 지오코딩 성공: {latitude:.6f}, {longitude:.6f}")
                        else:
                            # 실패 시 기본값 (강남역 중심)
                            latitude = 37.5665
                            longitude = 127.0286
                            addr_norm = None
                            geocoding_stats["failed"] += 1
                            print(f"   ⚠️  지오코딩 실패, 기본값 사용")
                            
                    except Exception as e:
                        print(f"   ❌ 지오코딩 에러: {e}")
                        # 기본값 사용
                        latitude = 37.5665
                        longitude = 127.0286
                        addr_norm = None
                        geocoding_stats["failed"] += 1
                    
                    address = Address(
                        addr_road=address_text,
                        latitude=latitude,
                        longitude=longitude
                    )
                    
                    restaurant = Restaurant(
                        name=cleaned_restaurant_name,  # 전처리된 이름 사용
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
                        'source_url': source_url,
                        'representative_menu_name': None,  # 나중에 업데이트
                        'representative_keto_score': None  # 나중에 업데이트
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
        
        # 9단계: 메뉴 데이터 업로드, 사이드 분류 및 키토 점수 계산
        print(f"\n🍽️  9단계: 메뉴 업로드, 사이드 분류 및 키토 점수 계산")
        
        menu_count = 0
        keto_score_count = 0
        score_stats = []
        side_stats = {"side": 0, "main": 0}
        
        for item in crawled_data:
            restaurant_info = item['restaurant']
            restaurant_name = restaurant_info['name']
            
            # 레스토랑 ID 찾기
            if restaurant_name not in restaurant_mapping:
                print(f"   ⚠️  레스토랑 ID를 찾을 수 없음: {restaurant_name}")
                continue
                
            restaurant_id = restaurant_mapping[restaurant_name]
            
            # 레스토랑의 모든 메뉴 가격 수집 (사이드 분류용)
            restaurant_prices = [menu.get('price') for menu in item.get('menus', [])]
            
            # 메뉴들 처리
            for menu_info in item.get('menus', []):
                try:
                    # 메뉴명 전처리 적용
                    cleaned_menu_name = data_processor._clean_menu_name(menu_info['name'])
                    
                    # 전처리된 메뉴명이 비어있으면 건너뛰기
                    if not cleaned_menu_name or len(cleaned_menu_name.strip()) == 0:
                        print(f"   ⚠️  메뉴명이 전처리 후 비어있음: '{menu_info['name']}', 건너뛰기")
                        continue
                    
                    # 사이드 분류 수행
                    side_result = side_classifier.classify(
                        name=cleaned_menu_name,
                        description=menu_info.get('description'),
                        price=menu_info.get('price'),
                        restaurant_prices=restaurant_prices
                    )
                    
                    # 중복 메뉴 체크 먼저 (전처리된 이름으로)
                    existing_menu = supabase.table('menu').select('id').eq('restaurant_id', restaurant_id).eq('name', cleaned_menu_name).execute()
                    
                    if existing_menu.data:
                        # 기존 메뉴가 있으면 해당 ID 사용하고 is_side 업데이트
                        menu_id = existing_menu.data[0]['id']
                        
                        # 기존 메뉴의 is_side 값 업데이트
                        update_data = {'is_side': side_result.is_side}
                        supabase.table('menu').update(update_data).eq('id', menu_id).execute()
                        
                        print(f"   🔄 기존 메뉴 발견 및 업데이트: {cleaned_menu_name} (ID: {menu_id}, is_side: {side_result.is_side})")
                    else:
                        # 새 메뉴 생성
                        menu = Menu(
                            name=cleaned_menu_name,  # 전처리된 이름 사용
                            price=menu_info.get('price'),
                            description=menu_info.get('description'),
                            restaurant_id=restaurant_id
                        )
                        menu_id = str(menu.id)
                        
                        # 메뉴 DB 저장 (사이드 분류 결과 포함)
                        menu_data = {
                            'id': menu_id,
                            'name': cleaned_menu_name,  # 전처리된 이름 사용
                            'price': menu_info.get('price'),
                            'description': menu_info.get('description'),
                            'restaurant_id': restaurant_id,
                            'currency': 'KRW',
                            'is_side': side_result.is_side
                        }
                        
                        menu_result = supabase.table('menu').insert(menu_data).execute()
                    menu_count += 1
                    
                    # 키토 점수 계산을 위한 Menu 객체 생성
                    menu_for_scoring = Menu(
                        name=cleaned_menu_name,  # 전처리된 이름 사용
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
                        print(f"   🔄 키토 점수 업데이트: {cleaned_menu_name} -> {keto_score.final_score}점")
                    else:
                        # 새로운 점수 생성
                        keto_result = supabase.table('keto_scores').insert(keto_score_data).execute()
                        print(f"   ✅ 키토 점수 생성: {cleaned_menu_name} -> {keto_score.final_score}점")
                    keto_score_count += 1
                    score_stats.append(keto_score.final_score)
                    
                    # 사이드 분류 통계 업데이트
                    if side_result.is_side:
                        side_stats["side"] += 1
                        print(f"   🥗 사이드: {cleaned_menu_name} (점수: {side_result.side_score}, 태그: {side_result.tags[:3]})")
                    else:
                        side_stats["main"] += 1
                        print(f"   🍽️  메인: {cleaned_menu_name} (키토: {keto_score.final_score}점)")
                    
                    # 진행률 표시
                    if menu_count % 20 == 0:
                        print(f"   📊 진행률: {menu_count}개 메뉴 처리 완료...")
                        
                except Exception as e:
                    print(f"   ❌ 메뉴/점수 저장 실패: {menu_info.get('name', 'Unknown')} - {e}")
                    continue
        
        print(f"✅ 총 {menu_count}개 메뉴, {keto_score_count}개 키토 점수 저장 완료")
        
        # 9.5단계: 레스토랑별 대표 메뉴 및 키토 점수 업데이트
        print(f"\n🏆 9.5단계: 레스토랑별 대표 메뉴 및 키토 점수 업데이트")
        
        for restaurant_id in restaurant_mapping.values():
            try:
                # 해당 레스토랑의 최고 키토 점수 메뉴 찾기
                # 먼저 해당 레스토랑의 메뉴 ID들을 가져오기
                menu_ids_result = supabase.table('menu').select('id').eq('restaurant_id', restaurant_id).execute()
                
                if menu_ids_result.data:
                    menu_ids = [menu['id'] for menu in menu_ids_result.data]
                    
                    # 해당 메뉴들의 키토 점수 중 최고점 찾기
                    best_menu_result = supabase.table('keto_scores').select(
                        'menu_id', 'score'
                    ).in_('menu_id', menu_ids).order('score', desc=True).limit(1).execute()
                    
                    if best_menu_result.data:
                        best_score = best_menu_result.data[0]
                        best_menu_id = best_score['menu_id']
                        representative_keto_score = best_score['score']
                        
                        # 최고 점수 메뉴의 이름 가져오기
                        menu_name_result = supabase.table('menu').select('name').eq('id', best_menu_id).execute()
                        if menu_name_result.data:
                            representative_menu_name = menu_name_result.data[0]['name']
                        else:
                            representative_menu_name = "알 수 없는 메뉴"
                    else:
                        representative_menu_name = None
                        representative_keto_score = None
                else:
                    representative_menu_name = None
                    representative_keto_score = None
                
                # 레스토랑 정보 업데이트
                if representative_menu_name and representative_keto_score is not None:
                    update_result = supabase.table('restaurant').update({
                        'representative_menu_name': representative_menu_name,
                        'representative_keto_score': representative_keto_score
                    }).eq('id', restaurant_id).execute()
                    
                    print(f"   ✅ {representative_menu_name} (점수: {representative_keto_score})")
                else:
                    print(f"   ⚠️  메뉴 없음: {restaurant_id}")
                    
            except Exception as e:
                print(f"   ❌ 대표 메뉴 업데이트 실패: {restaurant_id} - {e}")
        
        # 10단계: 최종 결과 요약
        print(f"\n📊 10단계: 최종 결과 요약")
        print("=" * 60)
        print(f"🏪 레스토랑: {restaurant_count}개")
        print(f"🍽️  메뉴: {menu_count}개")
        print(f"🧮 키토 점수: {keto_score_count}개")
        print(f"🥗 사이드 메뉴: {side_stats['side']}개")
        print(f"🍽️  메인 메뉴: {side_stats['main']}개")
        
        # 지오코딩 통계 출력
        print(f"\n🗺️  지오코딩 통계:")
        print(f"   성공: {geocoding_stats['success']}개")
        print(f"   실패: {geocoding_stats['failed']}개")
        if geocoding_stats['success'] + geocoding_stats['failed'] > 0:
            total_geocoding = geocoding_stats['success'] + geocoding_stats['failed']
            success_rate = geocoding_stats['success'] / total_geocoding * 100
            print(f"   성공률: {success_rate:.1f}%")
        
        if menu_count > 0:
            side_percentage = side_stats['side'] / menu_count * 100
            main_percentage = side_stats['main'] / menu_count * 100
            print(f"\n🔍 사이드/메인 분포:")
            print(f"   사이드: {side_stats['side']}개 ({side_percentage:.1f}%)")
            print(f"   메인: {side_stats['main']}개 ({main_percentage:.1f}%)")
        
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
        
        # 11단계: 샘플 데이터 확인
        print(f"\n🔍 11단계: 저장된 데이터 샘플 확인")
        
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
