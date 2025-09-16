#!/bin/bash

# KetoHelper 프로젝트 설정 스크립트

echo "🥑 KetoHelper 프로젝트 설정을 시작합니다..."

# 환경 변수 파일 확인
if [ ! -f .env ]; then
    echo "📝 .env 파일을 생성합니다..."
    cp env.example .env
    echo "⚠️  .env 파일에서 필요한 환경 변수들을 설정해주세요!"
fi

# Node.js 버전 확인
echo "📦 Node.js 버전을 확인합니다..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js $NODE_VERSION 발견"
    
    # Node.js 18+ 확인
    MAJOR_VERSION=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
    if [ "$MAJOR_VERSION" -lt 18 ]; then
        echo "❌ Node.js 18 이상이 필요합니다. 현재 버전: $NODE_VERSION"
        exit 1
    fi
else
    echo "❌ Node.js가 설치되어 있지 않습니다."
    echo "   https://nodejs.org에서 Node.js 18 이상을 설치해주세요."
    exit 1
fi

# Python 버전 확인
echo "🐍 Python 버전을 확인합니다..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ $PYTHON_VERSION 발견"
    
    # Python 3.11+ 확인
    PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        echo "❌ Python 3.11 이상이 필요합니다. 현재 버전: $PYTHON_VERSION"
        exit 1
    fi
else
    echo "❌ Python3가 설치되어 있지 않습니다."
    echo "   https://python.org에서 Python 3.11 이상을 설치해주세요."
    exit 1
fi

# 프론트엔드 의존성 설치
echo "🎨 프론트엔드 의존성을 설치합니다..."
cd frontend
if [ -f package.json ]; then
    npm install
    if [ $? -eq 0 ]; then
        echo "✅ 프론트엔드 의존성 설치 완료"
    else
        echo "❌ 프론트엔드 의존성 설치 실패"
        exit 1
    fi
else
    echo "❌ frontend/package.json을 찾을 수 없습니다."
    exit 1
fi
cd ..

# 백엔드 가상환경 및 의존성 설치
echo "⚙️ 백엔드 가상환경을 설정합니다..."
cd backend

# 가상환경 생성
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 가상환경 생성 완료"
fi

# 가상환경 활성화
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# 의존성 설치
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ 백엔드 의존성 설치 완료"
    else
        echo "❌ 백엔드 의존성 설치 실패"
        exit 1
    fi
else
    echo "❌ backend/requirements.txt를 찾을 수 없습니다."
    exit 1
fi
cd ..

# MongoDB Atlas 설정 안내
echo "🗄️ MongoDB Atlas 설정이 필요합니다..."
echo "   1. https://www.mongodb.com/atlas 에서 계정 생성"
echo "   2. 무료 클러스터 생성 (M0 Sandbox)"
echo "   3. Database Access에서 사용자 생성"
echo "   4. Network Access에서 IP 허용 (0.0.0.0/0)"
echo "   5. Connect → Drivers → 연결 문자열 복사"
echo "   6. backend/.env 파일의 MONGODB_URL 업데이트"

echo ""
echo "🎉 KetoHelper 프로젝트 설정이 완료되었습니다!"
echo ""
echo "📋 다음 단계:"
echo "1. MongoDB Atlas 클러스터 생성 및 연결 문자열 설정"
echo "2. backend/.env 파일에서 MONGODB_URL 업데이트"
echo "3. 개발 서버를 시작하세요:"
echo "   • 프론트엔드: cd frontend && npm run dev"
echo "   • 백엔드: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo ""
echo "🌐 애플리케이션 URL:"
echo "   • 프론트엔드: http://localhost:3000"
echo "   • 백엔드 API: http://localhost:8000"
echo "   • API 문서: http://localhost:8000/docs"
echo ""
echo "Happy coding! 🥑"
