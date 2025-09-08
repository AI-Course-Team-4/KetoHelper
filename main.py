"""
레스토랑 메뉴 벡터 검색 데이터 준비 메인 스크립트
Phase 1: 데이터 파싱, 임베딩 생성, 데이터베이스 저장
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from loguru import logger
import json

# 프로젝트 모듈 import
sys.path.append(str(Path(__file__).parent / "src"))
from data_parser import RestaurantDataParser
from embedding_generator import EmbeddingGenerator, EmbeddingConfig
from database_manager import DatabaseManager, DatabaseConfig


def setup_logging(log_level: str = "INFO") -> None:
    """로깅 설정"""
    # 기존 로거 제거
    logger.remove()
    
    # 콘솔 로거 추가
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 파일 로거 추가
    os.makedirs("logs", exist_ok=True)
    logger.add(
        "logs/main.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days"
    )


def load_environment_variables() -> Dict[str, str]:
    """환경변수 로드 및 검증"""
    load_dotenv()
    
    required_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY")
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        logger.error(f"다음 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        logger.error("env_template.txt를 참고하여 .env 파일을 생성하고 값을 설정해주세요.")
        sys.exit(1)
    
    logger.info("환경변수 로드 완료")
    return required_vars


def create_configurations() -> tuple[EmbeddingConfig, DatabaseConfig]:
    """설정 객체 생성"""
    # 환경변수에서 설정값 로드
    embedding_config = EmbeddingConfig(
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        dimension=int(os.getenv("EMBEDDING_DIMENSION", "1536")),
        batch_size=int(os.getenv("BATCH_SIZE", "50")),
        max_retries=int(os.getenv("MAX_RETRIES", "3"))
    )
    
    database_config = DatabaseConfig(
        batch_size=int(os.getenv("BATCH_SIZE", "50")),
        max_retries=int(os.getenv("MAX_RETRIES", "3"))
    )
    
    return embedding_config, database_config


def step1_parse_data(json_file_path: str) -> list[Dict[str, Any]]:
    """Step 1: JSON 데이터 파싱 및 전처리"""
    logger.info("=" * 50)
    logger.info("STEP 1: 데이터 파싱 및 전처리")
    logger.info("=" * 50)
    
    parser = RestaurantDataParser(json_file_path)
    
    # 데이터 로드
    logger.info("JSON 데이터 로드 중...")
    parser.load_json_data()
    
    # 데이터 처리
    logger.info("데이터 처리 중...")
    processed_data = parser.process_restaurant_data()
    
    # 유효성 검사
    is_valid, errors = parser.validate_data()
    if not is_valid:
        logger.error("데이터 유효성 검사 실패:")
        for error in errors[:10]:  # 최대 10개 오류만 출력
            logger.error(f"  - {error}")
        if len(errors) > 10:
            logger.error(f"  ... 그 외 {len(errors) - 10}개 오류")
        
        # 심각한 오류가 많으면 중단
        if len(errors) > len(processed_data) * 0.1:  # 10% 이상 오류
            logger.error("오류가 너무 많습니다. 데이터를 확인해주세요.")
            sys.exit(1)
    
    # 통계 정보 출력
    stats = parser.get_statistics()
    logger.info("데이터 통계:")
    for key, value in stats.items():
        logger.info(f"  - {key}: {value}")
    
    # 샘플 데이터 출력
    sample_data = parser.get_sample_data(3)
    logger.info("샘플 데이터:")
    for i, item in enumerate(sample_data):
        logger.info(f"  {i+1}. {item['restaurant_name']} - {item['menu_name']}")
        logger.info(f"     결합텍스트: {item['combined_text'][:100]}...")
    
    # 중간 결과 저장
    parser.save_processed_data("data/processed_restaurant_data.json")
    
    logger.info(f"Step 1 완료: {len(processed_data)}개 메뉴 항목 처리")
    return processed_data


def step2_generate_embeddings(processed_data: list[Dict[str, Any]], 
                             embedding_config: EmbeddingConfig,
                             api_key: str) -> list[Dict[str, Any]]:
    """Step 2: 임베딩 벡터 생성"""
    logger.info("=" * 50)
    logger.info("STEP 2: 임베딩 벡터 생성")
    logger.info("=" * 50)
    
    generator = EmbeddingGenerator(api_key, embedding_config)
    
    # 예상 비용 계산
    total_chars = sum(len(item.get("combined_text", "")) for item in processed_data)
    estimated_tokens = int(total_chars * 0.75)  # 대략적인 토큰 추정
    estimated_cost = estimated_tokens * 0.00002  # text-embedding-3-small 가격
    
    logger.info(f"예상 토큰 사용량: {estimated_tokens:,}")
    logger.info(f"예상 비용: ${estimated_cost:.4f}")
    
    # 사용자 확인
    if estimated_cost > 1.0:  # $1 이상이면 확인
        confirm = input(f"예상 비용이 ${estimated_cost:.2f}입니다. 계속하시겠습니까? (y/N): ")
        if confirm.lower() != 'y':
            logger.info("임베딩 생성을 취소했습니다.")
            sys.exit(0)
    
    # 임베딩 생성
    logger.info("임베딩 생성 시작...")
    data_with_embeddings = generator.process_restaurant_data(processed_data)
    
    # 통계 정보 출력
    stats = generator.get_embedding_statistics(data_with_embeddings)
    logger.info("임베딩 통계:")
    for key, value in stats.items():
        logger.info(f"  - {key}: {value}")
    
    # 중간 결과 저장
    os.makedirs("data", exist_ok=True)
    generator.save_embeddings(data_with_embeddings, "data/restaurant_data_with_embeddings.json")
    
    logger.info(f"Step 2 완료: {stats['successful_embeddings']}/{stats['total_items']} 임베딩 생성")
    return data_with_embeddings


def step3_save_to_database(data_with_embeddings: list[Dict[str, Any]],
                          database_config: DatabaseConfig,
                          supabase_url: str, supabase_key: str) -> Dict[str, Any]:
    """Step 3: 데이터베이스에 저장"""
    logger.info("=" * 50)
    logger.info("STEP 3: 데이터베이스 저장")
    logger.info("=" * 50)
    
    db_manager = DatabaseManager(supabase_url, supabase_key, database_config)
    
    # 연결 테스트
    logger.info("데이터베이스 연결 테스트...")
    if not db_manager.test_connection():
        logger.error("데이터베이스 연결 실패")
        sys.exit(1)
    
    # 기존 데이터 확인
    existing_stats = db_manager.get_table_stats()
    if existing_stats.get("total_menu_items", 0) > 0:
        logger.warning(f"기존 데이터가 {existing_stats['total_menu_items']}개 있습니다.")
        clear_data = input("기존 데이터를 삭제하고 새로 저장하시겠습니까? (y/N): ")
        if clear_data.lower() == 'y':
            logger.info("기존 데이터 삭제 중...")
            db_manager.clear_table()
        else:
            logger.info("기존 데이터를 유지하고 새 데이터를 추가합니다.")
    
    # 데이터 삽입
    logger.info("데이터베이스 삽입 시작...")
    result = db_manager.insert_restaurant_data(data_with_embeddings)
    
    # 결과 출력
    logger.info("데이터베이스 삽입 결과:")
    for key, value in result.items():
        if key != "errors":
            logger.info(f"  - {key}: {value}")
    
    if result.get("errors"):
        logger.warning("삽입 오류:")
        for error in result["errors"][:5]:  # 최대 5개 오류만 출력
            logger.warning(f"  - {error}")
    
    # 최종 통계
    final_stats = db_manager.get_table_stats()
    logger.info("최종 데이터베이스 통계:")
    for key, value in final_stats.items():
        logger.info(f"  - {key}: {value}")
    
    # 벡터 인덱스 생성 시도
    if final_stats.get("total_menu_items", 0) >= 100:
        logger.info("벡터 검색 인덱스 생성 시도...")
        if db_manager.create_vector_index():
            logger.info("벡터 검색 인덱스 생성 완료")
        else:
            logger.warning("벡터 검색 인덱스 생성 실패 (나중에 수동으로 생성하세요)")
    else:
        logger.info("데이터가 부족하여 벡터 인덱스 생성을 건너뜁니다.")
    
    logger.info(f"Step 3 완료: {result['successful_inserts']}개 항목 저장")
    return result


def create_summary_report(processed_data: list[Dict], embeddings_data: list[Dict], 
                         db_result: Dict, output_path: str = "data/summary_report.json") -> None:
    """요약 리포트 생성"""
    logger.info("요약 리포트 생성 중...")
    
    from datetime import datetime
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "phase_1_summary": {
            "total_restaurants": len(set(item['restaurant_name'] for item in processed_data)),
            "total_menu_items": len(processed_data),
            "data_processing": {
                "success": True,
                "processed_items": len(processed_data)
            }
        },
        "embedding_generation": {
            "total_items": len(embeddings_data),
            "successful_embeddings": sum(1 for item in embeddings_data if item.get("has_embedding")),
            "success_rate": round(sum(1 for item in embeddings_data if item.get("has_embedding")) / len(embeddings_data) * 100, 2) if embeddings_data else 0
        },
        "database_storage": db_result,
        "next_steps": [
            "팀원들은 이제 벡터 검색, 키워드 검색, 하이브리드 검색 기능을 구현할 수 있습니다.",
            "setup_database.sql에 정의된 함수들을 활용하세요.",
            "데이터베이스에 저장된 임베딩을 사용하여 검색 성능을 테스트하세요."
        ]
    }
    
    os.makedirs("data", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"요약 리포트 저장 완료: {output_path}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="레스토랑 메뉴 벡터 검색 데이터 준비")
    parser.add_argument("--json-file", default="mock_restaurants_50.json", 
                       help="입력 JSON 파일 경로")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="로그 레벨")
    parser.add_argument("--skip-embeddings", action="store_true",
                       help="임베딩 생성 단계 건너뛰기 (테스트용)")
    
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging(args.log_level)
    
    logger.info("🚀 레스토랑 메뉴 벡터 검색 데이터 준비 시작!")
    logger.info(f"입력 파일: {args.json_file}")
    
    try:
        # 환경변수 로드
        env_vars = load_environment_variables()
        
        # 설정 생성
        embedding_config, database_config = create_configurations()
        
        # Step 1: 데이터 파싱
        processed_data = step1_parse_data(args.json_file)
        
        if args.skip_embeddings:
            logger.info("임베딩 생성을 건너뜁니다 (테스트 모드)")
            # 더미 임베딩 데이터 생성
            data_with_embeddings = []
            for item in processed_data[:5]:  # 테스트용으로 5개만
                item_copy = item.copy()
                item_copy["embedding"] = [0.1] * 1536  # 더미 임베딩
                item_copy["has_embedding"] = True
                data_with_embeddings.append(item_copy)
        else:
            # Step 2: 임베딩 생성
            data_with_embeddings = step2_generate_embeddings(
                processed_data, embedding_config, env_vars["OPENAI_API_KEY"]
            )
        
        # Step 3: 데이터베이스 저장
        db_result = step3_save_to_database(
            data_with_embeddings, database_config,
            env_vars["SUPABASE_URL"], env_vars["SUPABASE_KEY"]
        )
        
        # 요약 리포트 생성
        create_summary_report(processed_data, data_with_embeddings, db_result)
        
        # 최종 메시지
        logger.info("=" * 60)
        logger.info("🎉 Phase 1 데이터 준비 완료!")
        logger.info("=" * 60)
        logger.info("다음 단계:")
        logger.info("1. 팀원들과 데이터베이스 접근 정보 공유")
        logger.info("2. 벡터 검색, 키워드 검색, 하이브리드 검색 기능 구현")
        logger.info("3. 검색 성능 테스트 및 비교 분석")
        logger.info("4. 최적의 검색 전략 도출")
        logger.info("")
        logger.info("📁 생성된 파일들:")
        logger.info("  - data/processed_restaurant_data.json")
        logger.info("  - data/restaurant_data_with_embeddings.json")
        logger.info("  - data/summary_report.json")
        logger.info("  - logs/main.log")
        
    except KeyboardInterrupt:
        logger.warning("사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"처리 중 오류 발생: {e}")
        logger.exception("상세 오류 정보:")
        sys.exit(1)


if __name__ == "__main__":
    main()
