#!/usr/bin/env python3
"""
배치 임베딩 처리 스크립트

크롤링된 원시 데이터에서 임베딩이 없는 메뉴들을 찾아서
배치로 임베딩을 생성하는 독립적인 스크립트입니다.

사용법:
    python batch_embedding.py                    # 모든 임베딩 없는 메뉴 처리
    python batch_embedding.py --stats           # 현재 임베딩 상태만 조회
    python batch_embedding.py --limit 100       # 최대 100개까지만 처리
    python batch_embedding.py --restaurant-id <uuid>  # 특정 식당만 처리
"""
import argparse
import logging
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

from config import validate_config
from database_adapter import DatabaseAdapter
from embedding_service import EmbeddingService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BatchEmbeddingProcessor:
    def __init__(self):
        """배치 임베딩 프로세서 초기화"""
        try:
            # 환경 설정 검증
            validate_config()
            
            # 서비스 초기화
            self.db = DatabaseAdapter()
            self.embedding_service = EmbeddingService()
            
            if not self.db.test_connection():
                raise Exception("데이터베이스 연결 실패")
            
            logger.info("배치 임베딩 프로세서 초기화 완료")
            
        except Exception as e:
            logger.error(f"초기화 실패: {e}")
            raise
    
    def get_embedding_status(self) -> Dict[str, Any]:
        """현재 임베딩 상태 조회"""
        try:
            stats = self.db.get_statistics()
            
            total_menus = stats.get('menus_count', 0)
            with_embedding = stats.get('menus_with_embedding', 0)
            without_embedding = total_menus - with_embedding
            coverage_percentage = (with_embedding / total_menus * 100) if total_menus > 0 else 0
            
            return {
                'total_menus': total_menus,
                'with_embedding': with_embedding,
                'without_embedding': without_embedding,
                'coverage_percentage': coverage_percentage,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"임베딩 상태 조회 실패: {e}")
            return {}
    
    def get_menus_without_embedding(self, limit: Optional[int] = None, restaurant_id: Optional[str] = None) -> List[Dict]:
        """임베딩이 없는 메뉴 목록 조회"""
        try:
            query = self.db.client.table('menus').select(
                'id, name, menu_text, restaurant_id, restaurants(name, address)'
            ).is_('embedding', 'null')
            
            if restaurant_id:
                query = query.eq('restaurant_id', restaurant_id)
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"임베딩 없는 메뉴 조회 실패: {e}")
            return []
    
    def process_batch(self, limit: Optional[int] = None, restaurant_id: Optional[str] = None) -> Dict[str, int]:
        """배치 임베딩 처리"""
        start_time = time.time()
        
        try:
            logger.info("🔄 배치 임베딩 처리 시작...")
            
            # 처리 대상 메뉴 조회
            menus = self.get_menus_without_embedding(limit=limit, restaurant_id=restaurant_id)
            
            if not menus:
                logger.info("✅ 처리할 메뉴가 없습니다. 모든 메뉴가 임베딩을 가지고 있습니다.")
                return {'processed': 0, 'success': 0, 'failed': 0}
            
            logger.info(f"📝 처리 대상: {len(menus)}개 메뉴")
            
            # 통계 변수
            success_count = 0
            failed_count = 0
            
            # 메뉴별 처리
            for i, menu in enumerate(menus, 1):
                try:
                    menu_id = menu['id']
                    menu_name = menu['name']
                    restaurant_info = menu.get('restaurants', {})
                    restaurant_name = restaurant_info.get('name', '')
                    
                    logger.info(f"🔄 처리 중 ({i}/{len(menus)}): {restaurant_name} - {menu_name}")
                    
                    # menu_text가 없으면 생성
                    menu_text = menu.get('menu_text')
                    if not menu_text:
                        menu_text = self.embedding_service.create_menu_text(
                            menu_name,
                            restaurant_name,
                            restaurant_info.get('address', '')
                        )
                        
                        # menu_text 업데이트
                        self.db.client.table('menus').update({
                            'menu_text': menu_text
                        }).eq('id', menu_id).execute()
                        
                        logger.debug(f"menu_text 생성: {menu_text}")
                    
                    # 임베딩 생성
                    embedding = self.embedding_service.generate_embedding(menu_text)
                    
                    if embedding:
                        # 데이터베이스에 임베딩 저장
                        if self.db.update_menu_embedding(menu_id, embedding):
                            success_count += 1
                            logger.info(f"✅ 성공: {menu_name}")
                        else:
                            failed_count += 1
                            logger.warning(f"❌ 저장 실패: {menu_name}")
                    else:
                        failed_count += 1
                        logger.warning(f"❌ 임베딩 생성 실패: {menu_name}")
                    
                    # API 레이트 리미트 고려 (OpenAI는 분당 3000 requests)
                    time.sleep(0.1)
                    
                    # 진행률 출력 (10개마다)
                    if i % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = i / elapsed
                        eta = (len(menus) - i) / rate if rate > 0 else 0
                        logger.info(f"📊 진행률: {i}/{len(menus)} ({i/len(menus)*100:.1f}%) - ETA: {eta:.0f}초")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ 메뉴 처리 실패 ({menu.get('name', 'unknown')}): {e}")
            
            # 최종 결과
            elapsed = time.time() - start_time
            result = {
                'processed': len(menus),
                'success': success_count,
                'failed': failed_count,
                'elapsed_time': elapsed
            }
            
            logger.info(f"🎉 배치 처리 완료!")
            logger.info(f"   📝 처리된 메뉴: {result['processed']}개")
            logger.info(f"   ✅ 성공: {result['success']}개")
            logger.info(f"   ❌ 실패: {result['failed']}개")
            logger.info(f"   ⏱️  소요 시간: {elapsed:.1f}초")
            logger.info(f"   📈 처리 속도: {result['processed']/elapsed:.1f}개/초")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 배치 처리 중 오류 발생: {e}")
            return {'processed': 0, 'success': 0, 'failed': 0, 'error': str(e)}
    
    def process_restaurant_batch(self, restaurant_id: str) -> Dict[str, int]:
        """특정 식당의 메뉴만 배치 처리"""
        logger.info(f"🏪 특정 식당 처리: {restaurant_id}")
        return self.process_batch(restaurant_id=restaurant_id)
    
    def print_status_report(self):
        """상세한 상태 리포트 출력"""
        try:
            status = self.get_embedding_status()
            
            if not status:
                print("❌ 상태 조회에 실패했습니다.")
                return
            
            print("\n" + "="*60)
            print("📊 임베딩 상태 리포트")
            print("="*60)
            print(f"🗓️  조회 시간: {status['last_updated']}")
            print(f"📝 총 메뉴 수: {status['total_menus']:,}개")
            print(f"✅ 임베딩 완료: {status['with_embedding']:,}개")
            print(f"⏳ 임베딩 대기: {status['without_embedding']:,}개")
            print(f"📈 완료율: {status['coverage_percentage']:.1f}%")
            
            # 진행률 바 출력
            if status['total_menus'] > 0:
                bar_length = 40
                filled_length = int(bar_length * status['coverage_percentage'] / 100)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                print(f"📊 [{bar}] {status['coverage_percentage']:.1f}%")
            
            print("="*60)
            
            # 추천 사항
            if status['without_embedding'] > 0:
                print(f"💡 {status['without_embedding']}개의 메뉴가 임베딩 처리를 기다리고 있습니다.")
                print("   다음 명령어로 배치 처리를 실행하세요:")
                print("   python batch_embedding.py")
            else:
                print("🎉 모든 메뉴의 임베딩 처리가 완료되었습니다!")
            
        except Exception as e:
            logger.error(f"상태 리포트 출력 실패: {e}")

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='배치 임베딩 처리 스크립트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
    python batch_embedding.py                    # 모든 메뉴 처리
    python batch_embedding.py --stats           # 상태만 조회
    python batch_embedding.py --limit 50        # 최대 50개만 처리
    python batch_embedding.py --restaurant-id <uuid>  # 특정 식당만 처리
        """
    )
    
    parser.add_argument(
        '--stats', 
        action='store_true', 
        help='임베딩 상태만 조회하고 종료'
    )
    
    parser.add_argument(
        '--limit', 
        type=int, 
        help='처리할 최대 메뉴 개수'
    )
    
    parser.add_argument(
        '--restaurant-id', 
        type=str, 
        help='처리할 특정 식당의 UUID'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='상세한 로그 출력'
    )
    
    args = parser.parse_args()
    
    # 로깅 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 프로세서 초기화
        processor = BatchEmbeddingProcessor()
        
        if args.stats:
            # 상태만 조회
            processor.print_status_report()
        else:
            # 배치 처리 실행
            result = processor.process_batch(
                limit=args.limit,
                restaurant_id=args.restaurant_id
            )
            
            # 처리 후 상태 출력
            if result['processed'] > 0:
                print("\n" + "="*40)
                processor.print_status_report()
    
    except KeyboardInterrupt:
        logger.info("❌ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 실행 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
