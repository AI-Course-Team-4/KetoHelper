"""
가드레일 메트릭 API
"""

from fastapi import APIRouter, Query
from typing import Optional
from app.core.guard_service import guard_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/guard-metrics")
async def get_guard_metrics(
    from_: Optional[str] = Query(None, alias="from", description="시작 날짜"),
    to: Optional[str] = Query(None, description="종료 날짜"),
    route: Optional[str] = Query(None, description="특정 경로 필터")
):
    """가드레일 메트릭 조회"""
    metrics = guard_service.get_metrics()
    
    # 날짜/경로 필터링은 추후 구현
    # 현재는 전체 메트릭 반환
    
    return {
        "success": True,
        "data": metrics,
        "filters": {
            "from": from_,
            "to": to,
            "route": route
        }
    }


@router.get("/guard-dashboard")
async def get_guard_dashboard():
    """가드레일 대시보드 데이터"""
    metrics = guard_service.get_metrics()
    
    return {
        "summary": {
            "total_requests": metrics["summary"]["total_requests"],
            "success_rate": round(metrics["summary"]["success_rate"] * 100, 2),
            "avg_response_time_ms": metrics["summary"]["avg_response_time_ms"]
        },
        "error_breakdown": metrics["error_breakdown"],
        "auto_corrections": metrics["auto_corrections"],
        "performance": metrics["performance"],
        "config": metrics["config"]
    }
