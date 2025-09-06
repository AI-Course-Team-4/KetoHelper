"""
크롤링 데이터용 OpenAI 임베딩 생성 서비스
"""
import openai
import logging
from typing import List, Dict, Any, Optional
import time

from config import OPENAI_API_KEY
from database_adapter import DatabaseAdapter

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        """OpenAI 클라이언트 및 데이터베이스 어댑터 초기화"""
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다")
        
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.db = DatabaseAdapter()
        self.model = "text-embedding-3-small"  # 1536 차원
        
        logger.info("임베딩 서비스 초기화 완료")
    
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
    
    def create_menu_text(self, menu_name: str, restaurant_name: str, restaurant_address: str) -> str:
        """메뉴 검색용 텍스트 생성"""
        menu_text_parts = [restaurant_name, menu_name, restaurant_address]
        return ' '.join(part for part in menu_text_parts if part)
    
    def process_menus_without_embedding(self) -> Dict[str, int]:
        """임베딩이 없는 메뉴들을 처리"""
        try:
            # 임베딩이 없는 메뉴들 조회 (JOIN으로 식당 정보 포함)
            menus = self.db.get_menus_without_embedding()
            
            if not menus:
                logger.info("임베딩이 필요한 메뉴가 없습니다")
                return {'processed': 0, 'success': 0, 'failed': 0}
            
            logger.info(f"임베딩 생성 대상: {len(menus)}개 메뉴")
            
            # menu_text 생성 및 임베딩 생성
            success_count = 0
            failed_count = 0
            
            for menu in menus:
                try:
                    # menu_text가 없으면 생성
                    if not menu.get('menu_text'):
                        restaurant_info = menu.get('restaurants', {})
                        menu_text = self.create_menu_text(
                            menu['name'],
                            restaurant_info.get('name', ''),
                            restaurant_info.get('address', '')
                        )
                        
                        # menu_text 업데이트
                        self.db.client.table('menus').update({
                            'menu_text': menu_text
                        }).eq('id', menu['id']).execute()
                    else:
                        menu_text = menu['menu_text']
                    
                    # 임베딩 생성
                    embedding = self.generate_embedding(menu_text)
                    
                    if embedding:
                        # 데이터베이스에 임베딩 저장
                        if self.db.update_menu_embedding(menu['id'], embedding):
                            success_count += 1
                            logger.debug(f"임베딩 생성 성공: {menu['name']}")
                        else:
                            failed_count += 1
                            logger.warning(f"임베딩 저장 실패: {menu['name']}")
                    else:
                        failed_count += 1
                        logger.warning(f"임베딩 생성 실패: {menu['name']}")
                    
                    # API 레이트 리미트 고려
                    time.sleep(0.1)
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"메뉴 처리 실패 ({menu['name']}): {e}")
            
            result = {
                'processed': len(menus),
                'success': success_count,
                'failed': failed_count
            }
            
            logger.info(f"임베딩 처리 완료: 성공 {success_count}개, 실패 {failed_count}개")
            return result
            
        except Exception as e:
            logger.error(f"임베딩 처리 중 오류 발생: {e}")
            return {'processed': 0, 'success': 0, 'failed': 0}
    
    def process_new_menus(self, menu_ids: List[str]) -> Dict[str, int]:
        """새로 추가된 특정 메뉴들의 임베딩 생성"""
        try:
            success_count = 0
            failed_count = 0
            
            for menu_id in menu_ids:
                try:
                    # 메뉴 정보 조회 (JOIN으로 식당 정보 포함)
                    result = self.db.client.table('menus').select(
                        'id, name, menu_text, restaurants(name, address)'
                    ).eq('id', menu_id).execute()
                    
                    if not result.data:
                        failed_count += 1
                        continue
                    
                    menu = result.data[0]
                    restaurant_info = menu.get('restaurants', {})
                    
                    # menu_text가 없으면 생성
                    if not menu.get('menu_text'):
                        menu_text = self.create_menu_text(
                            menu['name'],
                            restaurant_info.get('name', ''),
                            restaurant_info.get('address', '')
                        )
                        
                        # menu_text 업데이트
                        self.db.client.table('menus').update({
                            'menu_text': menu_text
                        }).eq('id', menu_id).execute()
                    else:
                        menu_text = menu['menu_text']
                    
                    # 임베딩 생성
                    embedding = self.generate_embedding(menu_text)
                    
                    if embedding:
                        if self.db.update_menu_embedding(menu_id, embedding):
                            success_count += 1
                        else:
                            failed_count += 1
                    else:
                        failed_count += 1
                    
                    # API 레이트 리미트 고려
                    time.sleep(0.1)
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"메뉴 임베딩 처리 실패 ({menu_id}): {e}")
            
            result = {
                'processed': len(menu_ids),
                'success': success_count,
                'failed': failed_count
            }
            
            logger.info(f"새 메뉴 임베딩 처리: 성공 {success_count}개, 실패 {failed_count}개")
            return result
            
        except Exception as e:
            logger.error(f"새 메뉴 임베딩 처리 중 오류: {e}")
            return {'processed': len(menu_ids), 'success': 0, 'failed': len(menu_ids)}
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """임베딩 현황 통계"""
        try:
            stats = self.db.get_statistics()
            return {
                'total_menus': stats.get('menus_count', 0),
                'with_embedding': stats.get('menus_with_embedding', 0),
                'without_embedding': stats.get('menus_count', 0) - stats.get('menus_with_embedding', 0),
                'coverage_percentage': stats.get('embedding_coverage', 0)
            }
        except Exception as e:
            logger.error(f"임베딩 통계 조회 실패: {e}")
            return {}

# 독립 실행 스크립트
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        embedding_service = EmbeddingService()
        
        if len(sys.argv) > 1 and sys.argv[1] == "--stats":
            # 통계만 출력
            stats = embedding_service.get_embedding_stats()
            print(f"\n📊 임베딩 현황:")
            print(f"- 총 메뉴 수: {stats.get('total_menus', 0)}")
            print(f"- 임베딩 있는 메뉴: {stats.get('with_embedding', 0)}")
            print(f"- 임베딩 없는 메뉴: {stats.get('without_embedding', 0)}")
            print(f"- 커버리지: {stats.get('coverage_percentage', 0):.1f}%")
        else:
            # 임베딩 처리 실행
            print("🔄 임베딩 생성 시작...")
            result = embedding_service.process_menus_without_embedding()
            
            print(f"\n✅ 임베딩 처리 완료:")
            print(f"- 처리된 메뉴: {result.get('processed', 0)}개")
            print(f"- 성공: {result.get('success', 0)}개")
            print(f"- 실패: {result.get('failed', 0)}개")
            
            if result.get('success', 0) > 0:
                stats = embedding_service.get_embedding_stats()
                print(f"\n📊 현재 커버리지: {stats.get('coverage_percentage', 0):.1f}%")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)
