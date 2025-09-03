from typing import Any, Dict, Optional

class APIException(Exception):
    """API 커스텀 예외 클래스"""
    
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}

class AuthenticationError(APIException):
    """인증 관련 예외"""
    
    def __init__(self, message: str = "인증이 필요합니다"):
        super().__init__(
            status_code=401,
            code="AUTHENTICATION_REQUIRED",
            message=message
        )

class AuthorizationError(APIException):
    """권한 관련 예외"""
    
    def __init__(self, message: str = "권한이 없습니다"):
        super().__init__(
            status_code=403,
            code="INSUFFICIENT_PERMISSIONS",
            message=message
        )

class NotFoundError(APIException):
    """리소스를 찾을 수 없음"""
    
    def __init__(self, resource: str = "리소스"):
        super().__init__(
            status_code=404,
            code="RESOURCE_NOT_FOUND",
            message=f"{resource}를 찾을 수 없습니다"
        )

class ValidationError(APIException):
    """데이터 검증 오류"""
    
    def __init__(self, message: str = "잘못된 데이터입니다", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=422,
            code="VALIDATION_ERROR",
            message=message,
            details=details
        )

class DatabaseError(APIException):
    """데이터베이스 관련 오류"""
    
    def __init__(self, message: str = "데이터베이스 오류가 발생했습니다"):
        super().__init__(
            status_code=500,
            code="DATABASE_ERROR",
            message=message
        )

class ExternalServiceError(APIException):
    """외부 서비스 연동 오류"""
    
    def __init__(self, service: str, message: str = "외부 서비스 연동 중 오류가 발생했습니다"):
        super().__init__(
            status_code=503,
            code="EXTERNAL_SERVICE_ERROR",
            message=f"{service}: {message}"
        )
