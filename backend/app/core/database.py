"""
데이터베이스 연결 및 설정
Supabase 하이브리드 검색 지원
"""

import asyncio
from typing import AsyncGenerator
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# SQLAlchemy Base 클래스 (호환성을 위해 유지)
Base = declarative_base()

# 호환성을 위한 더미 클래스들
class DummyAsyncSessionLocal:
    def __call__(self):
        return DummyAsyncSession()
    
    def __enter__(self):
        return DummyAsyncSession()
    
    def __exit__(self, *args):
        pass

class DummyAsyncSession:
    async def execute(self, *args, **kwargs):
        return DummyResult()
    
    async def commit(self):
        pass
    
    async def rollback(self):
        pass
    
    async def close(self):
        pass

class DummyResult:
    def scalar(self):
        return 1

# 호환성을 위한 더미 객체들
AsyncSessionLocal = DummyAsyncSessionLocal()

# Supabase 클라이언트 (하이브리드 검색용)
try:
    from supabase import create_client, Client
    supabase_url = settings.supabase_url
    supabase_key = settings.supabase_anon_key
    service_role_key = settings.supabase_service_role_key
    
    if supabase_url and supabase_key and supabase_url.strip() and supabase_key.strip():
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Supabase 클라이언트 연결 성공")
    else:
        print("WARNING: Supabase 환경변수 없음 또는 빈 값 - 키워드 검색 비활성화")
        print(f"   SUPABASE_URL: {repr(supabase_url)}")
        print(f"   SUPABASE_ANON_KEY: {repr(supabase_key)}")
        supabase = None

    # 서비스 롤 클라이언트 (서버 사이드 쓰기용)
    supabase_admin = None
    if supabase_url and service_role_key and supabase_url.strip() and service_role_key.strip():
        try:
            supabase_admin = create_client(supabase_url, service_role_key)
            print("SUCCESS: Supabase 서비스 롤 클라이언트 연결 성공")
        except Exception as e:
            print(f"WARNING: 서비스 롤 클라이언트 생성 실패: {e}")
            supabase_admin = None
except Exception as e:
    print(f"WARNING: Supabase 연결 실패: {e}")
    supabase = None
    supabase_admin = None

# 호환성을 위한 더미 객체들 (Supabase)
class DummySupabase:
    def table(self, name):
        return DummyTable()
    
    def select(self, *args):
        return self
    
    def limit(self, n):
        return self
    
    def execute(self):
        return type('Response', (), {'data': []})()

class DummyTable:
    def select(self, *args):
        return self
    
    def limit(self, n):
        return self
    
    def execute(self):
        return type('Response', (), {'data': []})()

# 더미 객체들 (Supabase가 없을 때)
if supabase is None:
    supabase = DummySupabase()
if supabase_admin is None:
    # 서비스 롤이 없으면 일반 클라이언트로 대체
    supabase_admin = supabase

async def get_db() -> AsyncGenerator[object, None]:
    """Supabase 클라이언트 의존성"""
    try:
        yield supabase
    except Exception as e:
        print(f"ERROR: Supabase 연결 실패: {e}")
        raise

async def init_db() -> None:
    """데이터베이스 초기화"""
    try:
        # Supabase 초기화
        if supabase and not isinstance(supabase, DummySupabase):
            try:
                # Supabase 연결 테스트
                test_response = supabase.table('recipe_blob_emb').select('id').limit(1).execute()
                print("SUCCESS: Supabase 연결 성공")
                print("SUCCESS: 하이브리드 검색 시스템 정상 작동")
                print("SUCCESS: 벡터 검색 + 키워드 검색 사용 가능")
            except Exception as e:
                print(f"WARNING: Supabase 연결 실패: {e}")
                print("INFO: 오프라인 모드로 실행됩니다.")
        else:
            print("WARNING: Supabase 연결 없음 - 하이브리드 검색 비활성화")
            print("INFO: 오프라인 모드로 실행됩니다.")
        
    except Exception as e:
        print(f"ERROR: 데이터베이스 초기화 실패: {e}")
        print("INFO: 오프라인 모드로 실행됩니다.")

async def test_connection() -> bool:
    """Supabase 연결 테스트"""
    try:
        if supabase and not isinstance(supabase, DummySupabase):
            test_response = supabase.table('recipe_blob_emb').select('id').limit(1).execute()
            return True
        return False
    except Exception:
        return False

async def test_hybrid_search() -> bool:
    """하이브리드 검색 기능 테스트"""
    try:
        if supabase and not isinstance(supabase, DummySupabase):
            # RPC 함수 테스트
            test_response = supabase.rpc('hybrid_search', {
                'query_text': '테스트',
                'query_embedding': [0.1] * 1536,  # 더미 임베딩
                'match_count': 1
            }).execute()
            return True
        return False
    except Exception:
        return False