#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 응답 생성 테스트 스크립트
실제 서버에서 레시피 요청을 보내고 LLM이 어떤 응답을 생성하는지 확인
"""

import asyncio
import sys
import os
from pathlib import Path

# 한글 인코딩 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.orchestrator import KetoCoachAgent

async def test_llm_response():
    print("🔍 LLM 응답 생성 테스트 시작...")
    
    # 오케스트레이터 인스턴스 생성
    agent = KetoCoachAgent()
    
    # 테스트 메시지 (더 명확하게)
    test_message = "아침에 먹을 키토 레시피 3개 추천해주세요"
    
    # 샘플 프로필 (알레르기/비선호 포함)
    sample_profile = {
        "allergies": ["새우", "땅콩"],
        "dislikes": ["브로콜리", "양파"],
        "goals_kcal": 1500,
        "goals_carbs_g": 20
    }
    
    print(f"📝 테스트 메시지: {test_message}")
    print(f"👤 샘플 프로필: {sample_profile}")
    print("\n" + "="*50)
    
    try:
        # 실제 서버 요청 시뮬레이션
        result = await agent.process_message(
            message=test_message,
            profile=sample_profile,
            chat_history=None
        )
        
        print("🎯 결과 분석:")
        print(f"   📊 의도: {result.get('intent')}")
        print(f"   📊 검색 결과 개수: {len(result.get('results', []))}")
        print(f"   📊 도구 호출: {len(result.get('tool_calls', []))}")
        
        print("\n🔍 검색 결과:")
        for i, res in enumerate(result.get('results', [])[:3], 1):
            print(f"   {i}. {res.get('title', '제목 없음')}")
        
        print("\n💬 LLM 응답:")
        print("-" * 30)
        print(result.get('response', '응답 없음'))
        print("-" * 30)
        
        # 다양성 분석
        response_text = result.get('response', '')
        print("\n🔍 다양성 분석:")
        
        # 계란 관련 키워드 체크
        egg_keywords = ['계란', '달걀', 'egg', '스크램블', '오믈렛', '에그']
        egg_count = sum(1 for keyword in egg_keywords if keyword in response_text.lower())
        print(f"   🥚 계란 관련 레시피 개수: {egg_count}개")
        
        # 배추류 키워드 체크
        cabbage_keywords = ['양배추', '알배추', '배추']
        cabbage_count = sum(1 for keyword in cabbage_keywords if keyword in response_text.lower())
        print(f"   🥬 배추류 레시피 개수: {cabbage_count}개")
        
        # 조리법 다양성 체크
        cooking_methods = ['볶음', '전', '피자', '샐러드', '스테이크', '구이', '찜']
        method_count = sum(1 for method in cooking_methods if method in response_text.lower())
        print(f"   👨‍🍳 조리법 다양성: {method_count}가지")
        
        # 문제 진단
        print("\n🚨 문제 진단:")
        if egg_count > 1:
            print("   ⚠️ 계란 레시피가 중복됨")
        if cabbage_count > 1:
            print("   ⚠️ 배추류 레시피가 중복됨")
        if method_count < 2:
            print("   ⚠️ 조리법이 단조로움")
        
        if egg_count <= 1 and cabbage_count <= 1 and method_count >= 2:
            print("   ✅ 다양성이 잘 확보됨")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_response())
