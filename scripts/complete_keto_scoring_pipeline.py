#!/usr/bin/env python3
"""
완전한 키토 스코어링 파이프라인
1. 크롤링 데이터 → Supabase 업로드 (restaurant, menu)
2. 키토 점수 계산
3. keto_scores 테이블에 저장
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.domain.menu import Menu
from core.domain.restaurant import Restaurant, Address
from services.scorer.keto_scorer import KetoScorer
from infrastructure.database.supabase_connection import SupabaseConnection
from config.settings import settings

async def complete_keto_scoring_pipeline():
    """완전한 키토 스코어링 파이프라인 실행"""
    print("🚀 키토 스코어링 파이프라인 시작")
    
    try:
        # Supabase 연결
        supabase_conn = SupabaseConnection()
        await supabase_conn.initialize()
        supabase = supabase_conn.client
        print("✅ Supabase 연결 성공")
        
        # 키토 스코어러 초기화
        scorer = KetoScorer(settings)
        print("✅ 키토 스코어러 초기화 성공")
        
        # 1단계: 크롤링 데이터 로드
        print("\n📁 크롤링 데이터 로드...")
        data_file = "data/reports/preprocessed_crawling_test_20250922_015616.json"
        
        with open(data_file, 'r', encoding='utf-8') as f:
            crawling_data = json.load(f)
        
        print(f"✅ {len(crawling_data)}개 레스토랑 데이터 로드")
        
        # 2단계: 레스토랑 데이터 업로드
        print("\n🏪 레스토랑 데이터 업로드...")
        restaurant_count = 0
        restaurant_mapping = {}  # 원본 이름 → UUID 매핑
        
        for item in crawling_data:
            restaurant_info = item['restaurant']
            
            # Address 객체 생성 (좌표는 임시로 서울 중심 사용)
            address = Address(
                addr_road=restaurant_info['address'],
                latitude=37.5665,  # 서울 중심 좌표
                longitude=126.9780
            )
            
            # Restaurant 객체 생성
            restaurant = Restaurant(
                name=restaurant_info['name'],
                address=address,
                phone=restaurant_info.get('phone'),
                source=restaurant_info.get('source_name', 'diningcode'),
                source_url=restaurant_info.get('source_url', '')
            )
            
            # DB 저장 데이터 준비 (필수 필드 포함)
            restaurant_data = {
                'id': str(restaurant.id),
                'name': restaurant.name,
                'addr_road': restaurant.address.addr_road,
                'lat': restaurant.address.latitude,
                'lng': restaurant.address.longitude,
                'source': restaurant_info.get('source_name', 'diningcode'),
                'source_url': restaurant_info.get('source_url', '')
            }
            
            # 선택적 필드 추가 (존재하는 경우만)
            if restaurant.phone:
                restaurant_data['phone'] = restaurant.phone
            
            # Supabase에 저장
            try:
                restaurant_result = supabase.table('restaurant').insert(restaurant_data).execute()
                restaurant_mapping[restaurant_info['name']] = str(restaurant.id)
                restaurant_count += 1
                print(f"  ✅ [{restaurant_count}] {restaurant.name}")
                
            except Exception as e:
                print(f"  ❌ 레스토랑 저장 실패: {restaurant.name} - {e}")
                continue
        
        print(f"✅ 총 {restaurant_count}개 레스토랑 업로드 완료")
        
        # 3단계: 메뉴 데이터 업로드
        print("\n🍽️  메뉴 데이터 업로드...")
        menu_count = 0
        menu_objects = []  # 키토 점수 계산용
        
        for item in crawling_data:
            restaurant_info = item['restaurant']
            restaurant_name = restaurant_info['name']
            
            # 레스토랑 ID 찾기
            if restaurant_name not in restaurant_mapping:
                print(f"  ⚠️  레스토랑 ID를 찾을 수 없음: {restaurant_name}")
                continue
                
            restaurant_id = restaurant_mapping[restaurant_name]
            
            # 메뉴들 처리
            for menu_info in item.get('menus', []):
                # Menu 객체 생성
                menu = Menu(
                    name=menu_info['name'],
                    price=menu_info.get('price'),
                    description=menu_info.get('description'),
                    restaurant_id=restaurant_id
                )
                
                # DB 저장 데이터 준비
                menu_data = {
                    'id': str(menu.id),
                    'name': menu.name,
                    'price': menu.price,
                    'description': menu.description,
                    'restaurant_id': menu.restaurant_id,
                    'currency': 'KRW'
                }
                
                # Supabase에 저장
                try:
                    menu_result = supabase.table('menu').insert(menu_data).execute()
                    menu_objects.append(menu)
                    menu_count += 1
                    
                    if menu_count % 10 == 0:
                        print(f"  📊 {menu_count}개 메뉴 업로드 중...")
                        
                except Exception as e:
                    print(f"  ❌ 메뉴 저장 실패: {menu.name} - {e}")
                    continue
        
        print(f"✅ 총 {menu_count}개 메뉴 업로드 완료")
        
        # 4단계: 키토 점수 계산 및 저장
        print(f"\n🧮 키토 점수 계산 및 저장 ({len(menu_objects)}개 메뉴)...")
        
        keto_score_count = 0
        score_stats = []
        
        for i, menu in enumerate(menu_objects, 1):
            try:
                # 키토 점수 계산
                keto_score = await scorer.calculate_score(menu)
                
                # 스키마에 맞게 데이터 변환 (실제 컬럼만 사용)
                penalty_keywords = [
                    kw for kw in keto_score.detected_keywords 
                    if any(r.impact < 0 for r in keto_score.reasons if r.keyword == kw)
                ]
                bonus_keywords = [
                    kw for kw in keto_score.detected_keywords 
                    if any(r.impact > 0 for r in keto_score.reasons if r.keyword == kw)
                ]
                
                # 최소한의 필수 필드만으로 시작
                keto_score_data = {
                    'menu_id': str(menu.id),
                    'score': max(0, min(100, int(keto_score.final_score))),  # 0-100 범위로 제한
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
                
                # DB에 저장
                keto_result = supabase.table('keto_scores').insert(keto_score_data).execute()
                
                keto_score_count += 1
                score_stats.append(keto_score.final_score)
                
                # 진행률 출력
                if i % 20 == 0 or i == len(menu_objects):
                    print(f"  📊 진행률: {i}/{len(menu_objects)} ({i/len(menu_objects)*100:.1f}%)")
                    
            except Exception as e:
                print(f"  ❌ 키토 점수 저장 실패: {menu.name} - {e}")
                continue
        
        print(f"✅ 총 {keto_score_count}개 키토 점수 저장 완료")
        
        # 5단계: 결과 요약
        print("\n📊 최종 결과 요약:")
        print(f"   레스토랑: {restaurant_count}개")
        print(f"   메뉴: {menu_count}개")
        print(f"   키토 점수: {keto_score_count}개")
        
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
        
        # 6단계: 샘플 데이터 확인
        print("\n🔍 저장된 데이터 샘플 확인...")
        
        # 조인 쿼리로 결과 확인
        sample_query = """
            id,
            menu:menu_id(name, price),
            score,
            confidence_score,
            detected_keywords,
            needs_review
        """
        
        sample_result = supabase.table('keto_scores').select(sample_query).order('score', desc=True).limit(5).execute()
        
        if sample_result.data:
            print("✅ 상위 5개 키토 점수:")
            for item in sample_result.data:
                menu_info = item.get('menu', {})
                menu_name = menu_info.get('name', 'N/A')
                price = menu_info.get('price', 'N/A')
                score = item.get('score', 0)
                confidence = item.get('confidence_score', 0)
                keywords = item.get('detected_keywords', [])
                
                print(f"   📋 {menu_name} ({price}원)")
                print(f"      점수: {score}점 (신뢰도: {confidence:.2f})")
                print(f"      키워드: {', '.join(keywords[:3]) if keywords else '없음'}")
                print()
        
        print("🎉 키토 스코어링 파이프라인 완료!")
        
    except Exception as e:
        print(f"❌ 파이프라인 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(complete_keto_scoring_pipeline())
