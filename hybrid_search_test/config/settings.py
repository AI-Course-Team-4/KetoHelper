"""
하이브리드 검색 테스트 설정
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv('.env')

class SearchConfig:
    """검색 설정 클래스"""
    
    # Supabase 설정
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    TABLE_NAME = 'recipes_hybrid_ingredient_llm'
    
    # OpenAI 설정
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    EMBEDDING_MODEL = 'text-embedding-3-small'
    EMBEDDING_DIMENSION = 1536
    
    # 검색 설정
    DEFAULT_TOP_K = 10
    MAX_TOP_K = 50
    
    # 하이브리드 검색 가중치
    VECTOR_WEIGHT = 0.7  # 벡터 검색 가중치
    KEYWORD_WEIGHT = 0.3  # 키워드 검색 가중치
    
    # 유사도 점수 정규화
    MIN_SIMILARITY = 0.0
    MAX_SIMILARITY = 1.0
    TARGET_MIN_SCORE = 0.0
    TARGET_MAX_SCORE = 100.0
    
    # 검색 타임아웃 (초)
    SEARCH_TIMEOUT = 30
    
    # 캐시 설정
    ENABLE_CACHE = True
    CACHE_TTL = 3600  # 1시간
    
    @classmethod
    def validate_config(cls) -> bool:
        """설정 유효성 검사"""
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY', 
            'OPENAI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Missing environment variables: {missing_vars}")
            return False
        
        return True
    
    @classmethod
    def get_search_weights(cls) -> Dict[str, float]:
        """검색 가중치 반환"""
        return {
            'vector': cls.VECTOR_WEIGHT,
            'keyword': cls.KEYWORD_WEIGHT
        }
    
    @classmethod
    def normalize_score(cls, similarity: float) -> float:
        """유사도 점수를 0-100% 범위로 정규화"""
        # 코사인 유사도는 -1 ~ 1 범위이지만, 실제로는 0 ~ 1 범위
        # 0 ~ 1을 0 ~ 100으로 변환
        normalized = max(0, min(1, similarity))  # 0~1 범위로 클램핑
        return normalized * 100  # 0~100% 범위로 변환

# 전역 설정 인스턴스
config = SearchConfig()
