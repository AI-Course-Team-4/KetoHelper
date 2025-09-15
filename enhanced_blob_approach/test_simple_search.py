#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 검색 테스트 (단어별 키워드 검색)
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# 환경설정
load_dotenv('../.env')
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def test_simple_keyword_search():
    """간단한 키워드 검색 테스트"""
    print("=== 간단한 키워드 검색 테스트 ===")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 단어별로 테스트
    test_words = ["김밥", "키토", "케이크", "계란", "다이어트"]
    
    for word in test_words:
        print(f"\n🔍 '{word}' 검색:")
        try:
            result = client.table("recipes_keto_enhanced").select("*").text_search("blob", word).execute()
            if result.data:
                print(f"✅ 결과 {len(result.data)}개:")
                for i, item in enumerate(result.data[:3], 1):
                    print(f"  {i}. {item.get('title', '')[:50]}...")
            else:
                print("❌ 결과 없음")
        except Exception as e:
            print(f"❌ 오류: {e}")

def test_direct_sql_search():
    """직접 SQL로 검색 테스트"""
    print("\n=== 직접 SQL 검색 테스트 ===")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # LIKE 검색으로 테스트
    test_words = ["김밥", "키토", "케이크"]
    
    for word in test_words:
        print(f"\n🔍 '{word}' LIKE 검색:")
        try:
            result = client.table("recipes_keto_enhanced").select("*").ilike("blob", f"%{word}%").limit(5).execute()
            if result.data:
                print(f"✅ 결과 {len(result.data)}개:")
                for i, item in enumerate(result.data, 1):
                    print(f"  {i}. {item.get('title', '')[:50]}...")
            else:
                print("❌ 결과 없음")
        except Exception as e:
            print(f"❌ 오류: {e}")

if __name__ == "__main__":
    test_simple_keyword_search()
    test_direct_sql_search()
