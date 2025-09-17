@echo off
echo 🚀 키토 코치 환경 설정을 시작합니다...
echo.

echo 📋 필요한 정보 준비 체크리스트:
echo.
echo 1. Supabase 프로젝트 생성 완료 여부
echo 2. OpenAI API 키 발급 여부  
echo 3. 카카오 디벨로퍼스 API 키 발급 여부
echo.

set /p continue="위 정보가 모두 준비되었나요? (y/n): "
if /i "%continue%"=="n" (
    echo.
    echo ❌ 먼저 다음 링크에서 필요한 API 키들을 발급받으세요:
    echo.
    echo 1. Supabase: https://supabase.com
    echo 2. OpenAI: https://platform.openai.com/api-keys
    echo 3. 카카오: https://developers.kakao.com
    echo.
    pause
    exit /b 1
)

echo.
echo 📁 환경 변수 파일을 생성합니다...
echo.

REM 백엔드 .env 파일 생성
if not exist "backend\.env" (
    echo 📄 backend/.env 파일 생성 중...
    copy "backend\env_template.txt" "backend\.env"
    echo ✅ backend/.env 파일이 생성되었습니다.
) else (
    echo ⚠️ backend/.env 파일이 이미 존재합니다.
)

REM 프론트엔드 .env 파일 생성
if not exist "frontend\.env" (
    echo 📄 frontend/.env 파일 생성 중...
    copy "frontend\env_template.txt" "frontend\.env"
    echo ✅ frontend/.env 파일이 생성되었습니다.
) else (
    echo ⚠️ frontend/.env 파일이 이미 존재합니다.
)

echo.
echo 🔧 다음 단계:
echo.
echo 1. backend\.env 파일을 편집기로 열어서 실제 값들로 교체하세요:
echo    - Supabase 프로젝트 URL, API 키, 데이터베이스 비밀번호
echo    - OpenAI API 키
echo    - 카카오 REST API 키
echo.
echo 2. frontend\.env 파일을 편집기로 열어서 실제 값들로 교체하세요:
echo    - Supabase 프로젝트 URL, anon 키
echo    - 카카오 JavaScript 키
echo.
echo 3. Supabase SQL Editor에서 docs\database_setup.sql 실행
echo.
echo 4. 개발 서버 실행: scripts\start_dev.bat
echo.

pause
