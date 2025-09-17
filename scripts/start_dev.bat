@echo off
echo 🚀 키토 코치 개발 환경을 시작합니다...

REM 환경 변수 체크
if not exist "backend\.env" (
    echo ❌ backend\.env 파일이 없습니다.
    echo 📝 backend\env.example을 참고하여 .env 파일을 생성하세요.
    echo.
    echo 필요한 API 키들:
    echo - OPENAI_API_KEY: OpenAI API 키
    echo - KAKAO_REST_KEY: 카카오 REST API 키
    echo - DATABASE_URL: Supabase 데이터베이스 URL
    echo - SUPABASE_URL: Supabase 프로젝트 URL
    echo - SUPABASE_ANON_KEY: Supabase Anon 키
    echo.
    pause
    exit /b 1
)

REM Python 가상환경 생성
if not exist "backend\venv" (
    echo 🐍 Python 가상환경을 생성합니다...
    cd backend
    python -m venv venv
    cd ..
)

REM 백엔드 의존성 설치
echo 📚 백엔드 의존성 설치...
cd backend
call venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..

REM 프론트엔드 의존성 설치
echo ⚛️ 프론트엔드 의존성 설치...
cd frontend
if not exist "node_modules" (
    npm install
)
cd ..

echo 🗄️ 데이터베이스 스키마를 확인합니다...
echo Supabase SQL Editor에서 docs\database_setup.sql을 실행했는지 확인하세요.

echo 🌟 개발 서버를 시작합니다...

REM 백엔드 서버 시작 (새 창에서)
echo 🔧 백엔드 서버 시작 중... (포트 8000)
start "Keto Coach Backend" cmd /k "cd backend && venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

REM 잠시 대기
timeout /t 3 /nobreak >nul

REM 프론트엔드 서버 시작 (새 창에서)
echo ⚛️ 프론트엔드 서버 시작 중... (포트 3000)
start "Keto Coach Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ✅ 개발 서버가 시작되었습니다!
echo.
echo 🌐 프론트엔드: http://localhost:3000
echo 🔧 백엔드 API: http://localhost:8000
echo 📖 API 문서: http://localhost:8000/docs
echo.
echo 각 서버는 별도 창에서 실행 중입니다.
echo 종료하려면 각 창을 닫으세요.

pause
