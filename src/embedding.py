"""
OpenAI API를 사용한 임베딩 생성 모듈
"""
import openai
import logging
from typing import List, Dict, Any, Optional
import time

from config import OPENAI_API_KEY
from database import DatabaseManager

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self, db_manager: DatabaseManager):
        """OpenAI 클라이언트 초기화"""
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다")
        
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.db = db_manager
        self.model = "text-embedding-3-small"  # 1536 차원
        
        logger.info("OpenAI 임베딩 생성기 초기화 완료")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """단일 텍스트의 임베딩 생성"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text.replace('\n', ' ')  # 줄바꿈 제거
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"임베딩 생성 완료: {len(embedding)} 차원")
            return embedding
            
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """배치로 여러 텍스트의 임베딩 생성"""
        try:
            # OpenAI API는 한 번에 최대 2048개 텍스트 처리 가능
            # 안전하게 100개씩 처리
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # 텍스트 전처리
                processed_texts = [text.replace('\n', ' ') for text in batch_texts]
                
                response = self.client.embeddings.create(
                    model=self.model,
                    input=processed_texts
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
                
                logger.info(f"배치 임베딩 완료: {i + len(batch_texts)}/{len(texts)}")
                
                # API 레이트 리미트 고려하여 잠시 대기
                if i + batch_size < len(texts):
                    time.sleep(1)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"배치 임베딩 생성 실패: {e}")
            return [None] * len(texts)
    
    def process_menus_without_embedding(self) -> bool:
        """임베딩이 없는 메뉴들을 처리"""
        try:
            # 임베딩이 없는 메뉴들 조회
            menus = self.db.get_menus_without_embedding()
            
            if not menus:
                logger.info("임베딩이 필요한 메뉴가 없습니다")
                return True
            
            logger.info(f"임베딩 생성 대상: {len(menus)}개 메뉴")
            
            # 텍스트 추출
            texts = [menu['menu_text'] for menu in menus]
            menu_ids = [menu['id'] for menu in menus]
            
            # 배치 임베딩 생성
            embeddings = self.generate_embeddings_batch(texts)
            
            # 데이터베이스 업데이트
            success_count = 0
            for menu_id, embedding in zip(menu_ids, embeddings):
                if embedding:
                    if self.db.update_embedding(menu_id, embedding):
                        success_count += 1
                    else:
                        logger.warning(f"임베딩 업데이트 실패: {menu_id}")
                else:
                    logger.warning(f"임베딩 생성 실패: {menu_id}")
            
            logger.info(f"임베딩 처리 완료: {success_count}/{len(menus)}")
            return success_count == len(menus)
            
        except Exception as e:
            logger.error(f"임베딩 처리 중 오류 발생: {e}")
            return False
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """임베딩 현황 통계"""
        try:
            total_count = self.db.get_menu_count()
            without_embedding = len(self.db.get_menus_without_embedding())
            with_embedding = total_count - without_embedding
            
            return {
                'total_menus': total_count,
                'with_embedding': with_embedding,
                'without_embedding': without_embedding,
                'coverage_percentage': (with_embedding / total_count * 100) if total_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {}

# 메인 실행 스크립트
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 데이터베이스 연결
        db = DatabaseManager()
        
        # 연결 테스트
        if not db.test_connection():
            print("❌ 데이터베이스 연결 실패")
            exit(1)
        
        print("✅ 데이터베이스 연결 성공")
        
        # 임베딩 생성기 초기화
        embedding_gen = EmbeddingGenerator(db)
        
        # 시작 전 현황
        stats_before = embedding_gen.get_embedding_stats()
        print(f"\n📊 임베딩 생성 전 현황:")
        print(f"- 총 메뉴 수: {stats_before.get('total_menus', 0)}")
        print(f"- 임베딩 있는 메뉴: {stats_before.get('with_embedding', 0)}")
        print(f"- 임베딩 없는 메뉴: {stats_before.get('without_embedding', 0)}")
        print(f"- 커버리지: {stats_before.get('coverage_percentage', 0):.1f}%")
        
        # 임베딩 생성 처리
        print("\n🔄 임베딩 생성 시작...")
        if embedding_gen.process_menus_without_embedding():
            print("✅ 임베딩 생성 완료")
        else:
            print("⚠️ 임베딩 생성 중 일부 오류 발생")
        
        # 완료 후 현황
        stats_after = embedding_gen.get_embedding_stats()
        print(f"\n📊 임베딩 생성 후 현황:")
        print(f"- 총 메뉴 수: {stats_after.get('total_menus', 0)}")
        print(f"- 임베딩 있는 메뉴: {stats_after.get('with_embedding', 0)}")
        print(f"- 임베딩 없는 메뉴: {stats_after.get('without_embedding', 0)}")
        print(f"- 커버리지: {stats_after.get('coverage_percentage', 0):.1f}%")
        
        # 성공 기준 체크 (95% 이상)
        if stats_after.get('coverage_percentage', 0) >= 95:
            print("\n🎉 성공 기준 달성: 임베딩 커버리지 95% 이상")
        else:
            print(f"\n⚠️ 성공 기준 미달: 임베딩 커버리지 {stats_after.get('coverage_percentage', 0):.1f}% (목표: 95%)")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        exit(1)
