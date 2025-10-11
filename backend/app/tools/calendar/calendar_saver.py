"""
캘린더 저장 전용 도구
- 식단을 캘린더에 저장하는 핵심 로직
- Supabase meal_log 테이블과 연동
- 식당 저장 기능 확장 가능
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.shared.utils.calendar_utils import CalendarUtils
from app.tools.shared.date_parser import DateParser
from app.core.database import supabase


class CalendarSaver:
    """캘린더 저장 전용 도구"""

    def __init__(self):
        self.date_parser = DateParser()
        self.calendar_utils = CalendarUtils()

    async def save_meal_plan_to_calendar(
        self,
        state: Dict[str, Any],
        message: str,
        chat_history: List[str]
    ) -> Dict[str, Any]:
        """식단표를 캘린더에 저장하는 메인 함수"""
        
        print("🚀🚀🚀 save_meal_plan_to_calendar 함수 호출됨! 🚀🚀🚀")
        print(f"🔍 DEBUG: message = '{message}'")
        print(f"🔍 DEBUG: chat_history 길이 = {len(chat_history)}")
        print(f"🔍 DEBUG: state keys = {list(state.keys()) if state else 'None'}")

        try:
            # 로그인 체크 - 가장 먼저 확인
            user_id = self.calendar_utils.get_user_id_from_state(state)
            if not user_id:
                return {
                    "success": False,
                    "message": "🔒 캘린더에 저장하려면 로그인이 필요합니다. 로그인 후 다시 시도해주세요!"
                }
            

            # 날짜 파싱
            parsed_date = self.date_parser.extract_date_from_message_with_context(message, chat_history)
            
            print(f"🔍 DEBUG: 날짜 파싱 결과 - parsed_date: {parsed_date}")
            if parsed_date:
                print(f"🔍 DEBUG: 파싱된 날짜 상세 - date: {parsed_date.date}, description: {parsed_date.description}, method: {parsed_date.method}")

            if not parsed_date:
                return {
                    "success": False,
                    "message": "날짜를 파악할 수 없습니다. 더 구체적으로 말씀해주세요. (예: '다음주 월요일부터', '내일부터')"
                }

            # meal_plan_data를 찾기 - state에서 먼저 확인
            meal_plan_data = state.get("meal_plan_data")

            if not meal_plan_data:
                print(f"🔍 식단 추출 중: 기존 채팅 히스토리 {len(chat_history)}개 메시지 분석")
                meal_plan_data = self.calendar_utils.find_recent_meal_plan(chat_history)

                # 메모리 히스토리에서 찾지 못한 경우 데이터베이스에서 직접 조회
                if not meal_plan_data and state.get("thread_id"):
                    meal_plan_data = await self._find_meal_plan_from_db(state["thread_id"])

            if not meal_plan_data:
                return {
                    "success": False,
                    "message": "저장할 식단을 찾을 수 없습니다. 먼저 식단을 생성해주세요."
                }

            # 사전 차단 로직 제거 - 부분 저장 로직으로 대체됨
            print(f"🔍 DEBUG: meal_plan_data 키들: {list(meal_plan_data.keys()) if meal_plan_data else 'None'}")
            print(f"🔍 DEBUG: has_banned_content 값: {meal_plan_data.get('has_banned_content', 'NOT_FOUND')}")
            print("✅ 사전 차단 로직 제거됨 - 부분 저장 로직 사용")

            # --- [수정된 로직 시작] ---
            # duration_days 추출 로직 수정 (더 강력한 보호 로직)
            print(f"🔍 DEBUG: parsed_date.duration_days = {parsed_date.duration_days}")
            
            # 특정 요일이 명시된 경우 먼저 확인
            is_specific_weekday = any(day in message.lower() for day in 
                ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'])
            
            # 1. 기본 parsed_date 값 우선 사용 (date_parser에서 파싱된 값)
            duration_days = parsed_date.duration_days
            print(f"🔍 초기 parsed_date에서 받은 값: {duration_days}일")
            
            # date_parser에서 파싱된 duration_days가 있으면 우선 사용
            if duration_days and duration_days > 0:
                print(f"✅ date_parser에서 파싱된 duration_days 사용: {duration_days}일")
            else:
                print(f"⚠️ date_parser에서 duration_days 파싱 실패 - 추가 로직 실행")

            # 1-1. '일주일'류 키워드 직접 매핑(숫자 미포함 표현 보호) - date_parser에서 파싱되지 않은 경우만
            if not duration_days or duration_days <= 0:
                week_keywords = ['일주일', '일주', '한 주', '한주', '일주간', '1주일']
                if any(k in message for k in week_keywords):
                    duration_days = 7
                    print("✅ '일주일' 키워드 감지 → duration_days = 7")
            
            # 2-1. 이전 대화에서 요일과 일수가 함께 언급된 경우 우선 체크 - date_parser에서 파싱되지 않은 경우만
            if not duration_days or duration_days <= 0 and is_specific_weekday:
                # 먼저 현재 메시지에도 일수 표현이 있는지 체크
                import re
                current_msg_patterns = [
                    (r'(\d+)일치', '일치'), (r'(\d+)주치', '주치'), 
                    (r'(\d+)일', '일'), (r'(\d+)주', '주')
                ]
                
                found_duration = None
                found_suffix = None
                for pattern, suffix in current_msg_patterns:
                    match = re.search(pattern, message.lower())
                    if match:
                        found_duration = int(match.group(1))
                        found_suffix = suffix
                        break
                
                # 한글 숫자도 체크 ("이틀치")
                korean_numbers = {'이틀': 2, '삼일': 3, '사일': 4, '오일': 5, '육일': 6}
                for kor_key, kor_val in korean_numbers.items():
                    if f"{kor_key}치" in message.lower():
                        found_duration = kor_val
                        found_suffix = '일'
                        break
                
                # 현재 메시지에서 못 찾았으면 이전 대화에서 찾기
                if not found_duration:
                    print(f"🔍 현재 메시지에서 일수 못 찾음 - 이전 대화에서 탐색 시작")
                    for history_msg in reversed(chat_history[-5:]):
                        print(f"🔍 이전 메시지 확인: '{history_msg.strip()[:80]}...'")
                        
                        # 한글 숫자 먼저 체크
                        for kor_key, kor_val in korean_numbers.items():
                            if f"{kor_key}치" in history_msg:
                                found_duration = kor_val
                                found_suffix = '일'
                                print(f"🔍 이전 대화에서 한글 {found_duration}일 감지!")
                                break
                        
                        if found_duration:
                            break
                        
                        # 아라비안 숫자 패턴들
                        for pattern_label, suffix in current_msg_patterns:
                            match = re.search(pattern_label, history_msg)
                            if match:
                                found_duration = int(match.group(1))
                                found_suffix = suffix
                                print(f"🔍 이전 대화에서 {found_duration}{suffix} 감지!")
                                break
                        
                        if found_duration:
                            break
                
                # 일수를 찾았으면 그것을 사용하되 요일 시작점은 유지
                if found_duration:
                    duration_days = found_duration
                    if found_suffix == '주':  # 주를 일로 변환
                        duration_days = found_duration * 7
                    print(f"🔍 다음주+요일에서 {duration_days}일 감지: '{message.strip()[:50]}...'")
                else:
                    duration_days = 1
                    print(f"🔍 요일만 언급되고 이전 대화에도 일수 없음 - 1일로 설정")
            # 3. 만약 파싱된 기간 정보가 없으면 식단 데이터에서 추론 - date_parser에서 파싱되지 않은 경우만
            found_duration_from_chat = False
            if not duration_days or duration_days <= 0:
                # 먼저 직전 대화에서 일수 정보 찾기
                duration_days = self._extract_duration_from_chat_history(chat_history, message)
                if duration_days and duration_days > 0:
                    found_duration_from_chat = True
                elif not duration_days or duration_days <= 0:
                    duration_days = self.calendar_utils.extract_duration_from_meal_plan(meal_plan_data, chat_history)

            # 4. 그래도 기간을 알 수 없다면 기본값(1일)으로 설정합니다.
            if not duration_days or duration_days <= 0:
                duration_days = 1
                print(f"⚠️ 기간을 특정할 수 없어 기본값 1일로 설정합니다.")
                
            # 🚨 식단 데이터 개수 기반 보정: 사용자가 명시적으로 요청한 일수 우선
            if meal_plan_data and "days" in meal_plan_data:
                actual_days_count = len(meal_plan_data["days"])
                print(f"🔍 DEBUG: 식단 데이터에서 {actual_days_count}개 일 찾음")
                
                # 사용자가 명시적으로 1일을 요청한 경우 보정하지 않음
                if duration_days == 1 and any(keyword in message.lower() for keyword in ['하루', '1일', '오늘', '내일']):
                    print(f"🔍 사용자가 1일을 명시적으로 요청 - 보정하지 않음")
                # "부터" 패턴으로 요청한 경우 - 식단 데이터의 실제 일수 사용 (가장 정확함)
                elif any(keyword in message.lower() for keyword in ['부터', '21일부터', '22일부터', '23일부터', '24일부터', '25일부터']):
                    print(f"🔍 사용자가 '부터' 패턴으로 요청 - 식단 데이터의 실제 일수({actual_days_count}) 사용")
                    duration_days = actual_days_count
                elif not duration_days or duration_days < actual_days_count:
                    print(f"✅ duration_days 보정: {duration_days} → {actual_days_count}")
                    duration_days = actual_days_count
                else:
                    print(f"🔍 DEBUG: duration_days 유지: {duration_days}일")
            
            print(f"🔍 DEBUG: 최종 duration_days = {duration_days}")
            # --- [수정된 로직 끝] ---

            # 사전 차단 로직 제거 - 부분 저장 로직으로 대체됨
            print("✅ 사전 차단 로직 제거됨 - 부분 저장 로직 사용")

            # 캘린더 저장 데이터 준비
            save_data = self.calendar_utils.prepare_calendar_save_data(
                parsed_date, meal_plan_data, duration_days
            )

            # 실제 Supabase에 식단 데이터 저장
            save_result = await self._save_to_supabase(state, save_data)

            # 결과 반환
            if save_result["success"]:
                success_message = f"✅ 성공적으로 캘린더에 저장되었습니다! {parsed_date.date.strftime('%Y년 %m월 %d일')}부터 시작합니다! 📅✨"
                
                return {
                    "success": True,
                    "message": success_message,
                    "save_data": save_data
                }
            else:
                return {
                    "success": False,
                    "message": save_result["message"],
                    "save_data": save_data
                }

        except Exception as e:
            print(f"❌ 캘린더 저장 처리 오류: {e}")
            import traceback
            print(f"❌ 상세 오류: {traceback.format_exc()}")
            return {
                "success": False,
                "message": "죄송합니다. 캘린더 저장 처리 중 오류가 발생했습니다. 다시 시도해주세요."
            }

    async def _find_meal_plan_from_db(self, thread_id: str) -> Optional[Dict]:
        """데이터베이스에서 식단 데이터 찾기"""

        try:
            print(f"🔍 데이터베이스 조회 시도: thread_id={thread_id}")
            db_history = supabase.table("chat").select("message").eq("thread_id", thread_id).order("created_at", desc=True).limit(20).execute()

            db_messages = [msg["message"] for msg in db_history.data if msg.get("message")]
            print(f"🔍 데이터베이스에서 {len(db_messages)}개 메시지 조회")

            if db_messages:
                meal_plan_data = self.calendar_utils.find_recent_meal_plan(db_messages)
                if meal_plan_data:
                    print(f"🔍 데이터베이스에서 식단 발견: {meal_plan_data}")
                    return meal_plan_data

        except Exception as db_error:
            print(f"⚠️ 데이터베이스 조회 실패: {db_error}")

        return None

    def _extract_duration_from_chat_history(self, chat_history: List[str], current_message: str) -> int:
        """
        직전 대화에서 일수 정보를 추출
        예: "3일치 식단표 만들어줘" → "21일부터 캘린더에 넣어줘" → 3일치
        """
        print(f"🔍 DEBUG: 직전 대화에서 일수 정보 추출 시작")
        
        # 현재 메시지가 "부터" 패턴인지 확인
        if not any(keyword in current_message.lower() for keyword in ['부터', '21일부터', '22일부터', '23일부터', '24일부터', '25일부터']):
            print(f"🔍 DEBUG: '부터' 패턴이 아님 - 직전 대화 검색 건너뜀")
            return 0
        
        # 직전 대화에서 일수 정보 찾기
        korean_numbers = {
            '하루': 1, '한날': 1, '하루치': 1, '1일치': 1,
            '이틀': 2, '이틀치': 2, '2일치': 2,
            '사흘': 3, '사흘치': 3, '3일치': 3,
            '나흘': 4, '나흘치': 4, '4일치': 4,
            '닷새': 5, '닷새치': 5, '5일치': 5,
            '엿새': 6, '엿새치': 6, '6일치': 6,
            '이레': 7, '이레치': 7, '일주일': 7, '일주일치': 7, '7일치': 7,
            '여드레': 8, '여드레치': 8, '8일치': 8,
            '아흐레': 9, '아흐레치': 9, '9일치': 9,
            '열흘': 10, '열흘치': 10, '10일치': 10
        }
        
        # 최근 5개 메시지에서 일수 정보 찾기
        for i, msg in enumerate(reversed(chat_history[-5:])):
            print(f"🔍 DEBUG: 이전 메시지 {i+1} 확인: '{msg.strip()[:80]}...'")
            
            # 한글 숫자 먼저 체크
            for kor_key, kor_val in korean_numbers.items():
                if f"{kor_key}치" in msg or f"{kor_key} 식단표" in msg:
                    print(f"🔍 DEBUG: 직전 대화에서 한글 {kor_val}일치 감지!")
                    return kor_val
            
            # 아라비안 숫자 패턴들
            import re
            patterns = [
                (r'(\d+)일치', '일치'),
                (r'(\d+)주치', '주치'),
                (r'(\d+)일 식단표', '일'),
                (r'(\d+)주 식단표', '주')
            ]
            
            for pattern, suffix in patterns:
                match = re.search(pattern, msg)
                if match:
                    days = int(match.group(1))
                    if suffix == '주':
                        days = days * 7
                    print(f"🔍 DEBUG: 직전 대화에서 {days}일치 감지!")
                    return days
        
        print(f"🔍 DEBUG: 직전 대화에서 일수 정보를 찾지 못함")
        return 0

    async def _save_to_supabase(self, state: Dict[str, Any], save_data: Dict[str, Any]) -> Dict[str, Any]:
        """Supabase에 실제 저장 수행 (기존 데이터 자동 덮어쓰기)"""

        try:
            # user_id 가져오기
            user_id = self.calendar_utils.get_user_id_from_state(state)

            if not user_id:
                print(f"⚠️ 사용자 정보를 찾을 수 없어 실제 저장을 건너뜁니다")
                return {
                    "success": False,
                    "message": f"데이터를 준비했습니다만, 사용자 정보가 필요합니다. 프론트엔드에서 완료될 예정입니다."
                }

            # 날짜 파싱
            start_date = datetime.fromisoformat(save_data["start_date"])
            duration_days = save_data["duration_days"]
            days_data = save_data["days_data"]

            print(f"🔍 DEBUG: 저장할 기간: {start_date.date()}부터 {duration_days}일, 데이터 개수: {len(days_data) if days_data else 0}")

            # meal_log 데이터 생성
            meal_logs_to_create = self.calendar_utils.create_meal_logs_data(
                days_data, user_id, start_date.date()
            )
            
            print(f"🔍 DEBUG: 생성된 meal_logs 개수: {len(meal_logs_to_create)}")

            # 사전 차단 로직 제거 - 부분 저장 로직으로 대체됨
            print("✅ 최종 하드 차단 로직 제거됨 - 부분 저장 로직 사용")

            # Supabase 저장 활성화 (차단 로직이 먼저 실행됨)
            print(f"🔍 DEBUG: Supabase 저장 시도 - meal_logs_to_create 개수: {len(meal_logs_to_create)}")
            
            # 기존 데이터 삭제 후 새 데이터 저장 (완전한 덮어쓰기)
            if meal_logs_to_create:
                print(f"🔍 DEBUG: 기존 데이터 삭제 후 {len(meal_logs_to_create)}개 새 데이터 저장 시도")
                
                # 1. 기존 데이터 삭제 (저장할 기간의 모든 데이터)
                end_date = start_date + timedelta(days=duration_days - 1)
                print(f"🔍 DEBUG: 삭제할 기간: {start_date.date()} ~ {end_date.date()}")
                
                delete_result = supabase.table('meal_log').delete().eq(
                    'user_id', user_id
                ).gte(
                    'date', start_date.date().isoformat()
                ).lte(
                    'date', end_date.date().isoformat()
                ).execute()
                
                print(f"🔍 DEBUG: 기존 데이터 삭제 완료: {len(delete_result.data) if delete_result.data else 0}개")
                
                # 2. 새 데이터 저장
                result = supabase.table('meal_log').insert(
                    meal_logs_to_create
                ).execute()
                print(f"🔍 DEBUG: Supabase 저장 결과: {result}")

                if result.data:
                    # 저장 완료 확인을 위한 짧은 지연
                    import asyncio
                    await asyncio.sleep(0.5)  # 500ms 지연
                    return {
                        "success": True,
                        "message": "캘린더에 성공적으로 저장되었습니다!"
                    }
                else:
                    return {
                        "success": False,
                        "message": "저장 중 오류가 발생했습니다. 다시 시도해주세요."
                    }
            else:
                return {
                    "success": False,
                    "message": "저장할 식단 데이터를 찾을 수 없습니다."
                }

        except Exception as save_error:
            print(f"❌ Supabase 저장 중 오류 발생: {save_error}")
            import traceback
            print(f"❌ 상세 저장 오류: {traceback.format_exc()}")
            return {
                "success": False,
                "message": "식단 데이터를 준비했습니다만 저장 중 오류가 발생했습니다. 프론트엔드에서 완료될 예정입니다."
            }

    async def save_restaurant_to_calendar(
        self,
        state: Dict[str, Any],
        restaurant_data: Dict[str, Any],
        target_date: datetime
    ) -> Dict[str, Any]:
        """식당 정보를 캘린더에 저장 (추후 확장용)"""

        try:
            # user_id 가져오기
            user_id = self.calendar_utils.get_user_id_from_state(state)

            if not user_id:
                return {
                    "success": False,
                    "message": "사용자 정보가 필요합니다."
                }

            # 식당 데이터를 meal_log 형태로 변환 (예시)
            restaurant_log = {
                "user_id": str(user_id),
                "date": target_date.date().isoformat(),
                "meal_type": "lunch",  # 기본값, 추후 사용자 선택 가능
                "eaten": False,
                "note": f"🏪 {restaurant_data.get('name', '')} - {restaurant_data.get('address', '')}",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Supabase에 저장
            result = supabase.table('meal_log').insert([restaurant_log]).execute()

            if result.data:
                return {
                    "success": True,
                    "message": f"식당 '{restaurant_data.get('name', '')}'가 캘린더에 저장되었습니다!"
                }
            else:
                return {
                    "success": False,
                    "message": "식당 저장 중 오류가 발생했습니다."
                }

        except Exception as e:
            print(f"❌ 식당 캘린더 저장 오류: {e}")
            return {
                "success": False,
                "message": "식당 캘린더 저장 중 오류가 발생했습니다."
            }
