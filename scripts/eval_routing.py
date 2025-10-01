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
    # ==== meal_plan (식단표 생성) ====
    ("한 달치 키토 식단 로테이션 만들어줘", "meal_plan"),
    ("초보자를 위한 5일 저탄수 아침·점심 구성", "meal_plan"),
    ("출근용 도시락 위주로 2주 식단", "meal_plan"),
    ("탄수 20g 이하 일주일 메뉴", "meal_plan"),
    ("유당 불내증 고려한 7일 저탄수", "meal_plan"),
    ("돼지고기 제외 3일 플랜", "meal_plan"),
    ("운동 전후 간식 포함 1주 루틴", "meal_plan"),
    ("냉동가능 메뉴로 5일 식단", "meal_plan"),
    ("전자레인지로 가능한 4일 저녁", "meal_plan"),
    ("간단 조리 15분 내 6끼 구성", "meal_plan"),
    ("주말 브런치 2회 구성 제안", "meal_plan"),
    ("맵기 0단계 일주일 저녁 추천", "meal_plan"),
    ("해산물 위주 5일 식단 구성", "meal_plan"),
    ("붉은 고기 줄인 7일 구성", "meal_plan"),
    ("간헐적 단식 16:8에 맞춘 하루 계획", "meal_plan"),
    ("야채 다양성 높인 7끼 추천", "meal_plan"),
    ("오피스에서 먹기 좋은 냄새 적은 메뉴", "meal_plan"),
    ("예산 절약형 1주 식단(10만 원 이하)", "meal_plan"),
    ("샐러드만으로 3일치 구성", "meal_plan"),
    ("칼로리 1500kcal 목표 1일 식단", "meal_plan"),
    ("집밥 재료로 5일 저탄 메뉴", "meal_plan"),
    ("한국식 반찬 스타일 1주 플랜", "meal_plan"),
    ("비건 키토 가능한 2일 메뉴", "meal_plan"),
    ("냉장고 파먹기 기준으로 구성해줘", "meal_plan"),
    ("요리 초보도 가능한 3끼 추천", "meal_plan"),
    
    # ==== recipe_search (레시피/조리법) ====
    ("닭가슴살 수비드 최적 온도 알려줘", "recipe_search"),
    ("에어프라이어 베이컨 칩 만드는 법", "recipe_search"),
    ("콜리플라워 라이스 볶음밥 레시피", "recipe_search"),
    ("두부 스테이크 겉바속촉 비법", "recipe_search"),
    ("계란버터 스크램블 크리미하게", "recipe_search"),
    ("아보카도 참치 샐러드 드레싱", "recipe_search"),
    ("저탄수 김치볶음 밥 없이 조리법", "recipe_search"),
    ("코코넛가루 팬케이크 레시피", "recipe_search"),
    ("주키니 누들 알리오올리오", "recipe_search"),
    ("당 없는 타르타르 소스 만들기", "recipe_search"),
    ("키토 빵 없는 햄버거 볼 레시피", "recipe_search"),
    ("노오븐 치즈케이크 저당 레시피", "recipe_search"),
    ("버터 대신 올리브유 버전으로 바꿔줘", "recipe_search"),
    ("버섯 크림수프(무루) 저탄 레시피", "recipe_search"),
    ("오트는 제외, 대체 재료 추천", "recipe_search"),

    
    # ==== place_search (식당 검색) ====
    ("광화문 근처 저탄수 메뉴 잘하는 곳", "place_search"),
    ("홍대입구역 포케 집 추천해줘", "place_search"),
    ("잠실 롯데타워 주변 샐러드 맛집?", "place_search"),
    ("성수동에서 키토 가능한 카페 알려줘", "place_search"),
    ("한남동 스테이크 괜찮은 곳 예약 가능?", "place_search"),
    ("비건 옵션 있는 저당 디저트 카페", "place_search"),
    ("강북역 인근 야외 좌석 레스토랑", "place_search"),
    ("퇴근길 포장 쉬운 샐러드 가게", "place_search"),
    ("늦은 밤 12시 이후 영업 식당", "place_search"),
    ("주차 무료 가능한 고기집 찾아줘", "place_search"),
    ("웨이팅 적은 포케 매장 어디?", "place_search"),
    ("반려견 동반 가능한 테라스 카페", "place_search"),
    ("매운맛 약한 메뉴 많은 곳", "place_search"),
    ("샐러드바 위생 좋은 곳 추천", "place_search"),
    ("무설탕 디저트 확실히 파는 카페", "place_search"),
    ("단체 8명 자리 넓은 레스토랑", "place_search"),
    ("역세권 5분 내 저탄수 식당", "place_search"),
    ("포장 할인 있는 샐러드 가게", "place_search"),
    ("비 오는 날 가기 좋은 한적한 카페", "place_search"),
    ("닭가슴살 샐러드 맛있는 집", "place_search"),

    # ==== calendar_save (캘린더 저장) ====
    ("이번 주 저녁 식단을 구글 캘린더에 추가", "calendar_save"),
    ("내일 아침 메뉴 일정으로 저장해줘", "calendar_save"),
    ("월~금 점심 반복 이벤트로 등록", "calendar_save"),
    ("주중 식단 전체를 한 번에 일정화", "calendar_save"),
    ("수요일 간식 시간 알림 10분 전으로", "calendar_save"),
    ("일요일 브런치 일정 생성 후 공유", "calendar_save"),
    ("식단 링크 메모에 첨부해서 일정 저장", "calendar_save"),
    ("캘린더 초대에 가족도 포함해줘", "calendar_save"),
    ("오늘 저녁만 일정 업데이트", "calendar_save"),
    ("변경된 재료 반영해서 재등록", "calendar_save"),
    ("공유 캘린더 복사본도 만들어줘", "calendar_save"),
    ("아점저 각각 개별 일정으로 추가", "calendar_save"),
    ("알림 끄고 조용히 저장", "calendar_save"),
    ("다음 주 5일 점심만 캘린더 반영", "calendar_save"),
    ("식단 제목은 Keto Plan v2", "calendar_save"),
    ("ICS 파일로도 내보내며 저장", "calendar_save"),
    ("반복 종료일을 이번 달 말로 설정", "calendar_save"),
    ("푸시 알림 켠 상태로 저장 완료", "calendar_save"),
    ("회사 캘린더에도 동기화해줘", "calendar_save"),
    ("시간대는 KST로 설정해서 등록", "calendar_save"),

    # ==== general (일반 대화/프로필 메모) ====
    ("버섯은 싫어하니 빼줘, 기억해", "general"),
    ("달걀 알레르기 있어, 메모 부탁", "general"),
    ("돼지고기 대신 소고기 위주로", "general"),
    ("너무 짜지 않게 해줘, 기억", "general"),
    ("오늘 컨디션이 별로야", "general"),
    ("도움말 메뉴 어디 있지?", "general"),
    ("앱 기능 간단히 소개해줘", "general"),
    ("할 일 체크리스트 만들어줄래?", "general"),
    ("항상 고마워, 잘하고 있어", "general"),
    ("현재 지원하는 명령 알려줘", "general"),
    ("예시 대화 몇 개 보여줘", "general"),
    ("환경설정 리셋은 어디에서 해?", "general"),
    ("대화 내용 초기화해줘", "general"),
    ("굿나잇, 내일 봐", "general"),
    ("테스트 중이라 몇 가지 물어볼게", "general"),
    ("오키, 이해 완료", "general"),
    ("괜찮아. 다음 질문으로 가자", "general"),
    ("오늘 도움 충분했어, 고마워", "general"),
    ("내 취향 요약해서 저장해줘", "general"),
    ("앞으로 맵기 1 이하로 기억해", "general"),

]





