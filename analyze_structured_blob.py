#!/usr/bin/env python3
"""
structured_blob 콘텐츠 분석
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def analyze_structured_blob():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    
    print("=== structured_blob 콘텐츠 분석 ===")
    
    # 샘플 데이터 가져오기
    result = client.table('recipes_hybrid_ingredient_llm').select('title, structured_blob, llm_metadata, basic_metadata').limit(5).execute()
    
    for i, row in enumerate(result.data, 1):
        print(f"\n{i}. {row['title']}")
        print(f"   structured_blob: {row['structured_blob']}")
        print(f"   llm_metadata: {row['llm_metadata']}")
        print(f"   basic_metadata: {row['basic_metadata']}")
        print(f"   ---")

if __name__ == "__main__":
    analyze_structured_blob()
