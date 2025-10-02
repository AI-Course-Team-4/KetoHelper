#!/usr/bin/env python3
"""
gpt-4o-mini duration parsing 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tools.shared.date_parser import DateParser

def test_duration_parsing():
    """duration parsing 테스트"""
    print("🧪 Duration Parsing 테스트 시작")
    print("=" * 50)
    
    parser = DateParser()
    
    # 테스트 케이스들
    test_cases = [
        "오늘 식단표 생성해줘",
        "3일치 식단표 만들어줘", 
        "다음주 식단표",
        "7일치 계획해줘",
        "내일 식단표",
        "2주치 식단표",
        "5일간 식단표",
        "일주일치 식단표"
    ]
    
    for test_input in test_cases:
        print(f"\n📝 입력: '{test_input}'")
        
        # 대화 맥락 포함 테스트
        chat_history = ["식단표 생성해줘", "키토 식단으로 만들어줘"]
        result = parser.parse_natural_date_with_context(test_input, chat_history)
        
        if result:
            print(f"✅ 성공: {result.description}")
            print(f"   📅 날짜: {result.date}")
            print(f"   📊 일수: {result.duration_days}일 (기본값: 7)")
            print(f"   🔍 방법: {result.method}")
            print(f"   📈 신뢰도: {result.confidence}")
        else:
            print("❌ 실패: 파싱되지 않음")
    
    print("\n" + "=" * 50)
    print("🏁 테스트 완료")

if __name__ == "__main__":
    test_duration_parsing()
