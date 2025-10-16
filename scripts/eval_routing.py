"""
의도분류 정확도 테스트 스크립트
예상 의도와 실제 분기된 의도가 일치하는지 테스트하는 파일입니다.
"""
# scripts/eval_routing.py
# -*- coding: utf-8 -*-
import sys
import os
import time
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





async def evaluate_routing_accuracy(clear_cache=True):
    from app.core.intent_classifier import IntentClassifier
    classifier = IntentClassifier()
    
    # 캐시 초기화 (토큰 사용량 정확한 측정을 위해)
    if clear_cache and classifier.cache:
        try:
            # Redis 캐시의 intent 관련 키만 삭제
            print("🔄 캐시 초기화 중...")
            # Redis 패턴 매칭으로 intent_classify:* 키만 삭제
            if hasattr(classifier.cache, 'redis'):
                keys = classifier.cache.redis.keys("intent_classify:*")
                if keys:
                    classifier.cache.redis.delete(*keys)
                    print(f"✅ {len(keys)}개의 캐시 키 삭제 완료")
                else:
                    print("✅ 삭제할 캐시 키 없음")
        except Exception as e:
            print(f"⚠️  캐시 초기화 실패: {e}")
    
    correct = 0
    total = len(TEST_CASES)
    
    # 시간 측정을 위한 리스트
    classification_times = []
    
    # 의도별 통계를 위한 딕셔너리
    intent_stats = {}  # {intent: {"correct": 0, "total": 0}}
    
    # 실패한 케이스들을 모으는 리스트
    failed_cases = []  # [(message, expected, predicted, confidence, reasoning)]
    
    # 빈 응답 케이스들을 모으는 리스트
    empty_response_cases = []  # [(message, expected, error_info)]
    empty_response_count = 0
    
    # 토큰 사용량 추적
    token_stats = {
        "prompt_tokens": [],
        "completion_tokens": [],
        "total_tokens": []
    }

    preview_count = 5  # 한글 출력 확인용 짧은 프리뷰 개수

    for idx, (message, expected_intent) in enumerate(TEST_CASES):
        # 실제 orchestrator.py와 동일한 방식으로 context 전달
        # 빈 컨텍스트로 테스트 (실제 프론트엔드와 동일)
        context = ""
        
        # 시간 측정 시작
        start_time = time.time()
        try:
            result = await classifier.classify(message, context)
            end_time = time.time()
            
            # 빈 응답 체크
            if result is None or not result or "intent" not in result:
                empty_response_count += 1
                elapsed_ms = (end_time - start_time) * 1000
                classification_times.append(elapsed_ms)
                empty_response_cases.append({
                    "message": message,
                    "expected": expected_intent,
                    "error_info": "응답이 None이거나 intent 필드가 없음"
                })
                print(f"[{idx+1}/{total}] ⚠️  {message[:40]}... | 빈 응답 발생 | 시간: {elapsed_ms:.2f}ms")
                continue
            
            # intent 값이 빈 문자열인지 체크
            predicted_raw = result.get("intent")
            if not predicted_raw or str(predicted_raw).strip() == "":
                empty_response_count += 1
                elapsed_ms = (end_time - start_time) * 1000
                classification_times.append(elapsed_ms)
                empty_response_cases.append({
                    "message": message,
                    "expected": expected_intent,
                    "error_info": f"intent 값이 비어있음: {predicted_raw}"
                })
                print(f"[{idx+1}/{total}] ⚠️  {message[:40]}... | 빈 응답 발생 | 시간: {elapsed_ms:.2f}ms")
                continue
                
        except Exception as e:
            end_time = time.time()
            empty_response_count += 1
            elapsed_ms = (end_time - start_time) * 1000
            classification_times.append(elapsed_ms)
            empty_response_cases.append({
                "message": message,
                "expected": expected_intent,
                "error_info": f"예외 발생: {str(e)}"
            })
            print(f"[{idx+1}/{total}] ⚠️  {message[:40]}... | 예외 발생 | 시간: {elapsed_ms:.2f}ms")
            continue
        
        # 소요 시간 기록 (밀리초 단위)
        elapsed_ms = (end_time - start_time) * 1000
        classification_times.append(elapsed_ms)
        
        # 토큰 사용량 수집
        token_usage = result.get("token_usage", {})
        if token_usage and token_usage.get("total_tokens", 0) > 0:
            if "prompt_tokens" in token_usage:
                token_stats["prompt_tokens"].append(token_usage["prompt_tokens"])
            if "completion_tokens" in token_usage:
                token_stats["completion_tokens"].append(token_usage["completion_tokens"])
            if "total_tokens" in token_usage:
                token_stats["total_tokens"].append(token_usage["total_tokens"])
        else:
            # 토큰 정보가 없는 경우 - 캐시 히트 또는 키워드 분류일 가능성
            method = result.get("method", "unknown")
            if idx < 3:  # 처음 3개만 출력
                print(f"    ⚠️  토큰 정보 없음 (method: {method})")
        
        # 디버깅: 실제 프롬프트 확인
        if idx == 0:  # 첫 번째 테스트 케이스만
            from app.prompts.chat.intent_classification import get_intent_prompt
            prompt = get_intent_prompt(message)
            print(f"🔍 실제 사용되는 프롬프트 (첫 200자): {prompt[:200]}...")
        # Enum.value 또는 문자열 처리
        predicted = getattr(result["intent"], "value", result["intent"])
        
        # 의도별 통계 업데이트
        if expected_intent not in intent_stats:
            intent_stats[expected_intent] = {"correct": 0, "total": 0}
        intent_stats[expected_intent]["total"] += 1
        
        # 모든 케이스의 개별 응답 시간 출력
        match_symbol = "✓" if predicted == expected_intent else "✗"
        try:
            print(f"[{idx+1}/{total}] {match_symbol} {message[:40]}... | 의도: {predicted} | 시간: {elapsed_ms:.2f}ms")
        except Exception:
            # 인코딩 문제 발생 시에도 테스트가 중단되지 않도록 안전 처리
            pass
        
        if predicted == expected_intent:
            correct += 1
            intent_stats[expected_intent]["correct"] += 1
        else:
            print(f"    ❌ 예상: {expected_intent}, 실제: {predicted}")
            # 실패한 케이스 기록
            failed_cases.append({
                "message": message,
                "expected": expected_intent,
                "predicted": predicted,
                "confidence": result.get("confidence", 0.0),
                "reasoning": result.get("reasoning", "")
            })

    acc = correct / total
    print(f"\n{'='*60}")
    print(f"[OK] 전체 정확도: {acc:.2%} ({correct}/{total}) | 목표: 90%+")
    
    # 빈 응답 통계 출력
    print(f"\n⚠️  빈 응답 통계:")
    print(f"   빈 응답 발생 횟수: {empty_response_count}회")
    print(f"   빈 응답 비율: {empty_response_count/total:.2%} ({empty_response_count}/{total})")
    
    # 의도별 정확도 출력
    print(f"\n📊 의도별 정확도:")
    for intent in sorted(intent_stats.keys()):
        stats = intent_stats[intent]
        intent_acc = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        print(f"   {intent:20s}: {intent_acc:.2%} ({stats['correct']}/{stats['total']})")
    
    # 시간 통계 출력
    if classification_times:
        avg_time = sum(classification_times) / len(classification_times)
        min_time = min(classification_times)
        max_time = max(classification_times)
        print(f"\n⏱️  의도분류 소요 시간 통계:")
        print(f"   평균: {avg_time:.2f}ms")
        print(f"   최소: {min_time:.2f}ms")
        print(f"   최대: {max_time:.2f}ms")
        print(f"   전체 테스트 시간: {sum(classification_times)/1000:.2f}초")
    
    # 토큰 사용량 통계 출력
    if token_stats["total_tokens"]:
        avg_prompt = sum(token_stats["prompt_tokens"]) / len(token_stats["prompt_tokens"])
        avg_completion = sum(token_stats["completion_tokens"]) / len(token_stats["completion_tokens"])
        avg_total = sum(token_stats["total_tokens"]) / len(token_stats["total_tokens"])
        
        llm_call_count = len(token_stats["total_tokens"])
        
        print(f"\n🪙 토큰 사용량 통계 (LLM 호출 {llm_call_count}/{total}회):")
        print(f"   프롬프트 토큰:")
        print(f"      평균: {avg_prompt:.1f} tokens")
        print(f"      최소: {min(token_stats['prompt_tokens'])} tokens")
        print(f"      최대: {max(token_stats['prompt_tokens'])} tokens")
        print(f"      합계: {sum(token_stats['prompt_tokens'])} tokens")
        print(f"   응답 토큰:")
        print(f"      평균: {avg_completion:.1f} tokens")
        print(f"      최소: {min(token_stats['completion_tokens'])} tokens")
        print(f"      최대: {max(token_stats['completion_tokens'])} tokens")
        print(f"      합계: {sum(token_stats['completion_tokens'])} tokens")
        print(f"   전체 토큰:")
        print(f"      평균: {avg_total:.1f} tokens/request")
        print(f"      최소: {min(token_stats['total_tokens'])} tokens")
        print(f"      최대: {max(token_stats['total_tokens'])} tokens")
        print(f"      총 사용량: {sum(token_stats['total_tokens'])} tokens")
        
        if llm_call_count < total:
            print(f"\n   ℹ️  {total - llm_call_count}개 요청은 캐시/키워드 분류로 처리되어 LLM 호출 없음")
    else:
        print(f"\n⚠️  토큰 사용량 정보를 수집하지 못했습니다.")
        print(f"   💡 가능한 원인:")
        print(f"      - 모든 요청이 캐시에서 처리됨 (clear_cache=True로 재실행 권장)")
        print(f"      - 모든 요청이 키워드 분류로 처리됨")
        print(f"      - LLM 응답에 토큰 정보가 포함되지 않음")
    
    # 빈 응답 케이스 상세 출력
    if empty_response_cases:
        print(f"\n{'='*60}")
        print(f"⚠️  빈 응답 케이스 분석 (총 {len(empty_response_cases)}개)")
        print(f"{'='*60}")
        for i, case in enumerate(empty_response_cases, 1):
            try:
                print(f"\n[{i}] 메시지: {case['message']}")
                print(f"    예상 의도: {case['expected']}")
                print(f"    에러 정보: {case['error_info']}")
            except Exception:
                # 인코딩 문제 발생 시에도 출력이 중단되지 않도록 안전 처리
                pass
    
    # 실패한 케이스 상세 출력
    if failed_cases:
        print(f"\n{'='*60}")
        print(f"❌ 의도분류 실패 케이스 분석 (총 {len(failed_cases)}개)")
        print(f"{'='*60}")
        for i, case in enumerate(failed_cases, 1):
            try:
                print(f"\n[{i}] 메시지: {case['message']}")
                print(f"    예상 의도: {case['expected']}")
                print(f"    실제 분류: {case['predicted']}")
                print(f"    신뢰도: {case['confidence']:.2f}")
            except Exception:
                # 인코딩 문제 발생 시에도 출력이 중단되지 않도록 안전 처리
                pass
    
    # 모든 테스트 성공 여부
    if not failed_cases and not empty_response_cases:
        print(f"\n✅ 모든 테스트 케이스 통과!")
    
    return acc

if __name__ == "__main__":
    import asyncio
    # clear_cache=True로 설정하여 캐시 초기화 후 테스트 (토큰 사용량 정확히 측정)
    asyncio.run(evaluate_routing_accuracy(clear_cache=True))
