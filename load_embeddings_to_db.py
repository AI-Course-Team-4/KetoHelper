#!/usr/bin/env python3
"""
기존에 생성된 임베딩 데이터를 데이터베이스에 로드하는 스크립트
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# 프로젝트 모듈 import
sys.path.append(str(Path(__file__).parent / "src"))
from database_manager import DatabaseManager, DatabaseConfig

def main():
    # 환경변수 로드
    load_dotenv()
    
    # 로깅 설정
    logger.add(sys.stdout, level="INFO")
    
    # 환경변수 확인
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL 또는 SUPABASE_KEY 환경변수가 설정되지 않았습니다.")
        return
    
    # 임베딩 데이터 로드
    embedding_file = "data/restaurant_data_with_embeddings.json"
    if not os.path.exists(embedding_file):
        logger.error(f"임베딩 파일을 찾을 수 없습니다: {embedding_file}")
        return
    
    logger.info("임베딩 데이터 로드 중...")
    with open(embedding_file, 'r', encoding='utf-8') as f:
        data_with_embeddings = json.load(f)
    
    logger.info(f"로드된 데이터: {len(data_with_embeddings)}개 항목")
    
    # 데이터베이스 매니저 초기화
    config = DatabaseConfig(batch_size=50)
    db_manager = DatabaseManager(supabase_url, supabase_key, config)
    
    # 연결 테스트
    if not db_manager.test_connection():
        logger.error("데이터베이스 연결 실패")
        return
    
    # 기존 데이터 확인 및 삭제
    logger.info("기존 데이터 확인 중...")
    try:
        existing_count = db_manager.client.table("restaurants").select("id", count="exact").execute().count
        if existing_count > 0:
            logger.warning(f"기존 데이터 {existing_count}개가 있습니다.")
            confirm = input("기존 데이터를 삭제하고 새로 저장하시겠습니까? (y/N): ")
            if confirm.lower() == 'y':
                logger.info("기존 데이터 삭제 중...")
                db_manager.clear_table()
    except Exception as e:
        logger.warning(f"기존 데이터 확인 실패: {e}")
    
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
        for error in result["errors"][:5]:
            logger.warning(f"  - {error}")
    
    # 벡터 인덱스 생성
    if result.get("successful_inserts", 0) >= 100:
        logger.info("벡터 검색 인덱스 생성 중...")
        try:
            # 직접 SQL 실행
            sql = """
            CREATE INDEX IF NOT EXISTS restaurants_embedding_idx 
            ON restaurants USING ivfflat (embedding vector_cosine_ops) 
            WITH (lists = 100);
            """
            db_manager.client.rpc("exec", {"sql": sql}).execute()
            logger.info("벡터 검색 인덱스 생성 완료")
        except Exception as e:
            logger.warning(f"벡터 인덱스 생성 실패: {e}")
    
    logger.info("✅ 임베딩 데이터 로드 완료!")

if __name__ == "__main__":
    main()
