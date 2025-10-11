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
                day_number = 0
                
                for line in lines:
                    # 이모지 제거 (🌅, 🌞, 🌙, 🍎 등)
                    clean_line = re.sub(r'[^\w\s:,.()/-]', '', line).strip()
                    
                    # 새로운 일차 시작
                    if '일차:' in line:
                        # 이전 day 저장
                        if current_day:
                            days.append(current_day)
                        current_day = {}
                        day_number += 1
                    
                    # 식사 시간별 파싱 (URL 정보 보존 및 제목 정리)
                    if '아침:' in clean_line:
                        title = clean_line.split('아침:')[1].strip() if ':' in clean_line else line.split('아침:')[1].strip()
                        # URL 정보 추출 및 제목 정리
                        url = CalendarUtils._extract_url_from_markdown(title)
                        clean_title = CalendarUtils._clean_title_from_urls(title)
                        current_day['breakfast'] = {'title': clean_title, 'url': url}
                    elif '점심:' in clean_line:
                        title = clean_line.split('점심:')[1].strip() if ':' in clean_line else line.split('점심:')[1].strip()
                        url = CalendarUtils._extract_url_from_markdown(title)
                        clean_title = CalendarUtils._clean_title_from_urls(title)
                        current_day['lunch'] = {'title': clean_title, 'url': url}
                    elif '저녁:' in clean_line:
                        title = clean_line.split('저녁:')[1].strip() if ':' in clean_line else line.split('저녁:')[1].strip()
                        url = CalendarUtils._extract_url_from_markdown(title)
                        clean_title = CalendarUtils._clean_title_from_urls(title)
                        current_day['dinner'] = {'title': clean_title, 'url': url}
                    elif '간식:' in clean_line:
                        title = clean_line.split('간식:')[1].strip() if ':' in clean_line else line.split('간식:')[1].strip()
                        url = CalendarUtils._extract_url_from_markdown(title)
                        clean_title = CalendarUtils._clean_title_from_urls(title)
                        current_day['snack'] = {'title': clean_title, 'url': url}

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
            
            # 모든 날짜의 데이터를 보장 (duration_days만큼)
            while len(days_data) < duration_days:
                days_data.append({})
                print(f"🔍 DEBUG: {len(days_data)}일차 빈 데이터 추가")
            
            # 금지 문구가 있는 슬롯은 제외하되, 날짜 자체는 유지
            banned_substrings = ['추천 식단이 없', '추천 불가']
            for day_idx, day in enumerate(days_data):
                if not isinstance(day, dict):
                    days_data[day_idx] = {}
                    continue
                for slot in ['breakfast', 'lunch', 'dinner', 'snack']:
                    item = day.get(slot)
                    title = ""
                    item_type = None
                    if isinstance(item, dict):
                        title = str(item.get('title', '')).strip()
                        item_type = item.get('type')
                    elif isinstance(item, str):
                        title = item.strip()
                    if (not item) or (not title) or (item_type == 'no_result') or any(bs in title for bs in banned_substrings):
                        day[slot] = None
        else:
            # Fallback 생성 금지: days_data를 비워 두어 저장이 진행되지 않게 함
            print(f"🔍 DEBUG: 유효한 식단 데이터가 없어 days_data를 생성하지 않습니다 (fallback 금지)")
            days_data = []
        
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
            print(f"🔍 DEBUG: {i+1}일차 데이터 처리 시작 - {date_string}")
            print(f"🔍 DEBUG: {i+1}일차 day_data: {day_data}")

            # 각 식사 시간대별로 meal_log 생성
            meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
            for slot in meal_types:
                print(f"🔍 DEBUG: {i+1}일차 {slot} 슬롯 처리 시작")
                
                if slot in day_data and day_data[slot] is not None:
                    meal_item = day_data[slot]
                    meal_title = ""
                    
                    print(f"🔍 DEBUG: {i+1}일차 {slot} meal_item: {meal_item} (타입: {type(meal_item)})")

                    if isinstance(meal_item, str):
                        meal_title = meal_item
                        print(f"🔍 DEBUG: {i+1}일차 {slot} 문자열 처리: '{meal_title}'")
                    elif isinstance(meal_item, dict) and meal_item.get('title'):
                        meal_title = meal_item['title']
                        print(f"🔍 DEBUG: {i+1}일차 {slot} 딕셔너리 처리: '{meal_title}'")
                    else:
                        meal_title = str(meal_item) if meal_item else ""
                        print(f"🔍 DEBUG: {i+1}일차 {slot} 기타 처리: '{meal_title}'")

                    # 더 강력한 금지 문구 검사
                    banned_substrings = [
                        '추천 식단이 없', '추천 불가', '추천 식단이 없습니다', 
                        '추천 식단이 없습니다😢', '추천 식단이 없습니다.',
                        'no_result', 'None', 'null', 'undefined'
                    ]
                    
                    # 이모지 제거 후 검사
                    import re
                    clean_title = re.sub(r'[^\w\s:,.()/-]', '', meal_title)
                    
                    has_banned = any(bs in meal_title for bs in banned_substrings) or any(bs in clean_title for bs in banned_substrings)
                    
                    print(f"🔍 DEBUG: {i+1}일차 {slot} 검사 결과:")
                    print(f"  - 원본: '{meal_title}'")
                    print(f"  - 정리: '{clean_title}'")
                    print(f"  - 금지문구 포함: {has_banned}")
                    print(f"  - 빈 문자열: {not meal_title or not meal_title.strip()}")
                    
                    if meal_title and meal_title.strip() and not has_banned:
                        # URL 정보 추출 (meal_item이 딕셔너리인 경우)
                        meal_url = None
                        if isinstance(meal_item, dict) and meal_item.get('url'):
                            meal_url = meal_item['url']
                            print(f"🔍 DEBUG: {i+1}일차 {slot} URL 발견: {meal_url}")
                        
                        # 제목에서 URL 제거하여 깔끔하게 정리
                        clean_meal_title = CalendarUtils._clean_title_from_urls(meal_title.strip())
                        
                        meal_log = {
                            "user_id": str(user_id),
                            "date": date_string,
                            "meal_type": slot,
                            "eaten": False,
                            "note": clean_meal_title,  # 정리된 제목만 저장
                            "url": meal_url,  # URL 정보는 별도 컬럼에 저장
                            "created_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                        meal_logs_to_create.append(meal_log)
                        print(f"✅ DEBUG: {i+1}일차 {slot} meal_log 추가: {meal_log}")
                    else:
                        print(f"❌ DEBUG: {i+1}일차 {slot} 제외됨 - 금지문구 또는 빈값")
                else:
                    print(f"🔍 DEBUG: {i+1}일차 {slot} 슬롯 없음 또는 빈값")

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

    @staticmethod
    def _extract_url_from_markdown(text: str) -> Optional[str]:
        """마크다운 링크에서 URL 추출"""
        import re
        
        # 마크다운 링크 패턴: [텍스트](URL)
        markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        match = re.search(markdown_pattern, text)
        
        if match:
            url = match.group(2)
            print(f"🔍 마크다운에서 URL 추출: {url}")
            return url
        
        # 일반 URL 패턴도 체크 (http/https로 시작하는 링크)
        url_pattern = r'https?://[^\s]+'
        url_match = re.search(url_pattern, text)
        
        if url_match:
            url = url_match.group(0)
            print(f"🔍 일반 URL에서 추출: {url}")
            return url
        
        return None

    @staticmethod
    def _clean_title_from_urls(text: str) -> str:
        """메뉴명에서 URL 제거하여 깔끔한 제목만 반환"""
        import re
        
        # 마크다운 링크 패턴 제거: [텍스트](URL) -> 텍스트
        markdown_pattern = r'\[([^\]]+)\]\([^)]+\)'
        text = re.sub(markdown_pattern, r'\1', text)
        
        # 일반 URL 패턴 제거: (https://...)
        url_pattern = r'\s*\(https?://[^\s)]+\)'
        text = re.sub(url_pattern, '', text)
        
        # 일반 URL 패턴 제거: https://... (괄호 없이)
        url_pattern2 = r'\s*https?://[^\s]+'
        text = re.sub(url_pattern2, '', text)
        
        # 🔗 아이콘 제거
        text = re.sub(r'\s*🔗\s*', '', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        print(f"🔍 제목 정리: '{text}'")
        return text