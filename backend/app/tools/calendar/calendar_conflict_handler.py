"""
캘린더 데이터 충돌 처리 도구
- 기존 식단 데이터가 있을 때 처리 방식 결정
- 사용자 선택에 따른 다양한 처리 옵션 제공
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from app.core.database import supabase


class ConflictAction(Enum):
    """충돌 처리 방식"""
    REPLACE = "replace"  # 기존 데이터 교체
    MERGE = "merge"      # 기존 데이터와 병합
    APPEND = "append"    # 기존 데이터 뒤에 추가
    CANCEL = "cancel"    # 저장 취소


class CalendarConflictHandler:
    """캘린더 데이터 충돌 처리기"""

    async def check_existing_data(
        self,
        user_id: str,
        start_date: datetime,
        duration_days: int,
        exclude_recent_minutes: int = 0
    ) -> Dict[str, Any]:
        """기존 데이터 존재 여부 확인"""

        try:
            end_date = start_date + timedelta(days=duration_days - 1)
            
            # 💡 수정 1: Supabase와 일관성을 위해 UTC 시간 사용
            current_time = datetime.utcnow()

            # 디버깅을 위한 로그 추가
            print(f"🔍 충돌 체크 시작:")
            print(f"  - user_id: {user_id}")
            print(f"  - start_date: {start_date.date().isoformat()}")
            print(f"  - end_date: {end_date.date().isoformat()}")
            print(f"  - duration_days: {duration_days}")
            print(f"  - exclude_recent_minutes: {exclude_recent_minutes}")
            print(f"  - 현재 시간: {current_time.isoformat()}")

            # 해당 기간의 기존 데이터 조회 - 모든 데이터 조사
            query = supabase.table('meal_log').select("*")\
                .eq('user_id', str(user_id))\
                .gte('date', start_date.date().isoformat())\
                .lte('date', end_date.date().isoformat())

            print(f"🔍 전체 기존 데이터를 조회하여 충돌 확인")

            # 이제 특정 임계치만 해당 - 매우 짧은 시간 (30초) 내에 저장된 동일한 내용 데이터만 필터링
            if exclude_recent_minutes > 0:
                # 동시 저장 방지를 위한 아주 짧은 제외 시간 (30초)
                cutoff_time = current_time - timedelta(seconds=30)
                
                # 💡 수정 2: Supabase의 UTC 저장 방식과 일치하도록 명시적으로 '+00:00' 추가
                cutoff_time_str = cutoff_time.isoformat() + "+00:00"
                
                print(f"🔍 동시 저장 방지를 위해 최근 30초 이내 데이터만 제외 (cutoff: {cutoff_time_str})")
                query = query.lt('created_at', cutoff_time_str)

            existing_data = query.execute()

            print(f"🔍 DB 조회 결과: {len(existing_data.data) if existing_data.data else 0}개 레코드 발견")
            
            # 실제 데이터가 있는지 더 엄격하게 확인 
            valid_data = []
            if existing_data.data is not None and len(existing_data.data) > 0:
                # 데이터 세부 검증: 실제 내용이 있는 필드가 있는지 확인
                for item in existing_data.data:
                    # None 체크 및 필수 필드 존재 및 비어있지 않은지 확인
                    if (item and 
                        item.get('date') and 
                        item.get('meal_type') and 
                        item.get('note') and 
                        item.get('note').strip()):  # note 필드가 빈 문자열이 아닌지 확인
                        valid_data.append(item)
                        print(f"🔍 유효한 항목 검증됨: {item.get('date')} - {item.get('meal_type')}")
                    else:
                        print(f"🔍 무효한 데이터 건너뜀: {item}")

            # 현재 저장하려는 줄거가 이미 있는지 확인하려면 ID나 시간 체크 등이 필요할 수 있음
            print(f"🔍 검증된 유효 데이터 개수: {len(valid_data)}")

            if len(valid_data) > 0:
                print(f"🔍 {len(valid_data)}개의 유효한 데이터로 실제 충돌 중")
                # 날짜별로 그룹화
                dates_with_data = {}
                for item in valid_data:
                    date = item['date']
                    if date not in dates_with_data:
                        dates_with_data[date] = []
                    dates_with_data[date].append({
                        'meal_type': item.get('meal_type', ''),
                        'note': item.get('note', ''),
                        'eaten': item.get('eaten', False)
                    })

                return {
                    "has_conflict": True,
                    "conflict_dates": list(dates_with_data.keys()),
                    "conflict_data": dates_with_data,
                    "total_conflicts": len(valid_data)
                }

            print(f"🔍 유효한 데이터 없음 ({len(valid_data)}개) - 충돌 아님")

            print(f"🔍 충돌 없음 - 빈 테이블이거나 해당 기간에 데이터 없음")
            return {
                "has_conflict": False,
                "conflict_dates": [],
                "conflict_data": {},
                "total_conflicts": 0
            }

        except Exception as e:
            print(f"❌ 기존 데이터 확인 중 오류: {e}")
            return {
                "has_conflict": False,
                "conflict_dates": [],
                "conflict_data": {},
                "total_conflicts": 0,
                "error": str(e)
            }

    def generate_conflict_message(
        self,
        conflict_info: Dict[str, Any],
        start_date: datetime,
        duration_days: int
    ) -> str:
        """충돌 상황에 대한 사용자 메시지 생성"""

        conflict_dates = conflict_info["conflict_dates"]
        total_conflicts = conflict_info["total_conflicts"]

        date_str = start_date.strftime('%Y년 %m월 %d일')
        end_date_str = (start_date + timedelta(days=duration_days - 1)).strftime('%Y년 %m월 %d일')

        message = f"""
