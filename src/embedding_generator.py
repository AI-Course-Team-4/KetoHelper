"""
OpenAI API를 사용한 임베딩 벡터 생성 모듈
텍스트를 벡터로 변환하여 의미적 검색을 가능하게 함
"""

import os
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from openai import OpenAI
from loguru import logger
from tqdm import tqdm
import json


@dataclass
class EmbeddingConfig:
    """임베딩 설정 클래스"""
    model: str = "text-embedding-3-small"
    dimension: int = 1536
    batch_size: int = 50
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_delay: float = 0.1


class EmbeddingGenerator:
    """OpenAI API를 사용한 임베딩 생성기"""
    
    def __init__(self, api_key: str, config: Optional[EmbeddingConfig] = None):
        """
        Args:
            api_key: OpenAI API 키
            config: 임베딩 설정
        """
        self.client = OpenAI(api_key=api_key)
        self.config = config or EmbeddingConfig()
        self.total_tokens_used = 0
        
        logger.info(f"임베딩 생성기 초기화 완료 - 모델: {self.config.model}")
    
    def estimate_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 추정 (대략적)"""
        # 한글의 경우 대략 1.5 토큰/글자, 영문의 경우 0.25 토큰/글자로 추정
        korean_chars = len([c for c in text if '가' <= c <= '힣'])
        other_chars = len(text) - korean_chars
        
        estimated_tokens = int(korean_chars * 1.5 + other_chars * 0.25)
        return max(1, estimated_tokens)
    
    def validate_text_length(self, text: str) -> Tuple[bool, str]:
        """텍스트 길이 유효성 검사"""
        if not text or not text.strip():
            return False, "빈 텍스트입니다."
        
        estimated_tokens = self.estimate_tokens(text)
        max_tokens = 8000  # OpenAI 임베딩 모델의 대략적인 최대 토큰 수
        
        if estimated_tokens > max_tokens:
            return False, f"텍스트가 너무 깁니다. ({estimated_tokens} > {max_tokens} 토큰)"
        
        return True, ""
    
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """단일 텍스트에 대한 임베딩 생성"""
        # 텍스트 유효성 검사
        is_valid, error_msg = self.validate_text_length(text)
        if not is_valid:
            logger.warning(f"텍스트 유효성 검사 실패: {error_msg}")
            return None
        
        for attempt in range(self.config.max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.config.model,
                    input=text,
                    dimensions=self.config.dimension
                )
                
                # 토큰 사용량 누적
                self.total_tokens_used += response.usage.total_tokens
                
                # 임베딩 벡터 반환
                embedding = response.data[0].embedding
                
                # Rate limiting을 위한 짧은 지연
                time.sleep(self.config.rate_limit_delay)
                
                return embedding
                
            except Exception as e:
                logger.warning(f"임베딩 생성 실패 (시도 {attempt + 1}/{self.config.max_retries}): {e}")
                
                if attempt < self.config.max_retries - 1:
                    # 지수 백오프로 재시도 지연
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.info(f"{delay}초 후 재시도합니다...")
                    time.sleep(delay)
                else:
                    logger.error(f"임베딩 생성 최종 실패: {text[:100]}...")
                    return None
        
        return None
    
    def create_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """배치로 임베딩 생성"""
        if not texts:
            return []
        
        logger.info(f"배치 임베딩 생성 시작: {len(texts)}개 텍스트")
        
        embeddings = []
        failed_count = 0
        
        # 진행률 표시
        with tqdm(total=len(texts), desc="임베딩 생성 중") as pbar:
            for i, text in enumerate(texts):
                embedding = self.create_embedding(text)
                embeddings.append(embedding)
                
                if embedding is None:
                    failed_count += 1
                    logger.warning(f"임베딩 생성 실패: 인덱스 {i}")
                
                pbar.update(1)
                pbar.set_postfix({
                    'failed': failed_count,
                    'tokens': self.total_tokens_used
                })
        
        success_count = len(texts) - failed_count
        logger.info(f"배치 임베딩 생성 완료: {success_count}/{len(texts)} 성공")
        logger.info(f"총 사용 토큰: {self.total_tokens_used}")
        
        return embeddings
    
    def process_restaurant_data(self, restaurant_data: List[Dict]) -> List[Dict]:
        """레스토랑 데이터에 임베딩 추가"""
        if not restaurant_data:
            logger.warning("처리할 레스토랑 데이터가 없습니다.")
            return []
        
        logger.info(f"레스토랑 데이터 임베딩 처리 시작: {len(restaurant_data)}개 항목")
        
        # 결합 텍스트 추출
        texts = []
        for item in restaurant_data:
            combined_text = item.get("combined_text", "")
            if not combined_text:
                logger.warning(f"결합 텍스트가 없습니다: {item.get('menu_name', 'Unknown')}")
                texts.append("")
            else:
                texts.append(combined_text)
        
        # 배치로 임베딩 생성
        embeddings = self.create_embeddings_batch(texts)
        
        # 결과 데이터 구성
        processed_data = []
        for i, (item, embedding) in enumerate(zip(restaurant_data, embeddings)):
            processed_item = item.copy()
            processed_item["embedding"] = embedding
            processed_item["has_embedding"] = embedding is not None
            
            if embedding is None:
                logger.warning(f"임베딩이 생성되지 않은 항목: {item.get('restaurant_name')} - {item.get('menu_name')}")
            
            processed_data.append(processed_item)
        
        # 통계 정보
        successful_embeddings = sum(1 for item in processed_data if item["has_embedding"])
        logger.info(f"임베딩 생성 완료: {successful_embeddings}/{len(processed_data)} 성공")
        
        return processed_data
    
    def save_embeddings(self, data_with_embeddings: List[Dict], output_path: str) -> None:
        """임베딩이 포함된 데이터를 파일로 저장"""
        try:
            # 디렉토리가 없으면 생성
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # numpy 배열을 리스트로 변환하여 JSON 직렬화 가능하게 함
            serializable_data = []
            for item in data_with_embeddings:
                serializable_item = item.copy()
                if item.get("embedding") is not None:
                    if isinstance(item["embedding"], np.ndarray):
                        serializable_item["embedding"] = item["embedding"].tolist()
                    # 이미 리스트인 경우는 그대로 유지
                
                serializable_data.append(serializable_item)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(serializable_data, file, ensure_ascii=False, indent=2)
            
            logger.info(f"임베딩 데이터 저장 완료: {output_path}")
            
        except Exception as e:
            logger.error(f"임베딩 데이터 저장 중 오류 발생: {e}")
            raise
    
    def load_embeddings(self, input_path: str) -> List[Dict]:
        """저장된 임베딩 데이터 로드"""
        try:
            with open(input_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            logger.info(f"임베딩 데이터 로드 완료: {len(data)}개 항목")
            return data
            
        except FileNotFoundError:
            logger.error(f"파일을 찾을 수 없습니다: {input_path}")
            raise
        except Exception as e:
            logger.error(f"임베딩 데이터 로드 중 오류 발생: {e}")
            raise
    
    def get_embedding_statistics(self, data_with_embeddings: List[Dict]) -> Dict[str, Any]:
        """임베딩 통계 정보 반환"""
        if not data_with_embeddings:
            return {}
        
        embeddings = [item["embedding"] for item in data_with_embeddings if item.get("embedding")]
        
        if not embeddings:
            return {"total_items": len(data_with_embeddings), "successful_embeddings": 0}
        
        # numpy 배열로 변환
        embedding_array = np.array(embeddings)
        
        stats = {
            "total_items": len(data_with_embeddings),
            "successful_embeddings": len(embeddings),
            "success_rate": round(len(embeddings) / len(data_with_embeddings) * 100, 2),
            "embedding_dimension": len(embeddings[0]) if embeddings else 0,
            "total_tokens_used": self.total_tokens_used,
            "avg_vector_norm": round(float(np.mean(np.linalg.norm(embedding_array, axis=1))), 4),
            "estimated_cost_usd": round(self.total_tokens_used * 0.00002, 4)  # text-embedding-3-small 가격
        }
        
        return stats


def main():
    """테스트용 메인 함수"""
    # 로깅 설정
    logger.add("logs/embedding_generator.log", rotation="10 MB")
    
    # 환경변수에서 API 키 로드
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return
    
    try:
        # 임베딩 생성기 초기화
        config = EmbeddingConfig(batch_size=10)  # 테스트용 작은 배치 크기
        generator = EmbeddingGenerator(api_key, config)
        
        # 테스트용 샘플 데이터
        sample_data = [
            {
                "restaurant_name": "청양불향관",
                "menu_name": "마라탕",
                "key_ingredients": ["소고기육수", "화자오", "청경채"],
                "short_description": "얼얼하고 칼칼한 국물.",
                "combined_text": "청양불향관 마라탕 소고기육수 화자오 청경채 얼얼하고 칼칼한 국물."
            },
            {
                "restaurant_name": "미도리 샐러드&바",
                "menu_name": "연어 포케",
                "key_ingredients": ["연어", "아보카도", "간장소스"],
                "short_description": "신선한 한그릇.",
                "combined_text": "미도리 샐러드&바 연어 포케 연어 아보카도 간장소스 신선한 한그릇."
            }
        ]
        
        logger.info("테스트 임베딩 생성 시작...")
        
        # 임베딩 생성
        processed_data = generator.process_restaurant_data(sample_data)
        
        # 통계 정보 출력
        stats = generator.get_embedding_statistics(processed_data)
        logger.info("임베딩 통계:")
        for key, value in stats.items():
            logger.info(f"  - {key}: {value}")
        
        # 결과 확인
        for i, item in enumerate(processed_data):
            logger.info(f"항목 {i+1}: {item['restaurant_name']} - {item['menu_name']}")
            logger.info(f"  임베딩 생성 여부: {item['has_embedding']}")
            if item['has_embedding']:
                embedding = item['embedding']
                logger.info(f"  임베딩 차원: {len(embedding)}")
                logger.info(f"  벡터 노름: {np.linalg.norm(embedding):.4f}")
        
        # 임베딩 데이터 저장 테스트
        generator.save_embeddings(processed_data, "test_embeddings.json")
        
        logger.info("임베딩 생성 테스트 완료!")
        
    except Exception as e:
        logger.error(f"임베딩 생성 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
