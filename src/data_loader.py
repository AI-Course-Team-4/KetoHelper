"""
CSV 데이터를 읽어서 Supabase에 적재하는 모듈
"""
import csv
import logging
from typing import List, Dict, Any
from pathlib import Path

from database import DatabaseManager

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def load_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """CSV 파일을 읽어서 딕셔너리 리스트로 반환"""
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
        
        menus = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # 데이터 정제
                    menu_data = {
                        'restaurant_name': row['restaurant_name'].strip('"'),
                        'address': row['address'].strip('"'),
                        'menu_name': row['menu_name'].strip('"'),
                        'price': int(row['price']) if row['price'].strip() else None,
                        'category': row['category'].strip('"') if row['category'].strip() else None,
                        'source': row['source'].strip('"') if row['source'].strip() else 'manual',
                        'rating': float(row['rating']) if row['rating'].strip() else None,
                        'image_url': row['image_url'].strip('"') if row['image_url'].strip() else None
                    }
                    
                    # menu_text 생성 (검색용)
                    menu_text_parts = [
                        menu_data['restaurant_name'],
                        menu_data['menu_name'],
                        menu_data['address']
                    ]
                    if menu_data['category']:
                        menu_text_parts.append(menu_data['category'])
                    
                    menu_data['menu_text'] = ' '.join(menu_text_parts)
                    
                    menus.append(menu_data)
            
            logger.info(f"CSV 파일 로드 완료: {len(menus)}개 메뉴")
            return menus
            
        except Exception as e:
            logger.error(f"CSV 파일 로드 실패: {e}")
            raise
    
    def validate_menu_data(self, menu_data: Dict[str, Any]) -> bool:
        """메뉴 데이터 유효성 검사"""
        required_fields = ['restaurant_name', 'address', 'menu_name']
        
        for field in required_fields:
            if not menu_data.get(field):
                logger.warning(f"필수 필드 누락: {field}")
                return False
        
        return True
    
    def load_to_database(self, csv_path: str) -> bool:
        """CSV 데이터를 데이터베이스에 적재"""
        try:
            # CSV 로드
            menus = self.load_csv(csv_path)
            
            # 데이터 검증
            valid_menus = []
            for menu in menus:
                if self.validate_menu_data(menu):
                    valid_menus.append(menu)
                else:
                    logger.warning(f"유효하지 않은 메뉴 데이터: {menu}")
            
            if not valid_menus:
                logger.error("유효한 메뉴 데이터가 없습니다")
                return False
            
            # 배치 삽입
            success = self.db.insert_menus_batch(valid_menus)
            
            if success:
                logger.info(f"데이터베이스 적재 완료: {len(valid_menus)}개 메뉴")
                return True
            else:
                logger.error("데이터베이스 적재 실패")
                return False
                
        except Exception as e:
            logger.error(f"데이터 적재 중 오류 발생: {e}")
            return False
    
    def get_load_summary(self) -> Dict[str, int]:
        """데이터 적재 현황 요약"""
        try:
            total_count = self.db.get_menu_count()
            menus_without_embedding = len(self.db.get_menus_without_embedding())
            
            return {
                'total_menus': total_count,
                'menus_with_embedding': total_count - menus_without_embedding,
                'menus_without_embedding': menus_without_embedding,
                'embedding_coverage': (total_count - menus_without_embedding) / total_count * 100 if total_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"요약 정보 조회 실패: {e}")
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
        
        # 데이터 로더 생성
        loader = DataLoader(db)
        
        # CSV 데이터 적재
        csv_path = "data/sample_menus.csv"
        if loader.load_to_database(csv_path):
            print("✅ 데이터 적재 완료")
            
            # 요약 정보 출력
            summary = loader.get_load_summary()
            print(f"\n📊 데이터 적재 현황:")
            print(f"- 총 메뉴 수: {summary.get('total_menus', 0)}")
            print(f"- 임베딩 있는 메뉴: {summary.get('menus_with_embedding', 0)}")
            print(f"- 임베딩 없는 메뉴: {summary.get('menus_without_embedding', 0)}")
            print(f"- 임베딩 커버리지: {summary.get('embedding_coverage', 0):.1f}%")
        else:
            print("❌ 데이터 적재 실패")
            exit(1)
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        exit(1)
