#!/usr/bin/env python3
"""
pgvector 스키마 수정 적용
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def apply_pgvector_fix():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    
    print("=== pgvector 스키마 수정 시작 ===")
    
    # SQL 파일 읽기
    with open('fix_pgvector_schema.sql', 'r', encoding='utf-8') as f:
        sql_commands = f.read()
    
    # SQL 명령어들을 세미콜론으로 분리
    commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
    
    for i, command in enumerate(commands, 1):
        if not command:
            continue
            
        print(f"\n{i}. 실행 중: {command[:50]}...")
        try:
            # Supabase에서 SQL 실행
            result = client.rpc('exec_sql', {'sql': command}).execute()
            print(f"   ✅ 성공")
        except Exception as e:
            print(f"   ❌ 실패: {e}")
            # 일부 명령어는 실패할 수 있음 (이미 존재하는 경우 등)
            if "already exists" in str(e).lower() or "does not exist" in str(e).lower():
                print(f"   ℹ️ 이미 존재하거나 존재하지 않음 (정상)")
            else:
                print(f"   ⚠️ 예상치 못한 오류")
    
    print(f"\n=== 스키마 수정 완료 ===")
    
    # 수정 후 테이블 구조 확인
    print(f"\n=== 수정 후 테이블 구조 확인 ===")
    try:
        # 샘플 데이터로 embedding 타입 확인
        result = client.table('recipes_hybrid_ingredient_llm').select('recipe_id, title, embedding').limit(1).execute()
        if result.data:
            sample = result.data[0]
            embedding = sample.get('embedding')
            print(f"샘플 데이터:")
            print(f"  - 제목: {sample['title']}")
            print(f"  - embedding 타입: {type(embedding)}")
            if hasattr(embedding, '__len__'):
                print(f"  - embedding 길이: {len(embedding)}")
            else:
                print(f"  - embedding 값: {str(embedding)[:100]}...")
        else:
            print("데이터가 없습니다.")
    except Exception as e:
        print(f"테이블 확인 실패: {e}")

if __name__ == "__main__":
    apply_pgvector_fix()
