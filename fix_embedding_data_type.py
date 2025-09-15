#!/usr/bin/env python3
"""
임베딩 데이터 타입 수정 스크립트
"""
from supabase import create_client
import os
from dotenv import load_dotenv
import json
import numpy as np

load_dotenv()

def fix_embedding_data_type():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    
    print("=== 임베딩 데이터 타입 수정 시작 ===")
    
    # 1. 현재 데이터 확인
    print("\n1. 현재 데이터 상태 확인:")
    result = client.table('recipes_hybrid_ingredient_llm').select('recipe_id, title, embedding').limit(3).execute()
    
    for i, row in enumerate(result.data, 1):
        print(f"\n{i}. {row['title']}")
        embedding = row.get('embedding')
        print(f"   - embedding 타입: {type(embedding)}")
        print(f"   - embedding 길이: {len(str(embedding))}")
        
        if isinstance(embedding, str):
            print(f"   - 문자열로 저장됨 (문제!)")
            try:
                # 문자열을 리스트로 파싱
                parsed_embedding = json.loads(embedding)
                print(f"   - 파싱 후 타입: {type(parsed_embedding)}")
                print(f"   - 파싱 후 길이: {len(parsed_embedding)}")
            except Exception as e:
                print(f"   - 파싱 실패: {e}")
        else:
            print(f"   - 정상적인 리스트 타입")
    
    # 2. 데이터 수정
    print("\n2. 데이터 수정 시작:")
    all_data = client.table('recipes_hybrid_ingredient_llm').select('*').execute()
    
    updated_count = 0
    for row in all_data.data:
        embedding = row.get('embedding')
        
        if isinstance(embedding, str):
            try:
                # 문자열을 리스트로 파싱
                parsed_embedding = json.loads(embedding)
                
                # 데이터 업데이트
                update_result = client.table('recipes_hybrid_ingredient_llm').update({
                    'embedding': parsed_embedding
                }).eq('recipe_id', row['recipe_id']).execute()
                
                updated_count += 1
                print(f"   ✅ {row['title']} - 임베딩 타입 수정 완료")
                
            except Exception as e:
                print(f"   ❌ {row['title']} - 수정 실패: {e}")
        else:
            print(f"   ⏭️ {row['title']} - 이미 정상 타입")
    
    print(f"\n3. 수정 완료: {updated_count}개 레코드 업데이트")
    
    # 4. 수정 후 확인
    print("\n4. 수정 후 데이터 확인:")
    result = client.table('recipes_hybrid_ingredient_llm').select('recipe_id, title, embedding').limit(3).execute()
    
    for i, row in enumerate(result.data, 1):
        print(f"\n{i}. {row['title']}")
        embedding = row.get('embedding')
        print(f"   - embedding 타입: {type(embedding)}")
        
        if isinstance(embedding, list):
            print(f"   - ✅ 정상적인 리스트 타입")
            print(f"   - embedding 길이: {len(embedding)}")
            print(f"   - embedding 범위: {min(embedding):.4f} ~ {max(embedding):.4f}")
        else:
            print(f"   - ❌ 여전히 문제 있음")

if __name__ == "__main__":
    fix_embedding_data_type()
