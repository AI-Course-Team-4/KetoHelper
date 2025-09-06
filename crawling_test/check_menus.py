#!/usr/bin/env python3
"""
메뉴 상태 확인 스크립트
"""
from database_adapter import DatabaseAdapter

def main():
    db = DatabaseAdapter()
    
    print("📋 최근 메뉴 목록:")
    result = db.client.table('menus').select(
        'id, name, restaurant_id, embedding, restaurants(name)'
    ).order('created_at', desc=True).limit(10).execute()
    
    for menu in result.data:
        has_embedding = '✅' if menu['embedding'] else '❌'
        restaurant_name = menu['restaurants']['name'] if menu['restaurants'] else 'Unknown'
        print(f"  {has_embedding} {menu['name']} ({restaurant_name})")
    
    # 임베딩 없는 메뉴들 확인  
    no_embedding = db.client.table('menus').select(
        'id, name, restaurants(name)'
    ).is_('embedding', 'null').execute()
    
    print(f"\n⏳ 임베딩 대기 중인 메뉴: {len(no_embedding.data)}개")
    for menu in no_embedding.data:
        restaurant_name = menu['restaurants']['name'] if menu['restaurants'] else 'Unknown'
        print(f"  - {menu['name']} ({restaurant_name})")

if __name__ == "__main__":
    main()
