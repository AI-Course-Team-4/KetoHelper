#!/usr/bin/env python3
"""
하이브리드 검색 테스트 실행 파일
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.search_cli import main

if __name__ == "__main__":
    main()
