#!/bin/bash

# 키토 코치 개발 환경 시작 스크립트

echo "🚀 키토 코치 개발 환경을 시작합니다..."

# 환경 변수 체크
check_env_file() {
    if [ ! -f "backend/.env" ]; then
        echo "❌ backend/.env 파일이 없습니다."
        echo "📝 backend/env.example을 참고하여 .env 파일을 생성하세요."
        echo ""
        echo "필요한 API 키들:"
        echo "- OPENAI_API_KEY: OpenAI API 키"
        echo "- KAKAO_REST_KEY: 카카오 REST API 키"
        echo "- DATABASE_URL: Supabase 데이터베이스 URL"
        echo "- SUPABASE_URL: Supabase 프로젝트 URL"
        echo "- SUPABASE_ANON_KEY: Supabase Anon 키"
        echo ""
        exit 1
    fi
}

# 의존성 설치 체크
install_dependencies() {
    echo "📦 의존성을 확인하고 설치합니다..."
    
    # Python 의존성
    if [ ! -d "backend/venv" ] && [ ! -d "backend/.venv" ]; then
        echo "🐍 Python 가상환경을 생성합니다..."
        cd backend
        python -m venv venv
        cd ..
    fi
    
    # 백엔드 의존성 설치
    echo "📚 백엔드 의존성 설치..."
    cd backend
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    pip install -r requirements.txt
    cd ..
    
    # 프론트엔드 의존성 설치
    echo "⚛️ 프론트엔드 의존성 설치..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    cd ..
}

# 데이터베이스 스키마 확인
check_database() {
    echo "🗄️ 데이터베이스 스키마를 확인합니다..."
    echo "Supabase SQL Editor에서 docs/database_setup.sql을 실행했는지 확인하세요."
}

# 개발 서버 시작
start_servers() {
    echo "🌟 개발 서버를 시작합니다..."
    
    # 백엔드 서버 시작 (백그라운드)
    echo "🔧 백엔드 서버 시작 중... (포트 8000)"
    cd backend
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    uvicorn app.main:app --reload --port 8000 &
    BACKEND_PID=$!
    cd ..
    
    # 잠시 대기
    sleep 3
    
    # 프론트엔드 서버 시작
    echo "⚛️ 프론트엔드 서버 시작 중... (포트 3000)"
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    echo "✅ 개발 서버가 시작되었습니다!"
    echo ""
    echo "🌐 프론트엔드: http://localhost:3000"
    echo "🔧 백엔드 API: http://localhost:8000"
    echo "📖 API 문서: http://localhost:8000/docs"
    echo ""
    echo "종료하려면 Ctrl+C를 누르세요."
    
    # 종료 신호 처리
    trap "echo '🛑 서버를 종료합니다...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
    
    # 대기
    wait
}

# 메인 실행
main() {
    check_env_file
    install_dependencies
    check_database
    start_servers
}

# 스크립트 실행
main
