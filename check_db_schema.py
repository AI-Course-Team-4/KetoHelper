#!/usr/bin/env python3
"""
Supabase 데이터베이스 스키마 확인
"""

import os
import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def check_supabase_schema():
    """Supabase 데이터베이스 스키마 확인"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase 환경 변수가 설정되지 않았습니다.")
            return False
        
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # 테이블 목록 확인
        tables_to_check = ['restaurants', 'menus', 'crawl_jobs']
        
        for table in tables_to_check:
            try:
                # 테이블 존재 여부 확인 (간단한 쿼리로)
                response = requests.get(
                    f"{supabase_url}/rest/v1/{table}?select=id&limit=1",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"✅ {table} 테이블 존재함")
                elif response.status_code == 404:
                    print(f"❌ {table} 테이블이 존재하지 않음")
                else:
                    print(f"⚠️ {table} 테이블 확인 실패: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {table} 테이블 확인 중 오류: {e}")
        
        # 테이블 스키마 정보 확인
        try:
            response = requests.get(
                f"{supabase_url}/rest/v1/",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Supabase REST API 접근 가능")
                return True
            else:
                print(f"❌ Supabase REST API 접근 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Supabase REST API 접근 중 오류: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 스키마 확인 중 오류: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Supabase 데이터베이스 스키마 확인 시작...")
    result = check_supabase_schema()
    
    if result:
        print("✅ 스키마 확인 완료!")
    else:
        print("❌ 스키마 확인 실패!")
