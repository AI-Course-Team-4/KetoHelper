# scripts/eval_routing.py
# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Windows 콘솔에서 UTF-8 인코딩 설정
if sys.platform == "win32":
    import locale
    import codecs
    
    # 콘솔 코드페이지를 UTF-8로 설정
    try:
        import subprocess
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
    except:
        pass
    
    # stdout, stderr 인코딩 설정
    try:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)
    except:
        # 이미 텍스트 모드인 경우 무시
        pass

TEST_CASES = [
    # ===== meal_planning (40) ===== (식단 계획 + 레시피 통합)
    ("7일치 키토 식단 계획 짜줘", "meal_planning"),
    ("이번 주 일주일 메뉴표 부탁", "meal_planning"),
    ("평일 5일 점심 식단만 구성해줘", "meal_planning"),
    ("3일 동안 아침/점심/저녁 메뉴 정리해줘", "meal_planning"),
    ("다음 주 간단한 식단표 만들어 줘", "meal_planning"),
    ("주간 저탄수 식단 캘린더용으로 만들어줘", "meal_planning"),
    ("하루치 시범 식단 한 번 추천", "meal_planning"),
    ("주말 이틀 식단만 가볍게", "meal_planning"),
    ("이번 주 저녁 중심으로 6일치", "meal_planning"),
    ("나 매운걸로 식단 짜줘줘", "meal_planning"),
    ("간식 포함 일주일 메뉴 구성", "meal_planning"),
    ("초보자를 위한 3일 키토 식단", "meal_planning"),
    ("한 주 버전 7일 메뉴 세워줘", "meal_planning"),
    ("담백한 느낌으로 5일치 식단", "meal_planning"),
    ("출근일 기준 5일 점심 메뉴 계획", "meal_planning"),
    ("아침만 7일치로 가자", "meal_planning"),
    ("저녁만 3일치 부탁해", "meal_planning"),
    ("일주일 균형 있게 식단 짜줘", "meal_planning"),
    ("이번주 식단표 PDF로 만들 예정이야, 안에 들어갈 메뉴만 정리", "meal_planning"),
    ("7일 순환 식단 계획 추천", "meal_planning"),
    ("돼지고기 수육 레시피 알려줘", "meal_planning"),
    ("버섯 오믈렛 만드는 법 알려줘", "meal_planning"),
    ("새우 아보카도 샐러드 어떻게 해?", "meal_planning"),
    ("양상추 랩(키토 랩) 레시피 줘", "meal_planning"),
    ("코코넛 밀크 카레 만드는법", "meal_planning"),
    ("콜리플라워 피자 도우 레시피", "meal_planning"),
    ("두부 스크램블 만드는 법", "meal_planning"),
    ("버팔로 치킨 윙 소스 레시피", "meal_planning"),
    ("연어 스테이크 굽는 방법", "meal_planning"),
    ("차슈 없이 차슈맛 돼지고기 어떻게?", "meal_planning"),
    ("코울슬로 드레싱 레시피", "meal_planning"),
    ("에그 마요 샌드 대체 레시피(빵 없이)", "meal_planning"),
    ("브로콜리 치즈 수프 만드는 법", "meal_planning"),
    ("구운 가지 샐러드 레시피", "meal_planning"),
    ("아몬드가루 팬케이크 레시피", "meal_planning"),
    ("저탄 파에야 비슷하게 만드는 법", "meal_planning"),
    ("치즈볼(키토 버전) 만드는법", "meal_planning"),
    ("참치마요 한 그릇(밥 없이) 레시피", "meal_planning"),
    ("토마토 없이 볼로네즈 소스 레시피", "meal_planning"),
    ("닭가슴살 너겟 에어프라이어 조리법", "meal_planning"),

    # ===== restaurant_search (20) =====
    ("강남구청역 주변 키토 메뉴 되는 곳 찾아줘", "restaurant_search"),
    ("선릉역 근처 샐러드 맛집 어디야?", "restaurant_search"),
    ("내 위치 기준 포케 파는 식당 추천", "restaurant_search"),
    ("서초역 부근 저탄수 메뉴 가능한 레스토랑", "restaurant_search"),
    ("주변에 스테이크 괜찮은 집 알려줘", "restaurant_search"),
    ("역삼동 카페 중 당 적은 디저트 있는 곳", "restaurant_search"),
    ("잠실 근방 고기 맛집 찾아줘", "restaurant_search"),
    ("근처 샐러드바나 그릭요거트 되는 곳", "restaurant_search"),
    ("한티역 주변 포장 가능한 식당 추천", "restaurant_search"),
    ("걸어서 갈 수 있는 거리 맛집 알려줘", "restaurant_search"),
    ("비 오는 날 가기 좋은 식당 가까운데", "restaurant_search"),
    ("주차 편한 레스토랑 근처에 있을까?", "restaurant_search"),
    ("테라스 좌석 있는 카페 주변 추천", "restaurant_search"),
    ("점심 웨이팅 짧은 곳 어디 있어?", "restaurant_search"),
    ("야채 많은 메뉴 파는 집 근처", "restaurant_search"),
    ("강남역 11번 출구 쪽 맛집 추천해줘", "restaurant_search"),
    ("회사 근처 단체석 가능한 식당", "restaurant_search"),
    ("포장마차 말고 깔끔한 집 근처 알려줘", "restaurant_search"),
    ("늦은 시간까지 하는 곳 주변 찾아줘", "restaurant_search"),
    ("비프 샐러드 메뉴 있는 식당 근처", "restaurant_search"),

    # ===== calendar_save (20) =====
    ("방금 만든 주간 식단을 내 캘린더에 바로 저장해줘", "calendar_save"),
    ("오늘 일정으로 아침 메뉴 등록해줘", "calendar_save"),
    ("구글 캘린더 이벤트로 식단 넣어줘", "calendar_save"),
    ("이번 주 식단 일정을 한 번에 추가", "calendar_save"),
    ("내 캘린더에 점심만 반복 등록", "calendar_save"),
    ("수요일 저녁 메뉴를 일정에 기록", "calendar_save"),
    ("알림 30분 전으로 설정해서 캘린더 저장", "calendar_save"),
    ("식단표를 일정 항목으로 동기화해줘", "calendar_save"),
    ("다음 주 월~금 점심 식단 캘린더에 반영", "calendar_save"),
    ("주말 식단 일정 추가 부탁", "calendar_save"),
    ("캘린더에 오늘 간식 시간도 같이 넣어", "calendar_save"),
    ("식단 일정 업데이트해서 저장해줘", "calendar_save"),
    ("메뉴 변경 반영해서 일정 재등록", "calendar_save"),
    ("그룹 캘린더에도 복사 저장해줘", "calendar_save"),
    ("아침/점심/저녁 전부 일정으로 만들어", "calendar_save"),
    ("이번주 목·금 점심만 일정 등록", "calendar_save"),
    ("식단 계획 캘린더 공유 링크로 저장", "calendar_save"),
    ("캘린더 제목은 'Keto Plan'으로 저장", "calendar_save"),
    ("내 캘린더 메모에 식단 링크 첨부", "calendar_save"),
    ("식단 알림 켜고 일정으로 저장해줘", "calendar_save"),

    # ===== general (20) ===== (memory + general_chat 통합)
    ("브로콜리 싫어해 - 기억해줘", "general"),
    ("새우 알레르기 있어", "general"),
    ("땅콩 못 먹어", "general"),
    ("유제품 싫어해", "general"),
    ("기억해줘 - 매운거 안돼", "general"),
    ("안녕 반가워!", "general"),
    ("도움이 필요해", "general"),
    ("사용 방법 좀 알려줄래?", "general"),
    ("오늘 일정 어때 보여?", "general"),
    ("고마워 정말", "general"),
    ("지금 뭐 할 수 있어?", "general"),
    ("예시 몇 개 보여줘", "general"),
    ("설정은 어디서 바꿔?", "general"),
    ("다시 시작하고 싶어", "general"),
    ("좋은 하루 보내", "general"),
    ("헬로우", "general"),
    ("하이 거기", "general"),
    ("오케이 알겠어", "general"),
    ("괜찮아, 넘어가자", "general"),
    ("지금은 괜찮아 고마워", "general"),
]



