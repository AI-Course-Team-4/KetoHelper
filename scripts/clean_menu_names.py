#!/usr/bin/env python3
"""
Supabase에 업로드된 메뉴명 전처리 스크립트
"""

import asyncio
import sys
import re
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.database.supabase_connection import supabase_connection

def clean_menu_name(name: str) -> str:
    """메뉴명 전처리 함수"""
    if not name:
        return name
        
    original_name = name
    
    # 1. "메뉴정보" 접두사 제거
    name = name.replace("메뉴정보 ", "")
    
    # 2. "추천 숫자" 패턴 제거 (예: "추천 1", "추천 2")
    name = re.sub(r'\s+추천\s+\d+$', '', name)
    
    # 3. 끝의 단독 숫자 제거 (예: "돈육전 1" -> "돈육전")
    # 단, 용량/수량 정보는 보존 (예: "150g", "500ml")
    name = re.sub(r'\s+\d+$', '', name)
    
    # 4. 연속된 공백을 하나로 정리
    name = re.sub(r'\s+', ' ', name)
    
    # 5. 앞뒤 공백 제거
    name = name.strip()
    
    # 6. 빈 문자열이 되면 원본 반환
    if not name:
        return original_name
        
    return name

async def update_menu_names():
    """메뉴명 전처리 및 업데이트"""
    try:
        await supabase_connection.initialize()
        print("Supabase 연결 성공!")
        
        # 모든 메뉴 조회
        all_menus = supabase_connection.client.table('menu').select('id, name').execute()
        print(f"총 {len(all_menus.data)}개 메뉴 조회")
        
        updated_count = 0
        unchanged_count = 0
        
        print("\n=== 메뉴명 전처리 시작 ===")
        
        for menu in all_menus.data:
            menu_id = menu['id']
            original_name = menu['name']
            cleaned_name = clean_menu_name(original_name)
            
            if original_name != cleaned_name:
                print(f"변경: '{original_name}' -> '{cleaned_name}'")
                
                # Supabase에서 메뉴명 업데이트
                try:
                    result = supabase_connection.client.table('menu').update({
                        'name': cleaned_name
                    }).eq('id', menu_id).execute()
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"업데이트 실패 (ID: {menu_id}): {e}")
                    
            else:
                unchanged_count += 1
                
        print(f"\n=== 전처리 완료 ===")
        print(f"변경된 메뉴: {updated_count}개")
        print(f"변경되지 않은 메뉴: {unchanged_count}개")
        
        # 결과 확인
        print(f"\n=== 전처리 후 샘플 확인 ===")
        updated_menus = supabase_connection.client.table('menu').select('name, price').limit(15).execute()
        
        for menu in updated_menus.data:
            print(f"- {menu['name']} ({menu['price']}원)")
            
    except Exception as e:
        print(f"메뉴명 전처리 실패: {e}")

async def preview_changes():
    """변경 사항 미리보기 (실제 업데이트 없이)"""
    try:
        await supabase_connection.initialize()
        print("=== 메뉴명 전처리 미리보기 ===")
        
        # 모든 메뉴 조회
        all_menus = supabase_connection.client.table('menu').select('id, name').limit(30).execute()
        
        changes = []
        
        for menu in all_menus.data:
            original_name = menu['name']
            cleaned_name = clean_menu_name(original_name)
            
            if original_name != cleaned_name:
                changes.append((original_name, cleaned_name))
                
        print(f"변경 예정: {len(changes)}개")
        print()
        
        for original, cleaned in changes[:15]:  # 처음 15개만 출력
            print(f"'{original}' -> '{cleaned}'")
            
        if len(changes) > 15:
            print(f"... 외 {len(changes) - 15}개 더")
            
        return len(changes)
        
    except Exception as e:
        print(f"미리보기 실패: {e}")
        return 0

async def main():
    """메인 함수"""
    print("메뉴명 전처리 스크립트")
    print("1. 미리보기만 실행")
    print("2. 실제 업데이트 실행")
    
    # 일단 미리보기부터 실행
    change_count = await preview_changes()
    
    if change_count > 0:
        print(f"\n{change_count}개 메뉴명이 변경될 예정입니다.")
        print("실제 업데이트를 진행하시겠습니까? (y/N): ", end="")
        
        # 자동으로 진행 (사용자 입력 없이)
        print("y")
        await update_menu_names()
    else:
        print("변경할 메뉴명이 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
