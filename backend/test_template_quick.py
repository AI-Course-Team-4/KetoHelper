"""
템플릿 응답 빠른 테스트
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.prompts.chat.general_templates import get_general_response_template

# 테스트 케이스들
test_cases = [
    "키토 다이어트는 어떤걸 먹으면 안돼?",
    "키토에서 피해야 할 음식은?",
    "키토 다이어트가 뭐야?",
    "안녕하세요",
    "키토 시작하려고 해"
]

print("=" * 80)
print("🧪 템플릿 키워드 매칭 테스트")
print("=" * 80)

for i, message in enumerate(test_cases, 1):
    print(f"\n{i}. 메시지: {message}")
    response = get_general_response_template(message, profile=None)
    
    # 응답 타입 확인
    if "🤔 질문해주셔서 감사합니다" in response:
        print("   ❌ 기본 응답 (템플릿 미매칭)")
    elif "🥑 키토 다이어트란?" in response:
        print("   ✅ 키토 설명 템플릿 (성공!)")
    elif "👋 안녕하세요" in response:
        print("   ✅ 인사 템플릿")
    elif "키토 시작 가이드" in response or "첫 주 적응기" in response:
        print("   ✅ 키토 시작 템플릿")
    else:
        print("   ⚠️  기타 템플릿")
    
    # 응답 미리보기
    preview = response.split('\n')[0][:60]
    print(f"   응답 미리보기: {preview}...")

print("\n" + "=" * 80)
print("✅ 테스트 완료")
print("=" * 80)

