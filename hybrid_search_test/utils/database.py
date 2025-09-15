"""
Supabase 데이터베이스 연결 및 쿼리 유틸리티
"""
import time
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from ..config.settings import config

class DatabaseManager:
    """Supabase 데이터베이스 관리자"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._connect()
    
    def _connect(self):
        """Supabase 클라이언트 연결"""
        try:
            if not config.validate_config():
                raise ValueError("Invalid configuration")
            
            self.client = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_ANON_KEY
            )
            print("✅ Supabase 연결 성공")
            
        except Exception as e:
            print(f"❌ Supabase 연결 실패: {e}")
            raise
    
    def get_table_info(self) -> Dict[str, Any]:
        """테이블 정보 조회"""
        try:
            result = self.client.table(config.TABLE_NAME).select('*').limit(1).execute()
            return {
                'table_name': config.TABLE_NAME,
                'has_data': len(result.data) > 0,
                'sample_count': len(result.data)
            }
        except Exception as e:
            print(f"테이블 정보 조회 실패: {e}")
            return {'error': str(e)}
    
    def get_total_count(self) -> int:
        """전체 레시피 수 조회"""
        try:
            result = self.client.table(config.TABLE_NAME).select('recipe_id', count='exact').execute()
            return result.count or 0
        except Exception as e:
            print(f"전체 수 조회 실패: {e}")
            return 0
    
    def get_sample_recipes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """샘플 레시피 조회"""
        try:
            result = self.client.table(config.TABLE_NAME).select('*').limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"샘플 레시피 조회 실패: {e}")
            return []
    
    def search_by_keyword(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """키워드 검색 (full-text search)"""
        try:
            # Supabase의 full-text search 사용
            result = self.client.table(config.TABLE_NAME).select('*').text_search(
                'structured_blob', query
            ).execute()
            
            # 결과를 limit만큼 자르기
            return result.data[:limit]
            
        except Exception as e:
            print(f"키워드 검색 실패: {e}")
            return []
    
    def search_by_vector(self, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """벡터 검색 (pgvector)"""
        try:
            # pgvector 함수 사용
            result = self.client.rpc('search_hybrid_recipes', {
                'query_embedding': query_embedding,
                'match_count': limit
            }).execute()
            
            if result.data:
                return result.data
            else:
                # fallback: 모든 데이터를 가져와서 클라이언트에서 계산
                return self._fallback_vector_search(query_embedding, limit)
            
        except Exception as e:
            print(f"벡터 검색 실패: {e}")
            # fallback 검색
            return self._fallback_vector_search(query_embedding, limit)
    
    def _fallback_vector_search(self, query_embedding: List[float], limit: int) -> List[Dict[str, Any]]:
        """백업 벡터 검색 - 모든 데이터를 가져와서 클라이언트에서 유사도 계산"""
        try:
            import numpy as np
            
            result = self.client.table(config.TABLE_NAME).select('*').execute()
            
            results = []
            query_embedding = np.array(query_embedding, dtype=np.float32)
            
            for row in result.data:
                embedding_data = row.get('embedding')
                if not embedding_data:
                    continue
                
                # embedding이 문자열인 경우 파싱
                if isinstance(embedding_data, str):
                    try:
                        import json
                        embedding_data = json.loads(embedding_data)
                    except:
                        continue
                
                # 데이터 타입을 float로 변환
                stored_embedding = np.array(embedding_data, dtype=np.float32)
                query_embedding_float = query_embedding.astype(np.float32)
                
                # 코사인 유사도 계산
                norm_query = np.linalg.norm(query_embedding_float)
                norm_stored = np.linalg.norm(stored_embedding)
                
                if norm_query == 0 or norm_stored == 0:
                    similarity = 0.0
                else:
                    similarity = np.dot(query_embedding_float, stored_embedding) / (norm_query * norm_stored)
                
                results.append({
                    'recipe_id': row['recipe_id'],
                    'title': row['title'],
                    'structured_blob': row.get('structured_blob', ''),
                    'llm_metadata': row.get('llm_metadata', {}),
                    'basic_metadata': row.get('basic_metadata', {}),
                    'similarity': float(similarity)
                })
            
            # 유사도 순으로 정렬하고 상위 k개 반환
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            print(f"백업 벡터 검색 실패: {e}")
            return []
    
    def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """레시피 ID로 단일 레시피 조회"""
        try:
            result = self.client.table(config.TABLE_NAME).select('*').eq('recipe_id', recipe_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"레시피 조회 실패: {e}")
            return None

# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()