🚨 **캘린더 충돌 감지!**

**저장하려는 기간**: {date_str} ~ {end_date_str} ({duration_days}일)
**기존 데이터**: {len(conflict_dates)}일의 식단이 이미 저장되어 있습니다 (총 {total_conflicts}개 항목)

**충돌되는 날짜들**:
{', '.join(conflict_dates)}

**어떻게 처리하시겠어요?**
1. **교체** - 기존 식단을 완전히 새 식단으로 교체
2. **병합** - 기존 식단과 새 식단을 합쳐서 저장
3. **추가** - 기존 식단은 그대로 두고 새 식단을 뒤에 추가
4. **취소** - 저장을 취소하고 기존 식단 유지

원하는 처리 방식을 말씀해주세요! (예: "교체해줘", "병합해줘")
        """.strip()

        return message

    async def handle_conflict(
        self,
        action: ConflictAction,
        user_id: str,
        start_date: datetime,
        duration_days: int,
        new_meal_logs: List[Dict[str, Any]],
        existing_conflict_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """충돌 처리 실행"""

        try:
            if action == ConflictAction.CANCEL:
                return {
                    "success": False,
                    "message": "저장이 취소되었습니다. 기존 식단이 그대로 유지됩니다.",
                    "action_taken": "cancelled"
                }

            elif action == ConflictAction.REPLACE:
                # 기존 방식: 삭제 후 새로 저장
                end_date = start_date + timedelta(days=duration_days - 1)
                delete_result = supabase.table('meal_log').delete()\
                    .eq('user_id', str(user_id))\
                    .gte('date', start_date.date().isoformat())\
                    .lte('date', end_date.date().isoformat()).execute()

                result = supabase.table('meal_log').insert(new_meal_logs).execute()

                if result.data:
                    return {
                        "success": True,
                        "message": f"✅ 기존 식단을 새 식단으로 교체했습니다! ({len(new_meal_logs)}개 항목)",
                        "action_taken": "replaced"
                    }

            elif action == ConflictAction.MERGE:
                # 병합: 같은 날짜+meal_type이 있으면 새것으로 교체, 없으면 추가
                conflict_data = existing_conflict_info["conflict_data"]

                # 기존 데이터 중 새 데이터와 중복되는 것만 삭제
                for new_log in new_meal_logs:
                    date = new_log["date"]
                    meal_type = new_log["meal_type"]

                    supabase.table('meal_log').delete()\
                        .eq('user_id', str(user_id))\
                        .eq('date', date)\
                        .eq('meal_type', meal_type).execute()

                # 새 데이터 저장
                result = supabase.table('meal_log').insert(new_meal_logs).execute()

                if result.data:
                    return {
                        "success": True,
                        "message": f"✅ 기존 식단과 새 식단을 병합했습니다! ({len(new_meal_logs)}개 항목 추가/수정)",
                        "action_taken": "merged"
                    }

            elif action == ConflictAction.APPEND:
                # 추가: 새 식단을 기존 식단 이후 날짜부터 저장
                last_date = max(existing_conflict_info["conflict_dates"])
                last_date_obj = datetime.fromisoformat(last_date)
                new_start_date = last_date_obj + timedelta(days=1)

                # 날짜를 다시 계산해서 저장
                adjusted_logs = []
                for i, log in enumerate(new_meal_logs):
                    adjusted_date = new_start_date + timedelta(days=i // 4)  # 4개 meal_type per day
                    adjusted_log = log.copy()
                    adjusted_log["date"] = adjusted_date.date().isoformat()
                    adjusted_logs.append(adjusted_log)

                result = supabase.table('meal_log').insert(adjusted_logs).execute()

                if result.data:
                    return {
                        "success": True,
                        "message": f"✅ 새 식단을 기존 식단 뒤에 추가했습니다! ({new_start_date.strftime('%Y년 %m월 %d일')}부터 시작)",
                        "action_taken": "appended"
                    }

            return {
                "success": False,
                "message": "알 수 없는 처리 방식입니다.",
                "action_taken": "unknown"
            }

        except Exception as e:
            print(f"❌ 충돌 처리 중 오류: {e}")
            return {
                "success": False,
                "message": f"처리 중 오류가 발생했습니다: {str(e)}",
                "action_taken": "error"
            }

    def parse_user_action(self, message: str) -> ConflictAction:
        """사용자 메시지에서 처리 방식 파악"""

        message_lower = message.lower()

        # 교체 키워드
        replace_keywords = ["교체", "바꿔", "덮어써", "새로", "replace", "overwrite"]
        if any(keyword in message_lower for keyword in replace_keywords):
            return ConflictAction.REPLACE

        # 병합 키워드
        merge_keywords = ["병합", "합쳐", "섞어", "merge", "combine"]
        if any(keyword in message_lower for keyword in merge_keywords):
            return ConflictAction.MERGE

        # 추가 키워드
        append_keywords = ["추가", "뒤에", "이어서", "append", "add"]
        if any(keyword in message_lower for keyword in append_keywords):
            return ConflictAction.APPEND

        # 취소 키워드
        cancel_keywords = ["취소", "안해", "그만", "cancel", "stop"]
        if any(keyword in message_lower for keyword in cancel_keywords):
            return ConflictAction.CANCEL

        # 기본값은 교체
        return ConflictAction.REPLACE