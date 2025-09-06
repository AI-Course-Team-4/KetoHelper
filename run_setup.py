"""
전체 시스템 설정 및 실행 스크립트
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

def run_command(command, description, cwd=None):
    """명령어 실행 및 결과 출력"""
    print(f"\n🔄 {description}")
    print(f"실행: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print(f"✅ 성공: {description}")
            if result.stdout:
                print(f"출력: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ 실패: {description}")
            if result.stderr:
                print(f"오류: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ 명령어 실행 실패: {e}")
        return False

def check_environment():
    """환경 설정 확인"""
    print("🔍 환경 설정 확인")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env 파일이 없습니다.")
        print("📝 env_example.txt를 참고하여 .env 파일을 생성하세요.")
        return False
    
    # 필수 환경 변수 확인
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'OPENAI_API_KEY']
    missing_vars = []
    
    with open(env_file, 'r', encoding='utf-8') as f:
        env_content = f.read()
        for var in required_vars:
            if f"{var}=" not in env_content or f"{var}=your_" in env_content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 다음 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        return False
    
    print("✅ 환경 설정 완료")
    return True

def main():
    """메인 실행 함수"""
    print("🚀 벡터 검색 시스템 V0 설정 시작")
    print("=" * 50)
    
    # 1. 환경 확인
    if not check_environment():
        print("\n❌ 환경 설정을 완료한 후 다시 실행하세요.")
        sys.exit(1)
    
    # 2. src 디렉토리로 이동
    src_dir = Path(__file__).parent / 'src'
    if not src_dir.exists():
        print("❌ src 디렉토리를 찾을 수 없습니다.")
        sys.exit(1)
    
    print(f"\n📁 작업 디렉토리: {src_dir}")
    
    # 3. 데이터 적재
    if not run_command("python data_loader.py", "CSV 데이터 적재", cwd=src_dir):
        print("❌ 데이터 적재에 실패했습니다.")
        print("💡 Supabase 설정이 완료되었는지 확인하세요.")
        sys.exit(1)
    
    # 4. 임베딩 생성
    if not run_command("python embedding.py", "OpenAI 임베딩 생성", cwd=src_dir):
        print("❌ 임베딩 생성에 실패했습니다.")
        print("💡 OpenAI API 키가 올바른지 확인하세요.")
        sys.exit(1)
    
    # 5. 시스템 테스트
    print(f"\n🧪 시스템 테스트 실행")
    if not run_command("python test_system.py", "전체 시스템 테스트", cwd=src_dir):
        print("⚠️ 일부 테스트가 실패했습니다.")
        print("📄 test_results.json 파일을 확인하세요.")
    else:
        print("🎉 모든 테스트가 성공했습니다!")
    
    # 6. API 서버 시작 안내
    print(f"\n" + "=" * 50)
    print("✅ 설정 완료!")
    print(f"\n🌐 API 서버를 시작하려면:")
    print(f"   cd src")
    print(f"   python main.py")
    print(f"\n📖 API 문서: http://localhost:8000/docs")
    print(f"🔍 검색 테스트: http://localhost:8000/search?preference_text=매운&top_k=5")

if __name__ == "__main__":
    main()
