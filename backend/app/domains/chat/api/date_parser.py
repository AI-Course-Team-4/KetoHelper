from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# date_parser.py import를 위한 path 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tools', 'shared'))
from date_parser import date_parser, ParsedDateInfo

router = APIRouter()


class DateParseRequest(BaseModel):
    message: str
    context: Optional[str] = None  # 추가 컨텍스트 (향후 LLM 연동 시 사용)


class DateParseResponse(BaseModel):
    success: bool
    parsed_date: Optional[dict] = None
    error_message: Optional[str] = None


@router.post("/parse-date", response_model=DateParseResponse)
async def parse_date_from_message(request: DateParseRequest):
    """
    채팅 메시지에서 날짜를 파싱하여 반환
    """
    try:
        # 메시지에서 날짜 추출
        parsed_date = date_parser.extract_date_from_message(request.message)

        if parsed_date is None:
            return DateParseResponse(
                success=False,
                error_message="날짜 표현을 찾을 수 없습니다."
            )

        # ParsedDateInfo를 dict로 변환
        date_dict = {
            "date": parsed_date.date.isoformat(),
            "description": parsed_date.description,
            "is_relative": parsed_date.is_relative,
            "confidence": parsed_date.confidence,
            "method": parsed_date.method,
            "iso_string": date_parser.to_iso_string(parsed_date),
            "display_string": date_parser.to_display_string(parsed_date)
        }

        return DateParseResponse(
            success=True,
            parsed_date=date_dict
        )

    except Exception as e:
        return DateParseResponse(
            success=False,
            error_message=f"날짜 파싱 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/parse-natural-date", response_model=DateParseResponse)
async def parse_natural_date(request: DateParseRequest):
    """
    자연어 날짜 표현을 직접 파싱
    """
    try:
        # 자연어 날짜 파싱
        parsed_date = date_parser.parse_natural_date(request.message)

        if parsed_date is None:
            return DateParseResponse(
                success=False,
                error_message="날짜 표현을 파싱할 수 없습니다."
            )

        # ParsedDateInfo를 dict로 변환
        date_dict = {
            "date": parsed_date.date.isoformat(),
            "description": parsed_date.description,
            "is_relative": parsed_date.is_relative,
            "confidence": parsed_date.confidence,
            "method": parsed_date.method,
            "iso_string": date_parser.to_iso_string(parsed_date),
            "display_string": date_parser.to_display_string(parsed_date)
        }

        return DateParseResponse(
            success=True,
            parsed_date=date_dict
        )

    except Exception as e:
        return DateParseResponse(
            success=False,
            error_message=f"날짜 파싱 중 오류가 발생했습니다: {str(e)}"
        )