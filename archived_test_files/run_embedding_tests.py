#!/usr/bin/env python3
"""
임베딩 테스트 실행 스크립트
"""

import sys
import subprocess
import os

def run_command(command, description):
    """명령어 실행"""
    print(f"\n🚀 {description}")
    print("=" * 50)
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"경고: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 오류: {e}")
        print(f"출력: {e.stdout}")
        print(f"에러: {e.stderr}")
        return False

def main():
    """메인 실행 함수"""
    print("🧪 임베딩 테스트 시작")
    print("=" * 50)
    
    # 1. 데이터베이스 테이블 생성
    print("1️⃣ 데이터베이스 테이블 생성")
    if not run_command("python -c \"exec(open('create_test_tables.sql').read())\"", "테이블 생성"):
        print("⚠️ SQL 파일을 Supabase SQL Editor에서 수동 실행해주세요")
        input("테이블 생성 완료 후 Enter를 눌러주세요...")
    
    # 2. 테스트 질의셋 생성
    print("2️⃣ 테스트 질의셋 생성")
    run_command("python create_test_queries.py", "30개 테스트 질의 생성")
    
    # 3. 방법1: 레시피명 포함 blob 임베딩 생성
    print("3️⃣ 방법1: 레시피명 포함 blob 임베딩 생성")
    run_command("python embedding_test_method1/method1_embedding_generator.py", "방법1 임베딩 생성")
    
    # 4. 방법2: 레시피명 제외 blob 임베딩 생성
    print("4️⃣ 방법2: 레시피명 제외 blob 임베딩 생성")
    run_command("python embedding_test_method2/method2_embedding_generator.py", "방법2 임베딩 생성")
    
    # 5. 방법3: LLM 전처리 정규화 임베딩 생성
    print("5️⃣ 방법3: LLM 전처리 정규화 임베딩 생성")
    run_command("python embedding_test_method3/method3_embedding_generator.py", "방법3 임베딩 생성")
    
    print("\n🎉 모든 임베딩 생성 완료!")
    print("다음 단계:")
    print("1. 각 방법별로 골든셋 생성")
    print("2. 성능 평가 실행")
    print("3. 결과 비교 분석")

if __name__ == "__main__":
    main()
