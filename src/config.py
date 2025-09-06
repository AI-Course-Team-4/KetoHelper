"""
환경 설정 관리 모듈
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# OpenAI 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 검증
def validate_config():
    """필수 환경 변수가 설정되어 있는지 확인"""
    missing = []
    
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    
    if missing:
        raise ValueError(f"다음 환경 변수가 설정되지 않았습니다: {', '.join(missing)}")
    
    return True
