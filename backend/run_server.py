"""
키토 코치 서버 실행 스크립트 (경로 문제 해결)
"""

import os
import sys
import uvicorn

# 현재 디렉토리를 Python path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    print("키토 코치 서버를 시작합니다...")
    print("주소: http://localhost:8000")
    print("API 문서: http://localhost:8000/docs")
    print("Ctrl+C로 종료")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
