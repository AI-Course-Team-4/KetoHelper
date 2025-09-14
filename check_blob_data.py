#!/usr/bin/env python3
"""
Supabase에서 blob 데이터 직접 확인
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import json

# .env 파일 로드
load_dotenv()

def check_blob_data():
    """Supabase에서 blob 데이터 확인"""
    print("=== Blob 데이터 확인 ===\n")
    
    # Supabase 클라이언트 설정
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("환경변수가 설정되지 않았습니다.")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    # 각 테이블별로 데이터 확인
    tables = [
        ("recipes_title_blob", "방식1 (Title + Blob)"),
        ("recipes_no_title_blob", "방식2 (No Title + Blob)"),
        ("recipes_llm_preprocessing", "방식3 (LLM Preprocessing)")
    ]
    
    for table_name, approach_name in tables:
        print(f"=== {approach_name} ===")
        
        try:
            # 데이터 조회
            result = supabase.table(table_name).select('*').limit(3).execute()
            
            if result.data:
                print(f"총 데이터 수: {len(result.data)}개 (샘플 3개)")
                print()
                
                for i, row in enumerate(result.data, 1):
                    print(f"--- 샘플 {i} ---")
                    print(f"레시피 ID: {row.get('recipe_id', 'N/A')}")
                    print(f"제목: {row.get('title', 'N/A')}")
                    
                    # processed_content 확인
                    processed_content = row.get('processed_content', '')
                    print(f"처리된 내용: {str(processed_content)[:200]}{'...' if len(str(processed_content)) > 200 else ''}")
                    
                    # 메타데이터 확인
                    metadata = row.get('metadata', {})
                    print(f"메타데이터: {metadata}")
                    
                    print()
                
                # 전체 통계
                all_result = supabase.table(table_name).select('*').execute()
                total_count = len(all_result.data)
                print(f"📊 총 레시피 수: {total_count}")
                
            else:
                print("데이터가 없습니다.")
                
        except Exception as e:
            print(f"오류: {e}")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    check_blob_data()
