"""
가드레일 서비스
통합 검증 및 응답 생성 로직
"""

import os
import json
import time
from typing import Dict, Any, Tuple
from ..shared.models.guard_models import (
    GuardRequest, GuardResponse, GuardSuccessResponse, GuardErrorResponse,
    ErrorCode, StockMessages
)
from ..shared.guards.validators import validate_and_normalize


class GuardService:
    """가드레일 서비스 클래스"""
    
    def __init__(self):
        self.strict_mode = os.getenv("GUARD_STRICT", "true").lower() == "true"
        self.log_sample_rate = float(os.getenv("GUARD_LOG_SAMPLE", "1.0"))
        self.rules_version = os.getenv("GUARD_RULES_VERSION", "v2025-01-24")
        
        # 메트릭 수집용
        self.metrics = {
            "total_requests": 0,
            "success_count": 0,
            "error_counts": {code.value: 0 for code in ErrorCode},
            "auto_corrections": {},
            "response_times": []
        }
    
    def validate_request(self, request: GuardRequest) -> GuardResponse:
        """요청 검증 및 응답 생성"""
        start_time = time.time()
        
        try:
            # 메트릭 업데이트
            self.metrics["total_requests"] += 1
            
            # 검증 수행
            ok, normalized_slots, auto_corrections, error_code, missing_slots = validate_and_normalize(
                request.dict()
            )
            
            # 응답 시간 측정
            response_time = (time.time() - start_time) * 1000  # ms
            self.metrics["response_times"].append(response_time)
            
            if ok:
                # 성공 응답
                self.metrics["success_count"] += 1
                self._update_auto_corrections_metrics(auto_corrections)
                
                return GuardSuccessResponse(
                    ok=True,
                    normalized_slots=normalized_slots,
                    auto_corrections=auto_corrections
                )
            else:
                # 에러 응답
                self.metrics["error_counts"][error_code] += 1
                
                return GuardErrorResponse(
                    ok=False,
                    error_code=ErrorCode(error_code),
                    message=StockMessages.ERROR_MESSAGES.get(ErrorCode(error_code), "오류가 발생했습니다."),
                    required_slots=missing_slots if missing_slots else None,
                    auto_corrections=auto_corrections if auto_corrections else None,
                    hint=StockMessages.HINT_MESSAGES.get(ErrorCode(error_code))
                )
        
        except Exception as e:
            # 예외 발생 시
            response_time = (time.time() - start_time) * 1000
            self.metrics["response_times"].append(response_time)
            self.metrics["error_counts"][ErrorCode.SAFETY.value] += 1
            
            return GuardErrorResponse(
                ok=False,
                error_code=ErrorCode.SAFETY,
                message="시스템 오류가 발생했습니다.",
                hint="다시 시도해주세요."
            )
    
    def _update_auto_corrections_metrics(self, auto_corrections: Dict[str, Any]):
        """자동 보정 메트릭 업데이트"""
        for key, value in auto_corrections.items():
            if key not in self.metrics["auto_corrections"]:
                self.metrics["auto_corrections"][key] = 0
            self.metrics["auto_corrections"][key] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """메트릭 조회"""
        response_times = self.metrics["response_times"]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # P95, P99 계산
        sorted_times = sorted(response_times)
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)
        
        return {
            "summary": {
                "total_requests": self.metrics["total_requests"],
                "success_rate": self.metrics["success_count"] / max(self.metrics["total_requests"], 1),
                "avg_response_time_ms": round(avg_response_time, 2)
            },
            "error_breakdown": self.metrics["error_counts"],
            "auto_corrections": self.metrics["auto_corrections"],
            "performance": {
                "p95_ms": sorted_times[p95_idx] if sorted_times else 0,
                "p99_ms": sorted_times[p99_idx] if sorted_times else 0,
                "min_ms": min(sorted_times) if sorted_times else 0,
                "max_ms": max(sorted_times) if sorted_times else 0
            },
            "config": {
                "strict_mode": self.strict_mode,
                "rules_version": self.rules_version,
                "log_sample_rate": self.log_sample_rate
            }
        }
    
    def should_log_request(self) -> bool:
        """샘플링 기반 로깅 여부 결정"""
        import random
        return random.random() < self.log_sample_rate
    
    def log_request(self, request: GuardRequest, response: GuardResponse, response_time_ms: float):
        """요청 로깅 (샘플링 적용)"""
        if not self.should_log_request():
            return
        
        log_entry = {
            "timestamp": time.time(),
            "request_id": f"req_{int(time.time() * 1000)}",
            "route": "/guard",
            "ok": response.ok,
            "error_code": response.error_code.value if hasattr(response, 'error_code') else None,
            "auto_corrections": response.auto_corrections if hasattr(response, 'auto_corrections') else {},
            "latency_ms": round(response_time_ms, 2),
            "guard_mode": "strict" if self.strict_mode else "lenient",
            "rules_version": self.rules_version,
            "utterance_sample": request.utterance[:50] + "..." if len(request.utterance) > 50 else request.utterance
        }
        
        # 실제 운영에서는 로그 파일이나 외부 시스템으로 전송
        print(f"GUARD_LOG: {json.dumps(log_entry, ensure_ascii=False)}")


# 전역 서비스 인스턴스
guard_service = GuardService()
