#!/usr/bin/env python3
"""
데이터베이스에서 레시피 데이터를 가져와서 인코딩 확인
"""

import asyncio
import sys
import json
sys.path.append('src')

from src.supabase_client import SupabaseClient
from datetime import datetime

async def check_encoding():
    """데이터베이스 데이터 인코딩 확인"""
    print("=== 데이터베이스 레시피 데이터 인코딩 확인 ===")
    print(f"확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        supabase_client = SupabaseClient()
        
        # 최근 5개 레시피 상세 조회
        result = supabase_client.client.table('recipes_keto_raw').select('*').order('fetched_at', desc=True).limit(5).execute()
        
        if result.data:
            print(f"\n=== 최근 크롤링된 레시피 5개 상세 확인 ===")
            
            for i, recipe in enumerate(result.data, 1):
                print(f"\n{'='*60}")
                print(f"레시피 {i}: {recipe.get('title', 'N/A')}")
                print(f"{'='*60}")
                
                # 기본 정보
                print(f"📝 제목: {recipe.get('title', 'N/A')}")
                print(f"👤 작성자: {recipe.get('author', 'N/A')}")
                print(f"⭐ 평점: {recipe.get('rating', 'N/A')}")
                print(f"👀 조회수: {recipe.get('views', 'N/A')}")
                print(f"🍽️ 분량: {recipe.get('servings', 'N/A')}")
                print(f"⏰ 조리시간: {recipe.get('cook_time', 'N/A')}")
                print(f"📊 난이도: {recipe.get('difficulty', 'N/A')}")
                print(f"🔗 URL: {recipe.get('source_url', 'N/A')}")
                
                # 요약
                summary = recipe.get('summary', '')
                if summary:
                    print(f"\n📋 요약:")
                    print(f"   {summary[:200]}{'...' if len(summary) > 200 else ''}")
                
                # 태그
                tags = recipe.get('tags', [])
                if tags:
                    print(f"\n🏷️ 태그: {', '.join(tags[:5])}{'...' if len(tags) > 5 else ''}")
                
                # 재료 정보 상세 확인
                ingredients = recipe.get('ingredients')
                if ingredients:
                    print(f"\n🥘 재료 정보:")
                    if isinstance(ingredients, str):
                        try:
                            ingredients = json.loads(ingredients)
                        except:
                            print(f"   재료 JSON 파싱 실패: {ingredients[:100]}...")
                            continue
                    
                    if isinstance(ingredients, list):
                        print(f"   총 {len(ingredients)}개 재료:")
                        for j, ing in enumerate(ingredients[:8], 1):  # 처음 8개만 표시
                            if isinstance(ing, dict):
                                name = ing.get('name', '')
                                amount = ing.get('amount', '')
                                print(f"   {j:2d}. {name} {amount}".strip())
                            else:
                                print(f"   {j:2d}. {ing}")
                        
                        if len(ingredients) > 8:
                            print(f"   ... 그리고 {len(ingredients) - 8}개 더")
                    else:
                        print(f"   재료 데이터 형식 오류: {type(ingredients)}")
                
                # 조리순서 정보 상세 확인
                steps = recipe.get('steps')
                if steps:
                    print(f"\n👨‍🍳 조리순서:")
                    if isinstance(steps, str):
                        try:
                            steps = json.loads(steps)
                        except:
                            print(f"   조리순서 JSON 파싱 실패: {steps[:100]}...")
                            continue
                    
                    if isinstance(steps, list):
                        print(f"   총 {len(steps)}단계:")
                        for j, step in enumerate(steps[:3], 1):  # 처음 3단계만 표시
                            if isinstance(step, dict):
                                step_num = step.get('step', j)
                                step_text = step.get('text', '')
                                print(f"   {step_num:2d}. {step_text[:100]}{'...' if len(step_text) > 100 else ''}")
                            else:
                                print(f"   {j:2d}. {step}")
                        
                        if len(steps) > 3:
                            print(f"   ... 그리고 {len(steps) - 3}단계 더")
                    else:
                        print(f"   조리순서 데이터 형식 오류: {type(steps)}")
                
                # 이미지
                images = recipe.get('images', [])
                if images:
                    print(f"\n🖼️ 이미지: {len(images)}개")
                    for j, img in enumerate(images[:2], 1):  # 처음 2개만 표시
                        print(f"   {j}. {img}")
                    if len(images) > 2:
                        print(f"   ... 그리고 {len(images) - 2}개 더")
                
                # 크롤링 시간
                fetched_at = recipe.get('fetched_at', '')
                if fetched_at:
                    print(f"\n⏰ 크롤링 시간: {fetched_at}")
                
                # embedding_blob 확인
                embedding_blob = recipe.get('embedding_blob', '')
                if embedding_blob:
                    print(f"\n🔍 검색용 텍스트 (처음 200자):")
                    print(f"   {embedding_blob[:200]}{'...' if len(embedding_blob) > 200 else ''}")
        
        else:
            print("데이터베이스에 레시피가 없습니다.")
        
        # 인코딩 문제가 있는 데이터 확인
        print(f"\n{'='*60}")
        print("=== 인코딩 문제 검사 ===")
        
        # 특수 문자가 포함된 데이터 찾기
        special_chars_result = supabase_client.client.table('recipes_keto_raw').select('title, ingredients, steps').execute()
        
        if special_chars_result.data:
            encoding_issues = []
            for recipe in special_chars_result.data:
                title = recipe.get('title', '')
                ingredients = recipe.get('ingredients', '')
                steps = recipe.get('steps', '')
                
                # 인코딩 문제 패턴 검사
                if any(char in str(title) for char in ['\\u', 'ë', 'ì', 'í', 'ê', 'ë']):
                    encoding_issues.append(f"제목 인코딩 문제: {title[:50]}...")
                
                if any(char in str(ingredients) for char in ['\\u', 'ë', 'ì', 'í', 'ê', 'ë']):
                    encoding_issues.append(f"재료 인코딩 문제: {str(ingredients)[:50]}...")
                
                if any(char in str(steps) for char in ['\\u', 'ë', 'ì', 'í', 'ê', 'ë']):
                    encoding_issues.append(f"조리순서 인코딩 문제: {str(steps)[:50]}...")
            
            if encoding_issues:
                print(f"발견된 인코딩 문제 ({len(encoding_issues)}개):")
                for issue in encoding_issues[:10]:  # 처음 10개만 표시
                    print(f"   - {issue}")
                if len(encoding_issues) > 10:
                    print(f"   ... 그리고 {len(encoding_issues) - 10}개 더")
            else:
                print("✅ 인코딩 문제가 발견되지 않았습니다!")
        
    except Exception as e:
        print(f"데이터 확인 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_encoding())
