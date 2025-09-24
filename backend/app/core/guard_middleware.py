"""
가드레일 미들웨어
FastAPI 미들웨어로 요청 전 검증 수행
"""

import json
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .guard_service import guard_service
from ..shared.models.guard_models import GuardRequest
from .guard_service import GuardService


class GuardMiddleware(BaseHTTPMiddleware):
    """가드레일 미들웨어"""
    
    def __init__(self, app, whitelist_paths: set = None):
        print("🛡️ GuardMiddleware 초기화 중...")
        super().__init__(app)
        self.whitelist_paths = whitelist_paths or {
            "/health", "/docs", "/openapi.json", "/redoc",
            "/admin/guard-metrics", "/favicon.ico"
        }
        print(f"🛡️ GuardMiddleware 초기화 완료. Whitelist: {self.whitelist_paths}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """미들웨어 처리"""
        
        # 화이트리스트 경로는 우회
        if request.url.path in self.whitelist_paths:
            print(f"🔄 Guard middleware: Whitelist path {request.url.path} - bypassing")
            return await call_next(request)
        
        # POST 요청만 처리 (JSON 바디가 있는 요청)
        if request.method != "POST":
            print(f"🔄 Guard middleware: Non-POST method {request.method} - bypassing")
            return await call_next(request)
        
        # 가드레일 적용 경로 확인
        print(f"🔍 Guard middleware: Checking path: {request.url.path}")
        if not self._should_apply_guard(request.url.path):
            print(f"🔄 Guard middleware: Path {request.url.path} not in guard paths - bypassing")
            return await call_next(request)
        
        print(f"🛡️ Guard middleware: Processing {request.url.path}")
        
        try:
            # 요청 바디 읽기
            body = await request.body()
            if not body:
                return await call_next(request)
            
            # JSON 파싱
            try:
                payload = json.loads(body.decode())
            except json.JSONDecodeError:
                return await call_next(request)
            
            # ChatMessage 구조에서 message 추출
            message = payload.get('message', '')
            if not message:
                print("🔄 Guard middleware: No message field - bypassing")
                return await call_next(request)
            
            print(f"🛡️ Guard middleware: Validating message: '{message}'")
            
            # GuardRequest 모델 생성
            guard_request = GuardRequest(
                utterance=message,
                expected_intent=None,  # 자동 분류
                slots={}  # 빈 슬롯으로 시작
            )
            
            # 가드레일 서비스를 통한 검증
            guard_response = guard_service.validate_request(guard_request)
            
            # 실패 시 차단 응답 반환
            if not guard_response.ok:
                print(f"🚨 Guard middleware: {guard_response.error_code} detected!")
                return JSONResponse(
                    status_code=200,
                    content={
                        "response": guard_response.message,
                        "intent": "other",
                        "slots": {},
                        "error_code": guard_response.error_code.value,
                        "hint": guard_response.hint
                    }
                )
            
            print("✅ Guard middleware: Message passed validation")
            
            # 성공 시 바디 재주입 후 다음 단계로 전달
            await self._receive_body(request, body)
            
            # 다음 미들웨어/엔드포인트로 전달
            return await call_next(request)
        
        except Exception as e:
            # 예외 발생 시 원본 요청 그대로 전달
            print(f"🚨 Guard middleware error: {e}")
            import traceback
            traceback.print_exc()
            return await call_next(request)
    
    def _should_apply_guard(self, path: str) -> bool:
        """가드레일 적용 여부 확인"""
        guard_paths = [
            "/chat",
            "/chat/",
            "/api/v1/chat",
            "/meal",
            "/meal/",
            "/api/v1/meal",
            "/restaurant", 
            "/restaurant/",
            "/api/v1/restaurant",
            "/places",
            "/places/",
            "/api/v1/places"
        ]
        
        # 정확한 매칭 또는 슬래시 포함 매칭
        for guard_path in guard_paths:
            if path == guard_path or path.startswith(guard_path + "/"):
                return True
        return False
    
    
    async def _receive_body(self, request: Request, body: bytes):
        """요청 바디 재주입"""
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        
        request._receive = receive


