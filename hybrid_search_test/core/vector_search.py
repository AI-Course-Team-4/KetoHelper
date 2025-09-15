"""
벡터 검색 엔진
pgvector 코사인 유사도 활용
"""
import time
from typing import List, Dict, Any
from ..utils.database import db_manager
from ..utils.embedding import embedding_generator
from ..utils.similarity import similarity_calculator
from ..utils.formatter import result_formatter
from ..config.settings import config

class VectorSearchEngine:
    """벡터 검색 엔진"""
    
    def __init__(self):
        self.db = db_manager
        self.embedding = embedding_generator
        self.similarity = similarity_calculator
        self.formatter = result_formatter
    
    def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """벡터 검색 실행"""
        if top_k is None:
            top_k = config.DEFAULT_TOP_K
        
        start_time = time.time()
        
        try:
            # 1. 쿼리 임베딩 생성
            query_embedding = self.embedding.generate_embedding(query)
            
            # 2. pgvector 검색 실행
            raw_results = self.db.search_by_vector(query_embedding, top_k)
            
            # 3. 결과 포맷팅
            formatted_results = self.formatter.format_search_results(raw_results, 'vector')
            
            # 4. 순위 추가
            final_results = self.similarity.add_rank_to_results(formatted_results)
            
            search_time = (time.time() - start_time) * 1000  # ms
            
            print(f"🔍 벡터 검색 완료: {len(final_results)}개 결과, {search_time:.1f}ms")
            
            return final_results
            
        except Exception as e:
            print(f"❌ 벡터 검색 실패: {e}")
            return []
    
    def search_with_embedding(self, query_embedding: List[float], top_k: int = None) -> List[Dict[str, Any]]:
        """이미 생성된 임베딩으로 벡터 검색"""
        if top_k is None:
            top_k = config.DEFAULT_TOP_K
        
        start_time = time.time()
        
        try:
            # pgvector 검색 실행
            raw_results = self.db.search_by_vector(query_embedding, top_k)
            
            # 결과 포맷팅
            formatted_results = self.formatter.format_search_results(raw_results, 'vector')
            
            # 순위 추가
            final_results = self.similarity.add_rank_to_results(formatted_results)
            
            search_time = (time.time() - start_time) * 1000  # ms
            
            print(f"🔍 벡터 검색 완료: {len(final_results)}개 결과, {search_time:.1f}ms")
            
            return final_results
            
        except Exception as e:
            print(f"❌ 벡터 검색 실패: {e}")
            return []
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간의 벡터 유사도 계산"""
        try:
            # 두 텍스트의 임베딩 생성
            embedding1 = self.embedding.generate_embedding(text1)
            embedding2 = self.embedding.generate_embedding(text2)
            
            # 코사인 유사도 계산
            similarity = self.similarity.cosine_similarity(embedding1, embedding2)
            
            return similarity
            
        except Exception as e:
            print(f"유사도 계산 실패: {e}")
            return 0.0
    
    def get_search_stats(self) -> Dict[str, Any]:
        """검색 엔진 통계"""
        try:
            total_count = self.db.get_total_count()
            return {
                'search_type': 'vector',
                'total_recipes': total_count,
                'search_method': 'pgvector cosine similarity',
                'embedding_model': config.EMBEDDING_MODEL,
                'embedding_dimension': config.EMBEDDING_DIMENSION
            }
        except Exception as e:
            return {'error': str(e)}

# 전역 벡터 검색 엔진 인스턴스
vector_search_engine = VectorSearchEngine()