async def evaluate_routing_accuracy():
    from app.core.intent_classifier import IntentClassifier
    classifier = IntentClassifier()
    correct = 0
    total = len(TEST_CASES)

    preview_count = 5  # 한글 출력 확인용 짧은 프리뷰 개수

    for idx, (message, expected_intent) in enumerate(TEST_CASES):
        # 실제 orchestrator.py와 동일한 방식으로 context 전달
        # 빈 컨텍스트로 테스트 (실제 프론트엔드와 동일)
        context = ""
        result = await classifier.classify(message, context)
        
        # 디버깅: 실제 프롬프트 확인
        if idx == 0:  # 첫 번째 테스트 케이스만
            from app.prompts.chat.intent_classification import get_intent_prompt
            prompt = get_intent_prompt(message)
            print(f"🔍 실제 사용되는 프롬프트 (첫 200자): {prompt[:200]}...")
        # Enum.value 또는 문자열 처리
        predicted = getattr(result["intent"], "value", result["intent"])
        # 프리뷰: 처음 N개만 간단히 결과 표시 (한글 깨짐 체크용)
        if idx < preview_count:
            try:
                reasoning = result.get('reasoning', '')
                print(f"[PREVIEW] 문장: {message} | 의도: {predicted} | 신뢰도: {result.get('confidence', 0.0):.2f}")
                if reasoning:
                    print(f"  💭 추론: {reasoning}")
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