async def evaluate_routing_accuracy():
    from app.core.intent_classifier import IntentClassifier
    classifier = IntentClassifier()
    correct = 0
    total = len(TEST_CASES)

    preview_count = 5  # 한글 출력 확인용 짧은 프리뷰 개수

    for idx, (message, expected_intent) in enumerate(TEST_CASES):
        result = await classifier.classify(message)
        # Enum.value 또는 문자열 처리
        predicted = getattr(result["intent"], "value", result["intent"])
        # 프리뷰: 처음 N개만 간단히 결과 표시 (한글 깨짐 체크용)
        if idx < preview_count:
            try:
                print(f"[PREVIEW] 문장: {message} | 의도: {predicted} | 신뢰도: {result.get('confidence', 0.0):.2f}")
            except Exception:
                # 인코딩 문제 발생 시에도 테스트가 중단되지 않도록 안전 처리
                pass
        if predicted == expected_intent:
            correct += 1
        else:
            print(f"[X] '{message}' -> 예상: {expected_intent}, 실제: {predicted}")

    acc = correct / total
    print(f"[OK] 정확도: {acc:.2%} ({correct}/{total}) | 목표: 90%+")
    return acc

if __name__ == "__main__":
    import asyncio
    asyncio.run(evaluate_routing_accuracy())
