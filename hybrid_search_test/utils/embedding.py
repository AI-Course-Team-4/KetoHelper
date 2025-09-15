"""
OpenAI 임베딩 생성 유틸리티
"""
import time
from typing import List, Optional
from openai import OpenAI
from ..config.settings import config

class EmbeddingGenerator:
    """OpenAI 임베딩 생성기"""
    
    def __init__(self):
        self.client: Optional[OpenAI] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """OpenAI 클라이언트 초기화"""
        try:
            if not config.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not found")
            
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            print("✅ OpenAI 클라이언트 초기화 성공")
            
        except Exception as e:
            print(f"❌ OpenAI 클라이언트 초기화 실패: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성"""
        try:
            if not self.client:
                raise ValueError("OpenAI client not initialized")
            
            response = self.client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=text
            )
            
            # API 제한 고려한 딜레이
            time.sleep(0.1)
            
            return response.data[0].embedding
            
        except Exception as e:
            print(f"임베딩 생성 실패: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """배치 임베딩 생성"""
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
                print(f"임베딩 생성 진행: {i+1}/{len(texts)}")
                
            except Exception as e:
                print(f"배치 임베딩 생성 실패 (텍스트 {i+1}): {e}")
                embeddings.append([])  # 빈 리스트로 채움
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """임베딩 차원 반환"""
        return config.EMBEDDING_DIMENSION

# 전역 임베딩 생성기 인스턴스
embedding_generator = EmbeddingGenerator()
