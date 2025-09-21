#!/usr/bin/env python3
"""
이미 업로드된 메뉴들의 키토 점수만 계산해서 저장
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.domain.menu import Menu
from services.scorer.keto_scorer import KetoScorer
from infrastructure.database.supabase_connection import SupabaseConnection
from config.settings import settings

async def calculate_keto_scores_only():
    """이미 업로드된 메뉴들의 키토 점수만 계산"""
    print("🧮 기존 메뉴들의 키토 점수 계산 시작")
    
    try:
        # Supabase 연결
        supabase_conn = SupabaseConnection()
        await supabase_conn.initialize()
        supabase = supabase_conn.client
        print("✅ Supabase 연결 성공")
        
        # 키토 스코어러 초기화
        scorer = KetoScorer(settings)
        print("✅ 키토 스코어러 초기화 성공")
        
        # 1단계: 기존 메뉴들 조회
        print("\n📋 기존 메뉴 데이터 조회...")
        menu_response = supabase.table('menu').select('*').execute()
        
        if not menu_response.data:
            print("❌ 저장된 메뉴가 없습니다")
            return
            
        print(f"✅ {len(menu_response.data)}개 메뉴 발견")
        
        # 2단계: Menu 객체로 변환
        menu_objects = []
        for menu_data in menu_response.data:
            menu = Menu(
                id=menu_data['id'],
                name=menu_data['name'],
                price=menu_data.get('price'),
                description=menu_data.get('description'),
                restaurant_id=menu_data['restaurant_id']
            )
            menu_objects.append(menu)
        
        # 3단계: 키토 점수 계산 및 저장
        print(f"\n🧮 키토 점수 계산 및 저장 ({len(menu_objects)}개 메뉴)...")
        
        keto_score_count = 0
        score_stats = []
        failed_count = 0
        
        for i, menu in enumerate(menu_objects, 1):
            try:
                # 키토 점수 계산
                keto_score = await scorer.calculate_score(menu)
                
                # 스키마에 맞게 데이터 변환
                penalty_keywords = [
                    kw for kw in keto_score.detected_keywords 
                    if any(r.impact < 0 for r in keto_score.reasons if r.keyword == kw)
                ]
                bonus_keywords = [
                    kw for kw in keto_score.detected_keywords 
                    if any(r.impact > 0 for r in keto_score.reasons if r.keyword == kw)
                ]
                
                keto_score_data = {
                    'id': str(uuid4()),
                    'menu_id': str(menu.id),
                    'score': max(0, min(100, int(keto_score.final_score))),  # 0-100 범위로 제한
                    'confidence_score': float(keto_score.confidence),
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
                        'bonus_keywords': bonus_keywords
                    },
                    'detected_keywords': keto_score.detected_keywords,
                    'substitution_tags': None,
                    'negation_detected': any(
                        '제외' in r.explanation or '없는' in r.explanation 
                        for r in keto_score.reasons
                    ),
                    'final_carb_base': None,
                    'override_reason': None,
                    'needs_review': keto_score.confidence < 0.7,
                    'reviewed_at': None,
                    'reviewed_by': None,
                    'rule_version': 'v1.0',
                    'ingredients_confidence': float(keto_score.confidence)
                }
                
                # DB에 저장
                keto_result = supabase.table('keto_scores').insert(keto_score_data).execute()
                
                keto_score_count += 1
                score_stats.append(keto_score.final_score)
                
                # 진행률 출력
                if i % 10 == 0 or i == len(menu_objects):
                    success_rate = (keto_score_count / i) * 100
                    print(f"  📊 진행률: {i}/{len(menu_objects)} ({i/len(menu_objects)*100:.1f}%) | 성공률: {success_rate:.1f}%")
                    
            except Exception as e:
                failed_count += 1
                print(f"  ❌ 키토 점수 저장 실패: {menu.name} - {e}")
                continue
        
        print(f"\n✅ 키토 점수 계산 완료!")
        print(f"   성공: {keto_score_count}개")
        print(f"   실패: {failed_count}개")
        
        # 4단계: 결과 요약
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
        
        # 5단계: 샘플 결과 확인
        print("\n🔍 상위 키토 점수 샘플:")
        
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
            for item in sample_result.data:
                menu_info = item.get('menu', {})
                menu_name = menu_info.get('name', 'N/A')
                price = menu_info.get('price', 'N/A')
                score = item.get('score', 0)
                confidence = item.get('confidence_score', 0)
                keywords = item.get('detected_keywords', [])
                needs_review = item.get('needs_review', False)
                
                # 점수에 따른 라벨
                if score >= 80:
                    label = "🟢 키토 권장"
                elif score >= 50:
                    label = "🟡 조건부 키토"
                elif score >= 20:
                    label = "🟠 키토 주의"
                else:
                    label = "🔴 키토 비추천"
                
                review_icon = "🔍" if needs_review else "✅"
                
                print(f"   {label} {review_icon}")
                print(f"   📋 {menu_name} ({price}원)")
                print(f"   📊 점수: {score}점 (신뢰도: {confidence:.2f})")
                print(f"   🏷️  키워드: {', '.join(keywords[:5]) if keywords else '없음'}")
                print()
        
        print("🎉 키토 점수 계산 완료!")
        
    except Exception as e:
        print(f"❌ 키토 점수 계산 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(calculate_keto_scores_only())
