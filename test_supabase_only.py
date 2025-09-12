#!/usr/bin/env python3
"""
Supabase 클라이언트만으로 연결 테스트
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 파일 로드
load_dotenv()

async def test_supabase_connection():
    """Supabase 클라이언트 연결 테스트"""
    try:
        # 환경 변수 확인
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        print(f"Supabase URL: {supabase_url}")
        print(f"Supabase Key: {supabase_key[:20]}..." if supabase_key else "None")
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase 환경 변수가 설정되지 않았습니다.")
            return False
        
        # Supabase 클라이언트 생성 (proxy 옵션 제거)
        try:
            supabase: Client = create_client(supabase_url, supabase_key)
            print("✅ Supabase 클라이언트 생성 성공")
        except Exception as e:
            print(f"❌ Supabase 클라이언트 생성 실패: {e}")
            # 다른 방법으로 시도
            try:
                import requests
                # 간단한 HTTP 요청으로 Supabase 연결 테스트
                headers = {
                    'apikey': supabase_key,
                    'Authorization': f'Bearer {supabase_key}'
                }
                response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)
                if response.status_code == 200:
                    print("✅ Supabase HTTP 연결 성공")
                    return True
                else:
                    print(f"❌ Supabase HTTP 연결 실패: {response.status_code}")
                    return False
            except Exception as e2:
                print(f"❌ Supabase HTTP 연결도 실패: {e2}")
                return False
        
        # 간단한 테스트 쿼리 (restaurants 테이블이 있는지 확인)
        try:
            # 테이블 목록 조회 시도
            response = supabase.table('restaurants').select('id').limit(1).execute()
            print("✅ Supabase 테이블 접근 성공")
            print(f"응답: {response}")
            return True
            
        except Exception as e:
            print(f"❌ Supabase 테이블 접근 실패: {e}")
            
            # 테이블이 없을 수도 있으니 다른 방법으로 테스트
            try:
                # 간단한 시스템 쿼리 시도
                response = supabase.rpc('version').execute()
                print("✅ Supabase RPC 호출 성공")
                return True
            except Exception as e2:
                print(f"❌ Supabase RPC 호출도 실패: {e2}")
                return False
        
    except Exception as e:
        print(f"❌ Supabase 클라이언트 생성 실패: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Supabase 연결 테스트 시작...")
    result = asyncio.run(test_supabase_connection())
    
    if result:
        print("✅ Supabase 연결 테스트 성공!")
    else:
        print("❌ Supabase 연결 테스트 실패!")
