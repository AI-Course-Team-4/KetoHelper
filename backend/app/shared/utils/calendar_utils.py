"""
캘린더 관련 공용 유틸리티 함수들
- 식단 데이터 파싱 및 처리
- 캘린더 저장 요청 감지
- 공통 데이터 변환 로직
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class CalendarUtils:
    """캘린더 관련 공용 유틸리티"""

    @staticmethod
    def find_recent_meal_plan(chat_history: List[str]) -> Optional[Dict]:
        """대화 히스토리에서 최근 식단 데이터 찾기"""

        # 역순으로 탐색 (최근 대화부터)
        for msg in reversed(chat_history[-10:]):  # 최근 10개 메시지만 확인
            # 식단표 패턴 찾기
            if "일차:" in msg or "아침:" in msg or "점심:" in msg or "저녁:" in msg:
                # 간단한 파싱 (실제로는 더 정교하게 구현 필요)
                days = []
                lines = msg.split('\n')

                current_day = {}
                for line in lines:
                    if '아침:' in line:
                        current_day['breakfast'] = {'title': line.split('아침:')[1].strip()}
                    elif '점심:' in line:
                        current_day['lunch'] = {'title': line.split('점심:')[1].strip()}
                    elif '저녁:' in line:
                        current_day['dinner'] = {'title': line.split('저녁:')[1].strip()}
                    elif '간식:' in line:
                        current_day['snack'] = {'title': line.split('간식:')[1].strip()}

                    # 하루 단위로 저장
                    if '일차:' in line and current_day:
                        days.append(current_day)
                        current_day = {}

                # 마지막 날 추가
                if current_day:
                    days.append(current_day)

                if days:
                    # duration_days를 더 정확하게 설정
                    found_duration = len(days)

                    # 메시지에서 숫자(일차) 찾기로 일수 추출
                    try:
                        from app.tools.shared.date_parser import DateParser
                        date_parser = DateParser()
                        extracted_days = date_parser._extract_duration_days(msg)
                        if extracted_days and extracted_days > 0:
                            found_duration = extracted_days
                            print(f"🔍 메시지에서 추출한 일수: {found_duration}")
                    except Exception as e:
                        print(f"⚠️ 일수 추출 중 오류: {e}")

                    return {
                        'days': days,
                        'duration_days': found_duration
                    }

        return None

    @staticmethod
    def is_calendar_save_request(message: str) -> bool:
        """캘린더 저장 요청인지 감지"""
        save_keywords = ['저장', '추가', '계획', '등록', '넣어', '캘린더', '일정']
        date_keywords = ['다음주', '내일', '오늘', '모레', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']

        has_save_keyword = any(keyword in message for keyword in save_keywords)
        has_date_keyword = any(keyword in message for keyword in date_keywords)

        return has_save_keyword and has_date_keyword

    @staticmethod
    def prepare_calendar_save_data(
        parsed_date: Any,
        meal_plan_data: Optional[Dict],
        duration_days: int
    ) -> Dict[str, Any]:
        """캘린더 저장을 위한 데이터 준비"""

        # 일별 식단 데이터를 직접 포함한 save_data 생성
        days_data = []

        if meal_plan_data and 'days' in meal_plan_data:
            days_data = meal_plan_data['days']
            print(f"🔍 DEBUG: 식단 데이터에서 {len(days_data)}개 일 찾음")
        else:
            # 기본 식단으로 fallback
            print(f"🔍 DEBUG: 식단 데이터가 없어서 기본 값으로 {duration_days}일치 생성")
            for i in range(duration_days):
                days_data.append({
                    'breakfast': {'title': f'키토 아침 메뉴 {i+1}일차'},
                    'lunch': {'title': f'키토 점심 메뉴 {i+1}일차'},
                    'dinner': {'title': f'키토 저녁 메뉴 {i+1}일차'},
                    'snack': {'title': f'키토 간식 {i+1}일차'}
                })
        
        print(f"🔍 DEBUG: 최종 days_data 길이: {len(days_data)}")

        return {
            "action": "save_to_calendar",
            "start_date": parsed_date.date.isoformat(),
            "duration_days": duration_days,
            "meal_plan_data": meal_plan_data,
            "days_data": days_data,  # 직접 프론트엔드에서 사용할 수 있는 일별 데이터 추가
            "message": f"{duration_days}일치 식단표를 {parsed_date.date.strftime('%Y년 %m월 %d일')}부터 캘린더에 저장합니다."
        }

    @staticmethod
    def extract_duration_from_meal_plan(meal_plan_data: Dict, chat_history: List[str]) -> int:
        """식단 데이터와 대화 히스토리에서 정확한 일수 추출 (다음주+요일 조합 보호)"""

        duration_days = None
        
        # 현재 날짜 파서에서 사용한 메시지 가져오기 (가장 최근 메시지 확인)
        current_message = ""
        if chat_history:
            current_message = chat_history[-1].lower()
        
        print(f"🔍 calendar_utils 부조화 추출: current_message 검사='{current_message[:50]}...'")

        # 1. meal_plan_data에서 duration_days 먼저 확인
        if 'duration_days' in meal_plan_data:
            duration_days = meal_plan_data['duration_days']
            print(f"🔍 DEBUG: meal_plan_data에서 duration_days 추출: {duration_days}")

        # 2. 특정 요일명시 체크 후 수정하지 않음 
        if any(day in current_message for day in ['다음주']):
            if any(weekday in current_message for weekday in ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']):
                print(f"🔍 다음주+요일 조합 감지 - duration_days 보호로 1일 강제 유지")
                return 1

        # 3. days 배열 길이로 확인
        if duration_days is None and 'days' in meal_plan_data:
            duration_days = len(meal_plan_data['days'])
            print(f"🔍 DEBUG: days 배열 길이로 duration_days 추출: {duration_days}")

        # 4. 대화 히스토리에서 더 정확한 일수 찾기  
        if duration_days is None or duration_days == 1:
            try:
                from app.tools.shared.date_parser import DateParser
                date_parser = DateParser()

                # DateParser의 _extract_duration_days로 다시 시도
                for history_msg in reversed(chat_history[-5:]):
                    extracted_days = date_parser._extract_duration_days(history_msg)
                    if extracted_days and extracted_days > 1:
                        duration_days = extracted_days
                        print(f"🔍 DEBUG: 채팅 히스토리에서 일수 재추출: {duration_days}")
                        break
            except Exception as e:
                print(f"⚠️ DateParser 사용 중 오류: {e}")

        # 최종 기본값 (1일이 아니면)
        if duration_days is None:
            duration_days = 3  # 기본 3일
            print(f"🔍 DEBUG: 기본값 사용: {duration_days}일")

        return duration_days

    @staticmethod
    def create_meal_logs_data(days_data: List[Dict], user_id: str, start_date: datetime) -> List[Dict]:
        """meal_log 테이블에 저장할 데이터 생성"""

        meal_logs_to_create = []
        current_date = start_date

        for i, day_data in enumerate(days_data):
            date_string = current_date.isoformat()

            # 각 식사 시간대별로 meal_log 생성
            meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
            for slot in meal_types:
                if slot in day_data and day_data[slot]:
                    meal_item = day_data[slot]
                    meal_title = ""

                    if isinstance(meal_item, str):
                        meal_title = meal_item
                    elif isinstance(meal_item, dict) and meal_item.get('title'):
                        meal_title = meal_item['title']
                    else:
                        meal_title = str(meal_item) if meal_item else ""

                    if meal_title and meal_title.strip():
                        meal_log = {
                            "user_id": str(user_id),
                            "date": date_string,
                            "meal_type": slot,
                            "eaten": False,
                            "note": meal_title.strip(),
                            "created_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                        meal_logs_to_create.append(meal_log)
                        print(f"🔍 DEBUG: meal_log 추가: {meal_log}")

            current_date += timedelta(days=1)

        return meal_logs_to_create

    @staticmethod
    def get_user_id_from_state(state: Dict[str, Any]) -> Optional[str]:
        """state에서 다양한 방법으로 user_id 추출"""

        user_id = None

        # 1. profile에서 확인
        if state.get("profile") and state["profile"].get("user_id"):
            user_id = state["profile"]["user_id"]
            print(f"🔍 DEBUG: user_id from profile: {user_id}")

        # 2. state에서 직접 user_id 확인
        if not user_id and state.get("user_id"):
            user_id = state["user_id"]
            print(f"🔍 DEBUG: user_id from state: {user_id}")

        # 3. thread_id로 데이터베이스에서 조회
        if not user_id and state.get("thread_id"):
            try:
                from app.core.database import supabase
                thread_response = supabase.table("chat_thread").select("user_id").eq("id", state["thread_id"]).execute()
                if thread_response.data:
                    user_id = thread_response.data[0].get("user_id")
                    print(f"🔍 DEBUG: user_id from thread: {user_id}")
            except Exception as thread_error:
                print(f"⚠️ thread에서 user_id 조회 실패: {thread_error}")

        return user_id