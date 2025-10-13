from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging

# 새 위치에서 tools/shared/date_parser 모듈 사용할 수 있도록 경로 수정
from ...tools.shared.date_parser import date_parser, ParsedDateInfo

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter()


class DateParseRequest(BaseModel):
    message: str
    context: Optional[str] = None  # 추가 컨텍스트 (향후 LLM 연동 시 사용)
    chat_history: Optional[List[str]] = None  # 이전 대화 맥락


class DateParseResponse(BaseModel):
    success: bool
    parsed_date: Optional[dict] = None
    error_message: Optional[str] = None


def _infer_days_from_history(history: Optional[List[str]]) -> Optional[int]:
    """이전 대화에서 기간(일수)을 추정한다.
    - '3일', '7일' 등의 패턴
    - '일주일' → 7
    가장 마지막에 등장한 값을 사용
    """
    try:
        if not history:
            return None
        import re
        days: Optional[int] = None
        for msg in reversed(history):
            if not isinstance(msg, str):
                continue
            # 일주일/한 주
            if '일주일' in msg or '한 주' in msg:
                days = 7
                break
            m = re.search(r"(\d+)\s*일", msg)
            if m:
                days = int(m.group(1))
                break
        return days
    except Exception:
        return None

@router.post("/parse-date", response_model=DateParseResponse)
async def parse_date_from_message(request: DateParseRequest):
    """
    채팅 메시지에서 날짜를 파싱하여 반환
    API 레이어: 요청 검증 및 응답 포맷팅만 담당
    """
    logger.info(f"날짜 파싱 요청 수신: message='{request.message}', context='{request.context}'")
    
    try:
        # 입력 검증
        if not request.message or not request.message.strip():
            logger.warning("빈 메시지로 날짜 파싱 요청")
            return DateParseResponse(
                success=False,
                error_message="날짜 파싱을 위한 메시지가 필요합니다."
            )

        # 날짜 파싱 로직은 date_parser 모듈에 위임 (대화 맥락 포함)
        parsed_date = date_parser.extract_date_from_message_with_context(
            request.message, 
            chat_history=request.chat_history or []
        )

        if parsed_date is None:
            logger.info(f"날짜 표현을 찾을 수 없음: '{request.message}'")
            return DateParseResponse(
                success=False,
                error_message="메시지에서 날짜 표현을 찾을 수 없습니다. '오늘', '내일', '이번주 토요일' 등의 표현을 사용해보세요."
            )

        # ParsedDateInfo를 dict로 변환 (API 응답 형식)
        date_dict = {
            "date": parsed_date.date.isoformat(),
            "description": parsed_date.description,
            "is_relative": parsed_date.is_relative,
            "confidence": parsed_date.confidence,
            "method": parsed_date.method,
            "duration_days": parsed_date.duration_days,
            "iso_string": date_parser.to_iso_string(parsed_date),
            "display_string": date_parser.to_display_string(parsed_date)
        }

        # 🔁 일수 보정: 파서가 못 찾았으면 최근 히스토리에서 추정
        if not date_dict["duration_days"]:
            inferred = _infer_days_from_history(request.chat_history)
            if inferred:
                date_dict["duration_days"] = inferred
                logger.info(f"일수 보정 적용: chat_history → {inferred}일")

        logger.info(f"날짜 파싱 성공: {parsed_date.description} -> {parsed_date.date.isoformat()}, 일수: {date_dict['duration_days']}")
        return DateParseResponse(
            success=True,
            parsed_date=date_dict
        )

    except ValueError as e:
        logger.error(f"날짜 형식 오류: {str(e)}")
        return DateParseResponse(
            success=False,
            error_message="날짜 형식이 올바르지 않습니다. 올바른 날짜 표현을 사용해주세요."
        )
    except Exception as e:
        logger.error(f"날짜 파싱 중 예상치 못한 오류: {str(e)}", exc_info=True)
        return DateParseResponse(
            success=False,
            error_message="서버에서 날짜 파싱 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


@router.post("/parse-natural-date", response_model=DateParseResponse)
async def parse_natural_date(request: DateParseRequest):
    """
    자연어 날짜 표현을 직접 파싱
    API 레이어: 요청 검증 및 응답 포맷팅만 담당
    """
    logger.info(f"자연어 날짜 파싱 요청 수신: message='{request.message}', context='{request.context}'")
    
    try:
        # 입력 검증
        if not request.message or not request.message.strip():
            logger.warning("빈 메시지로 자연어 날짜 파싱 요청")
            return DateParseResponse(
                success=False,
                error_message="자연어 날짜 파싱을 위한 메시지가 필요합니다."
            )

        # 자연어 날짜 파싱 로직은 date_parser 모듈에 위임 (대화 맥락 포함)
        parsed_date = date_parser.parse_natural_date_with_context(
            request.message,
            chat_history=request.chat_history or []
        )

        if parsed_date is None:
            logger.info(f"자연어 날짜 표현을 파싱할 수 없음: '{request.message}'")
            return DateParseResponse(
                success=False,
                error_message="자연어 날짜 표현을 파싱할 수 없습니다. '오늘', '내일', '다음주 화요일', '3일 후' 등의 표현을 사용해보세요."
            )

        # ParsedDateInfo를 dict로 변환 (API 응답 형식)
        date_dict = {
            "date": parsed_date.date.isoformat(),
            "description": parsed_date.description,
            "is_relative": parsed_date.is_relative,
            "confidence": parsed_date.confidence,
            "method": parsed_date.method,
            "duration_days": parsed_date.duration_days,
            "iso_string": date_parser.to_iso_string(parsed_date),
            "display_string": date_parser.to_display_string(parsed_date)
        }

        # 🔁 일수 보정: 파서가 못 찾았으면 최근 히스토리에서 추정
        if not date_dict["duration_days"]:
            inferred = _infer_days_from_history(request.chat_history)
            if inferred:
                date_dict["duration_days"] = inferred
                logger.info(f"일수 보정 적용: chat_history → {inferred}일")

        logger.info(f"자연어 날짜 파싱 성공: {parsed_date.description} -> {parsed_date.date.isoformat()} (신뢰도: {parsed_date.confidence:.2f}, 일수: {date_dict['duration_days']})")
        return DateParseResponse(
            success=True,
            parsed_date=date_dict
        )

    except ValueError as e:
        logger.error(f"자연어 날짜 형식 오류: {str(e)}")
        return DateParseResponse(
            success=False,
            error_message="자연어 날짜 형식이 올바르지 않습니다. 올바른 날짜 표현을 사용해주세요."
        )
    except Exception as e:
        logger.error(f"자연어 날짜 파싱 중 예상치 못한 오류: {str(e)}", exc_info=True)
        return DateParseResponse(
            success=False,
            error_message="서버에서 자연어 날짜 파싱 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )
