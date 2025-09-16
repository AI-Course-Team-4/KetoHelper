@echo off
echo 🔧 키토 코치 백엔드 의존성을 설치합니다...
echo.

echo 📍 현재 디렉토리: %CD%
echo.

echo 📦 Python 패키지 설치 중...
pip install fastapi uvicorn[standard]
pip install sqlalchemy psycopg[binary] 
pip install pgvector
pip install supabase
pip install langchain langgraph
pip install openai
pip install python-dotenv
pip install pydantic pydantic-settings
pip install httpx
pip install pytz
pip install icalendar

echo.
echo ✅ 의존성 설치 완료!
echo.
echo 🚀 테스트 서버 실행:
echo python test_server.py
echo.
echo 🚀 메인 서버 실행:
echo uvicorn app.main:app --reload
echo.
pause
