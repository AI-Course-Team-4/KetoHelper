"""
Supabase 데이터베이스 관리 모듈
레스토랑 메뉴 데이터와 임베딩을 Supabase에 저장하고 관리
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
from supabase import create_client, Client
from loguru import logger
from tqdm import tqdm
import time


@dataclass
class DatabaseConfig:
    """데이터베이스 설정 클래스"""
    batch_size: int = 50
    max_retries: int = 3
    retry_delay: float = 1.0
    table_name: str = "restaurants"


class DatabaseManager:
    """Supabase 데이터베이스 매니저"""
    
    def __init__(self, supabase_url: str, supabase_key: str, config: Optional[DatabaseConfig] = None):
        """
        Args:
            supabase_url: Supabase 프로젝트 URL
            supabase_key: Supabase API 키
            config: 데이터베이스 설정
        """
        self.config = config or DatabaseConfig()
        
        try:
            self.client: Client = create_client(supabase_url, supabase_key)
            logger.info("Supabase 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"Supabase 클라이언트 초기화 실패: {e}")
            raise
    
    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            # 테이블 존재 여부 확인
            response = self.client.table(self.config.table_name).select("id").limit(1).execute()
            logger.info("데이터베이스 연결 테스트 성공")
            return True
            
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {e}")
            return False
    
    def clear_table(self) -> bool:
        """테이블의 모든 데이터 삭제 (주의: 복구 불가능)"""
        try:
            logger.warning("테이블의 모든 데이터를 삭제합니다...")
            
            # 모든 레코드 삭제
            response = self.client.table(self.config.table_name).delete().neq("id", 0).execute()
            
            deleted_count = len(response.data) if response.data else 0
            logger.info(f"테이블 데이터 삭제 완료: {deleted_count}개 레코드")
            return True
            
        except Exception as e:
            logger.error(f"테이블 데이터 삭제 실패: {e}")
            return False
    
    def prepare_data_for_insert(self, restaurant_data: List[Dict]) -> List[Dict]:
        """데이터베이스 삽입을 위한 데이터 준비"""
        prepared_data = []
        
        for item in restaurant_data:
            # 필수 필드 확인
            if not all(key in item for key in ["restaurant_name", "menu_name", "combined_text"]):
                logger.warning(f"필수 필드가 누락된 항목을 건너뜁니다: {item.get('menu_name', 'Unknown')}")
                continue
            
            # 임베딩 벡터 처리
            embedding = item.get("embedding")
            if embedding is None:
                logger.warning(f"임베딩이 없는 항목을 건너뜁니다: {item['restaurant_name']} - {item['menu_name']}")
                continue
            
            # 데이터베이스 삽입용 형태로 변환
            db_item = {
                "restaurant_name": item["restaurant_name"],
                "menu_name": item["menu_name"],
                "key_ingredients": item.get("key_ingredients", []),
                "short_description": item.get("short_description", ""),
                "combined_text": item["combined_text"],
                "embedding": embedding  # pgvector가 자동으로 처리
            }
            
            prepared_data.append(db_item)
        
        logger.info(f"데이터 준비 완료: {len(prepared_data)}개 항목")
        return prepared_data
    
    def insert_batch(self, batch_data: List[Dict]) -> Tuple[bool, List[str]]:
        """배치 데이터 삽입"""
        if not batch_data:
            return True, []
        
        errors = []
        
        for attempt in range(self.config.max_retries):
            try:
                response = self.client.table(self.config.table_name).insert(batch_data).execute()
                
                if response.data:
                    logger.debug(f"배치 삽입 성공: {len(batch_data)}개 항목")
                    return True, []
                else:
                    error_msg = f"삽입 결과 데이터가 없습니다 (시도 {attempt + 1})"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                
            except Exception as e:
                error_msg = f"배치 삽입 실패 (시도 {attempt + 1}/{self.config.max_retries}): {e}"
                errors.append(error_msg)
                logger.warning(error_msg)
                
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.info(f"{delay}초 후 재시도합니다...")
                    time.sleep(delay)
        
        return False, errors
    
    def insert_restaurant_data(self, restaurant_data: List[Dict]) -> Dict[str, Any]:
        """레스토랑 데이터를 데이터베이스에 삽입"""
        if not restaurant_data:
            logger.warning("삽입할 데이터가 없습니다.")
            return {"success": False, "message": "데이터 없음"}
        
        logger.info(f"데이터베이스 삽입 시작: {len(restaurant_data)}개 항목")
        
        # 데이터 준비
        prepared_data = self.prepare_data_for_insert(restaurant_data)
        if not prepared_data:
            return {"success": False, "message": "준비된 데이터 없음"}
        
        # 배치로 나누어 삽입
        total_batches = (len(prepared_data) + self.config.batch_size - 1) // self.config.batch_size
        successful_inserts = 0
        failed_inserts = 0
        all_errors = []
        
        with tqdm(total=len(prepared_data), desc="데이터베이스 삽입 중") as pbar:
            for i in range(0, len(prepared_data), self.config.batch_size):
                batch = prepared_data[i:i + self.config.batch_size]
                batch_num = i // self.config.batch_size + 1
                
                logger.debug(f"배치 {batch_num}/{total_batches} 삽입 중...")
                
                success, errors = self.insert_batch(batch)
                
                if success:
                    successful_inserts += len(batch)
                    logger.debug(f"배치 {batch_num} 삽입 성공")
                else:
                    failed_inserts += len(batch)
                    all_errors.extend(errors)
                    logger.error(f"배치 {batch_num} 삽입 실패")
                
                pbar.update(len(batch))
                pbar.set_postfix({
                    'success': successful_inserts,
                    'failed': failed_inserts
                })
        
        # 결과 반환
        result = {
            "success": successful_inserts > 0,
            "total_items": len(prepared_data),
            "successful_inserts": successful_inserts,
            "failed_inserts": failed_inserts,
            "success_rate": round(successful_inserts / len(prepared_data) * 100, 2) if prepared_data else 0,
            "errors": all_errors[:10]  # 최대 10개 오류만 반환
        }
        
        if result["success"]:
            logger.info(f"데이터베이스 삽입 완료: {successful_inserts}/{len(prepared_data)} 성공")
        else:
            logger.error(f"데이터베이스 삽입 실패: 모든 항목 삽입 실패")
        
        return result
    
    def get_table_stats(self) -> Dict[str, Any]:
        """테이블 통계 정보 조회"""
        try:
            # 전체 레코드 수
            count_response = self.client.table(self.config.table_name).select("id", count="exact").execute()
            total_count = count_response.count if hasattr(count_response, 'count') else 0
            
            # 레스토랑 수
            restaurant_response = self.client.rpc("get_unique_restaurant_count").execute()
            restaurant_count = restaurant_response.data if restaurant_response.data else 0
            
            # 임베딩이 있는 레코드 수
            embedding_response = self.client.table(self.config.table_name).select("id").not_.is_("embedding", "null").execute()
            embedding_count = len(embedding_response.data) if embedding_response.data else 0
            
            stats = {
                "total_menu_items": total_count,
                "unique_restaurants": restaurant_count,
                "items_with_embeddings": embedding_count,
                "embedding_coverage": round(embedding_count / total_count * 100, 2) if total_count > 0 else 0
            }
            
            logger.info("테이블 통계 조회 완료")
            return stats
            
        except Exception as e:
            logger.error(f"테이블 통계 조회 실패: {e}")
            return {}
    
    def verify_data_integrity(self) -> Dict[str, Any]:
        """데이터 무결성 검사"""
        try:
            # 중복 데이터 확인
            duplicate_response = self.client.rpc("find_duplicate_menus").execute()
            duplicates = duplicate_response.data if duplicate_response.data else []
            
            # 빈 필드 확인
            empty_fields = {}
            required_fields = ["restaurant_name", "menu_name", "combined_text"]
            
            for field in required_fields:
                empty_response = self.client.table(self.config.table_name).select("id").or_(f"{field}.is.null,{field}.eq.").execute()
                empty_count = len(empty_response.data) if empty_response.data else 0
                empty_fields[field] = empty_count
            
            # 임베딩 벡터 차원 확인
            dimension_response = self.client.rpc("check_embedding_dimensions").execute()
            dimension_issues = dimension_response.data if dimension_response.data else []
            
            integrity_report = {
                "duplicate_menus": len(duplicates),
                "empty_fields": empty_fields,
                "embedding_dimension_issues": len(dimension_issues),
                "total_issues": len(duplicates) + sum(empty_fields.values()) + len(dimension_issues)
            }
            
            logger.info("데이터 무결성 검사 완료")
            return integrity_report
            
        except Exception as e:
            logger.error(f"데이터 무결성 검사 실패: {e}")
            return {"error": str(e)}
    
    def create_vector_index(self) -> bool:
        """벡터 검색 인덱스 생성"""
        try:
            # 데이터가 충분한지 확인
            count_response = self.client.table(self.config.table_name).select("id", count="exact").execute()
            total_count = count_response.count if hasattr(count_response, 'count') else 0
            
            if total_count < 100:
                logger.warning(f"벡터 인덱스 생성을 위한 데이터가 부족합니다. ({total_count} < 100)")
                return False
            
            # 인덱스 생성 SQL 실행
            sql = """
            CREATE INDEX IF NOT EXISTS restaurants_embedding_idx 
            ON restaurants USING ivfflat (embedding vector_cosine_ops) 
            WITH (lists = 100);
            """
            
            response = self.client.rpc("execute_sql", {"sql": sql}).execute()
            
            logger.info("벡터 검색 인덱스 생성 완료")
            return True
            
        except Exception as e:
            logger.error(f"벡터 검색 인덱스 생성 실패: {e}")
            return False
    
    def export_data(self, output_path: str) -> bool:
        """데이터베이스 데이터를 JSON 파일로 내보내기"""
        try:
            # 모든 데이터 조회
            response = self.client.table(self.config.table_name).select("*").execute()
            
            if not response.data:
                logger.warning("내보낼 데이터가 없습니다.")
                return False
            
            # JSON 파일로 저장
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(response.data, file, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"데이터 내보내기 완료: {len(response.data)}개 항목 -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"데이터 내보내기 실패: {e}")
            return False


def main():
    """테스트용 메인 함수"""
    # 로깅 설정
    logger.add("logs/database_manager.log", rotation="10 MB")
    
    # 환경변수에서 설정 로드
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL 또는 SUPABASE_KEY 환경변수가 설정되지 않았습니다.")
        return
    
    try:
        # 데이터베이스 매니저 초기화
        config = DatabaseConfig(batch_size=10)  # 테스트용 작은 배치 크기
        db_manager = DatabaseManager(supabase_url, supabase_key, config)
        
        # 연결 테스트
        if not db_manager.test_connection():
            logger.error("데이터베이스 연결 실패")
            return
        
        # 테이블 통계 조회
        stats = db_manager.get_table_stats()
        logger.info("테이블 통계:")
        for key, value in stats.items():
            logger.info(f"  - {key}: {value}")
        
        # 데이터 무결성 검사
        integrity = db_manager.verify_data_integrity()
        logger.info("데이터 무결성 검사:")
        for key, value in integrity.items():
            logger.info(f"  - {key}: {value}")
        
        logger.info("데이터베이스 매니저 테스트 완료!")
        
    except Exception as e:
        logger.error(f"데이터베이스 매니저 테스트 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
