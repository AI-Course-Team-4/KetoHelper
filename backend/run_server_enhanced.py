#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키토 코치 서버 실행 스크립트 (개선된 버전)
개발자별 가중치 설정 자동 로드 및 표시
"""

import os
import sys
import argparse
from pathlib import Path

# 인코딩 설정 (이모지 지원)
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 현재 디렉토리를 Python path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def print_banner():
    """시작 배너 출력"""
    print("\n" + "="*70)
    print("🚀 키토 코치 백엔드 서버 시작")
    print("="*70)

def print_usage():
    """사용법 출력"""
    print("\n📖 사용법:")
    print("  python run_server_enhanced.py [개발자명] [옵션]")
    print("\n👥 개발자명:")
    print("  soohwan  - 수환님 (검색 정확도 개선 실험)")
    print("  jihyun   - 지현님 (다양성 개선 실험)")
    print("  minseok  - 민석님 (키토 스코어 최적화 실험)")
    print("  default  - 기본 설정 (환경변수 기반)")
    print("\n⚙️ 옵션:")
    print("  --port PORT     - 포트 번호 (기본: 8000)")
    print("  --host HOST     - 호스트 (기본: 0.0.0.0)")
    print("  --reload        - 자동 재시작 활성화")
    print("  --no-reload     - 자동 재시작 비활성화")
    print("  --help          - 도움말 표시")
    print("\n💡 예시:")
    print("  python run_server_enhanced.py soohwan --reload")
    print("  python run_server_enhanced.py jihyun --port 8001")
    print("  python run_server_enhanced.py default")

def validate_developer(developer_name):
    """개발자명 유효성 검사"""
    valid_developers = ["soohwan", "jihyun", "minseok", "default"]
    if developer_name not in valid_developers:
        print(f"❌ 잘못된 개발자명: {developer_name}")
        print(f"✅ 사용 가능한 개발자명: {', '.join(valid_developers)}")
        return False
    return True

def setup_environment(developer_name, args):
    """환경 설정"""
    # 개발자명 환경변수 설정
    os.environ["DEVELOPER_NAME"] = developer_name
    
    # 추가 환경변수 설정
    if args.experiment_name:
        os.environ["EXPERIMENT_NAME"] = args.experiment_name
    if args.description:
        os.environ["EXPERIMENT_DESCRIPTION"] = args.description
    
    print(f"🔧 환경 설정 완료: DEVELOPER_NAME={developer_name}")

def load_and_display_config():
    """가중치 설정 로드 및 표시"""
    try:
        from app.core.weight_config import WeightConfig
        config = WeightConfig.load_config()
        config.print_config()
        return config
    except Exception as e:
        print(f"❌ 가중치 설정 로드 실패: {e}")
        print("⚠️ 기본 설정으로 진행합니다")
        return None

def start_server(args):
    """서버 시작"""
    import uvicorn
    
    print(f"\n🌐 서버 시작 중...")
    print(f"📍 주소: http://{args.host}:{args.port}")
    print(f"📚 API 문서: http://{args.host}:{args.port}/docs")
    print(f"🔄 자동 재시작: {'활성화' if args.reload else '비활성화'}")
    print(f"⏹️ 종료: Ctrl+C")
    print("="*70)
    
    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 서버가 안전하게 종료되었습니다")
    except Exception as e:
        print(f"\n❌ 서버 시작 실패: {e}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="키토 코치 백엔드 서버 실행 (개발자별 가중치 설정 지원)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "developer", 
        nargs="?", 
        default="default",
        help="개발자명 (soohwan, jihyun, minseok, default)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="포트 번호 (기본: 8000)"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="호스트 주소 (기본: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        default=True,
        help="자동 재시작 활성화 (기본값)"
    )
    
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="자동 재시작 비활성화"
    )
    
    parser.add_argument(
        "--experiment-name",
        help="실험명 (선택사항)"
    )
    
    parser.add_argument(
        "--description",
        help="실험 설명 (선택사항)"
    )
    
    args = parser.parse_args()
    
    # 자동 재시작 설정
    if args.no_reload:
        args.reload = False
    
    # 배너 출력
    print_banner()
    
    # 개발자명 유효성 검사
    if not validate_developer(args.developer):
        print_usage()
        sys.exit(1)
    
    # 환경 설정
    setup_environment(args.developer, args)
    
    # 가중치 설정 로드 및 표시
    config = load_and_display_config()
    
    # 서버 시작
    start_server(args)

if __name__ == "__main__":
    main()
