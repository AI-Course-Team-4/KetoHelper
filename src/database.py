"""
Supabase 데이터베이스 연결 및 관리 모듈
"""
from supabase import create_client, Client
from typing import List, Dict, Any, Optional
import logging

from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        """Supabase 클라이언트 초기화"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL과 KEY가 설정되지 않았습니다")
        
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase 클라이언트 초기화 완료")
    
    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            # 간단한 쿼리로 연결 테스트
            result = self.client.table('menus').select('count').execute()
            logger.info("데이터베이스 연결 테스트 성공")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {e}")
            return False
    
    def create_table(self) -> bool:
        """menus 테이블 생성 (SQL 실행)"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS menus (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            restaurant_name TEXT NOT NULL,
            address TEXT NOT NULL,
            menu_name TEXT NOT NULL,
            price INTEGER,
            menu_text TEXT,
            embedding vector(1536),
            source TEXT DEFAULT 'manual',
            category TEXT,
            rating DECIMAL(2,1),
            image_url TEXT,
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE UNIQUE INDEX IF NOT EXISTS idx_menus_unique 
        ON menus (restaurant_name, address, menu_name);
        
        CREATE INDEX IF NOT EXISTS idx_menus_source ON menus (source);
        CREATE INDEX IF NOT EXISTS idx_menus_category ON menus (category);
        """
        
        try:
            # Supabase에서는 RPC를 통해 SQL 실행
            self.client.rpc('exec_sql', {'sql': create_table_sql}).execute()
            logger.info("테이블 생성 완료")
            return True
        except Exception as e:
            logger.error(f"테이블 생성 실패: {e}")
            return False
    
    def insert_menu(self, menu_data: Dict[str, Any]) -> Optional[str]:
        """단일 메뉴 데이터 삽입"""
        try:
            result = self.client.table('menus').insert(menu_data).execute()
            if result.data:
                logger.info(f"메뉴 삽입 성공: {menu_data['menu_name']}")
                return result.data[0]['id']
            return None
        except Exception as e:
            logger.error(f"메뉴 삽입 실패: {e}")
            return None
    
    def insert_menus_batch(self, menus_data: List[Dict[str, Any]]) -> bool:
        """배치로 메뉴 데이터 삽입"""
        try:
            result = self.client.table('menus').insert(menus_data).execute()
            logger.info(f"배치 삽입 성공: {len(menus_data)}개 메뉴")
            return True
        except Exception as e:
            logger.error(f"배치 삽입 실패: {e}")
            return False
    
    def update_embedding(self, menu_id: str, embedding: List[float]) -> bool:
        """메뉴의 임베딩 업데이트"""
        try:
            result = self.client.table('menus').update({
                'embedding': embedding
            }).eq('id', menu_id).execute()
            return True
        except Exception as e:
            logger.error(f"임베딩 업데이트 실패: {e}")
            return False
    
    def get_menus_without_embedding(self) -> List[Dict[str, Any]]:
        """임베딩이 없는 메뉴들 조회"""
        try:
            result = self.client.table('menus').select('*').is_('embedding', 'null').execute()
            return result.data
        except Exception as e:
            logger.error(f"메뉴 조회 실패: {e}")
            return []
    
    def vector_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """벡터 유사도 검색"""
        try:
            # Supabase의 벡터 검색 함수 사용
            result = self.client.rpc('vector_search', {
                'query_embedding': query_embedding,
                'match_threshold': 0.0,
                'match_count': top_k
            }).execute()
            return result.data
        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return []
    
    def get_menu_count(self) -> int:
        """총 메뉴 개수 조회"""
        try:
            result = self.client.table('menus').select('count').execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            logger.error(f"메뉴 개수 조회 실패: {e}")
            return 0
