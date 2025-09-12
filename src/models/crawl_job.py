"""
🕷️ CrawlJob 데이터 모델
- 크롤링 작업 관리 및 상태 추적
- 비동기 작업 큐 지원
- 에러 처리 및 재시도 로직
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import conint, constr


class JobStatus(str, Enum):
    """작업 상태"""
    QUEUED = "queued"      # 대기중
    RUNNING = "running"    # 실행중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"      # 실패
    CANCELLED = "cancelled"  # 취소됨


class JobType(str, Enum):
    """작업 유형"""
    SEARCH = "search"      # 검색
    DETAIL = "detail"      # 상세 정보
    BATCH = "batch"        # 배치 작업


class ErrorCode(str, Enum):
    """에러 코드"""
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    PARSE_ERROR = "parse_error"
    BLOCKED_ERROR = "blocked_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"


class CrawlJobBase(BaseModel):
    """CrawlJob 기본 모델"""
    
    # 🎯 작업 정보
    job_type: JobType = Field(..., description="작업 유형")
    site: str = Field(..., max_length=20, description="대상 사이트")
    url: str = Field(..., max_length=1000, description="크롤링 대상 URL")
    keyword: Optional[str] = Field(None, max_length=100, description="검색 키워드")
    
    # 📊 작업 상태
    status: JobStatus = Field(JobStatus.QUEUED, description="작업 상태")
    priority: int = Field(0, description="우선순위 (높을수록 먼저 처리)")
    attempts: int = Field(0, description="시도 횟수")
    max_attempts: int = Field(3, description="최대 시도 횟수")
    
    # ❌ 오류 정보
    last_error_code: Optional[ErrorCode] = Field(None, description="마지막 오류 코드")
    last_error_message: Optional[str] = Field(None, max_length=1000, description="마지막 오류 메시지")
    last_error_at: Optional[datetime] = Field(None, description="마지막 오류 발생 시간")
    
    # ⏱️ 시간 정보
    scheduled_at: datetime = Field(default_factory=datetime.utcnow, description="예약 시간")
    started_at: Optional[datetime] = Field(None, description="시작 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    
    # 🔧 추가 설정
    config: Optional[Dict[str, Any]] = Field(None, description="작업별 설정")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        str_strip_whitespace = True


class CrawlJobCreate(CrawlJobBase):
    """CrawlJob 생성 모델"""
    pass


class CrawlJobUpdate(BaseModel):
    """CrawlJob 업데이트 모델"""
    status: Optional[JobStatus] = None
    priority: Optional[int] = None
    attempts: Optional[int] = None
    last_error_code: Optional[ErrorCode] = None
    last_error_message: Optional[str] = Field(None, max_length=1000)
    last_error_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class CrawlJob(CrawlJobBase):
    """CrawlJob 완전 모델 (DB 포함)"""
    
    # 🔑 시스템 필드
    id: UUID = Field(default_factory=uuid4, description="고유 식별자")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="수정 시간")
    
    class Config(CrawlJobBase.Config):
        orm_mode = True
    
    @validator('site')
    def validate_site(cls, v):
        """사이트명 검증"""
        allowed_sites = ['siksin', 'diningcode', 'mangoplate']
        if v not in allowed_sites:
            raise ValueError(f'지원되지 않는 사이트입니다: {v}')
        return v
    
    @validator('url')
    def validate_url(cls, v):
        """URL 검증"""
        import re
        url_pattern = r'^https?://.+'
        if not re.match(url_pattern, v):
            raise ValueError('올바른 URL 형식이 아닙니다')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        """우선순위 검증"""
        if v < -100 or v > 100:
            raise ValueError('우선순위는 -100~100 사이여야 합니다')
        return v
    
    @validator('attempts')
    def validate_attempts(cls, v, values):
        """시도 횟수 검증"""
        max_attempts = values.get('max_attempts', 3)
        if v > max_attempts:
            raise ValueError(f'시도 횟수가 최대값을 초과했습니다: {v} > {max_attempts}')
        return v
    
    @root_validator
    def validate_times(cls, values):
        """시간 관련 검증"""
        scheduled_at = values.get('scheduled_at')
        started_at = values.get('started_at')
        completed_at = values.get('completed_at')
        
        if started_at and scheduled_at and started_at < scheduled_at:
            raise ValueError('시작 시간이 예약 시간보다 빠를 수 없습니다')
        
        if completed_at and started_at and completed_at < started_at:
            raise ValueError('완료 시간이 시작 시간보다 빠를 수 없습니다')
        
        return values
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return self.dict(exclude_none=True)
    
    def is_pending(self) -> bool:
        """대기중 여부"""
        return self.status == JobStatus.QUEUED
    
    def is_running(self) -> bool:
        """실행중 여부"""
        return self.status == JobStatus.RUNNING
    
    def is_completed(self) -> bool:
        """완료 여부"""
        return self.status == JobStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """실패 여부"""
        return self.status == JobStatus.FAILED
    
    def can_retry(self) -> bool:
        """재시도 가능 여부"""
        return (self.is_failed() and 
                self.attempts < self.max_attempts and
                self.last_error_code != ErrorCode.VALIDATION_ERROR)
    
    def get_duration(self) -> Optional[timedelta]:
        """실행 시간 계산"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return datetime.utcnow() - self.started_at
        return None
    
    def get_wait_time(self) -> Optional[timedelta]:
        """대기 시간 계산"""
        if self.started_at:
            return self.started_at - self.scheduled_at
        else:
            return datetime.utcnow() - self.scheduled_at
    
    def calculate_next_retry_time(self) -> datetime:
        """다음 재시도 시간 계산 (지수 백오프)"""
        base_delay = 60  # 1분
        max_delay = 3600  # 1시간
        
        delay = min(base_delay * (2 ** self.attempts), max_delay)
        return datetime.utcnow() + timedelta(seconds=delay)
    
    def get_display_status(self) -> str:
        """상태 표시 문자열"""
        status_display = {
            JobStatus.QUEUED: "⏳ 대기중",
            JobStatus.RUNNING: "🔄 실행중",
            JobStatus.COMPLETED: "✅ 완료",
            JobStatus.FAILED: "❌ 실패",
            JobStatus.CANCELLED: "🚫 취소됨"
        }
        return status_display.get(self.status, str(self.status))
    
    def get_progress_info(self) -> Dict[str, Any]:
        """진행 정보 반환"""
        duration = self.get_duration()
        wait_time = self.get_wait_time()
        
        return {
            "id": str(self.id),
            "status": self.get_display_status(),
            "job_type": self.job_type.value,
            "site": self.site,
            "keyword": self.keyword,
            "attempts": f"{self.attempts}/{self.max_attempts}",
            "duration": str(duration) if duration else None,
            "wait_time": str(wait_time) if wait_time else None,
            "last_error": self.last_error_message,
            "scheduled_at": self.scheduled_at.isoformat(),
            "can_retry": self.can_retry()
        }


class CrawlJobSearch(BaseModel):
    """CrawlJob 검색 모델"""
    
    job_type: Optional[JobType] = Field(None, description="작업 유형 필터")
    site: Optional[str] = Field(None, description="사이트 필터")
    status: Optional[JobStatus] = Field(None, description="상태 필터")
    keyword: Optional[str] = Field(None, description="키워드 필터")
    
    # 시간 범위
    scheduled_after: Optional[datetime] = Field(None, description="예약 시간 이후")
    scheduled_before: Optional[datetime] = Field(None, description="예약 시간 이전")
    
    # 특성 필터
    has_errors: Optional[bool] = Field(None, description="에러 보유 여부")
    can_retry: Optional[bool] = Field(None, description="재시도 가능 여부")
    
    # 페이지네이션
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(20, ge=1, le=100, description="페이지 크기")
    
    # 정렬
    sort_by: str = Field("scheduled_at", description="정렬 기준")
    sort_desc: bool = Field(True, description="내림차순 정렬")


class CrawlJobStats(BaseModel):
    """CrawlJob 통계 모델"""
    
    total_count: int = Field(0, description="전체 작업 수")
    by_status: Dict[str, int] = Field(default_factory=dict, description="상태별 개수")
    by_site: Dict[str, int] = Field(default_factory=dict, description="사이트별 개수")
    by_job_type: Dict[str, int] = Field(default_factory=dict, description="작업 유형별 개수")
    by_error_code: Dict[str, int] = Field(default_factory=dict, description="에러 코드별 개수")
    
    success_rate: float = Field(0.0, description="성공률")
    avg_duration: Optional[float] = Field(None, description="평균 실행 시간 (초)")
    avg_wait_time: Optional[float] = Field(None, description="평균 대기 시간 (초)")
    
    pending_count: int = Field(0, description="대기중 작업 수")
    running_count: int = Field(0, description="실행중 작업 수")
    failed_count: int = Field(0, description="실패 작업 수")
    retryable_count: int = Field(0, description="재시도 가능 작업 수")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="마지막 업데이트")


class CrawlResult(BaseModel):
    """크롤링 결과 모델"""
    
    job_id: UUID = Field(..., description="작업 ID")
    success: bool = Field(..., description="성공 여부")
    
    # 수집 결과
    restaurants_found: int = Field(0, description="발견된 식당 수")
    restaurants_saved: int = Field(0, description="저장된 식당 수")
    menus_found: int = Field(0, description="발견된 메뉴 수")
    menus_saved: int = Field(0, description="저장된 메뉴 수")
    
    # 처리 정보
    pages_crawled: int = Field(0, description="크롤링한 페이지 수")
    duration: float = Field(0.0, description="실행 시간 (초)")
    
    # 에러 정보
    errors: List[str] = Field(default_factory=list, description="발생한 에러 목록")
    warnings: List[str] = Field(default_factory=list, description="경고 목록")
    
    # 메타데이터
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 정보")
    
    def get_summary(self) -> str:
        """결과 요약"""
        if self.success:
            return (f"✅ 성공: 식당 {self.restaurants_saved}개, "
                   f"메뉴 {self.menus_saved}개 저장 "
                   f"({self.duration:.1f}초)")
        else:
            error_count = len(self.errors)
            return f"❌ 실패: {error_count}개 에러 ({self.duration:.1f}초)"


# 편의 함수들
def create_search_job(site: str, keyword: str, priority: int = 0) -> CrawlJobCreate:
    """검색 작업 생성"""
    # URL은 사이트별로 다르게 생성해야 함 (실제 구현에서)
    url = f"https://{site}.com/search?q={keyword}"
    
    return CrawlJobCreate(
        job_type=JobType.SEARCH,
        site=site,
        url=url,
        keyword=keyword,
        priority=priority
    )


def create_detail_job(site: str, url: str, priority: int = 0) -> CrawlJobCreate:
    """상세 정보 작업 생성"""
    return CrawlJobCreate(
        job_type=JobType.DETAIL,
        site=site,
        url=url,
        priority=priority
    )


def create_batch_job(site: str, urls: List[str], priority: int = 0) -> List[CrawlJobCreate]:
    """배치 작업 생성"""
    jobs = []
    for i, url in enumerate(urls):
        job = CrawlJobCreate(
            job_type=JobType.BATCH,
            site=site,
            url=url,
            priority=priority - i  # 순서대로 우선순위 부여
        )
        jobs.append(job)
    
    return jobs


if __name__ == "__main__":
    # 테스트 코드
    
    # 검색 작업 생성
    search_job_data = {
        "job_type": JobType.SEARCH,
        "site": "siksin",
        "url": "https://siksin.com/search?q=강남맛집",
        "keyword": "강남맛집",
        "priority": 10
    }
    
    try:
        job = CrawlJob(**search_job_data)
        print(f"✅ CrawlJob 생성 성공: {job.id}")
        print(f"   표시 상태: {job.get_display_status()}")
        print(f"   대기중 여부: {job.is_pending()}")
        print(f"   재시도 가능: {job.can_retry()}")
        print(f"   대기 시간: {job.get_wait_time()}")
        
        # 진행 정보 테스트
        progress = job.get_progress_info()
        print(f"   진행 정보: {progress}")
        
        # 편의 함수 테스트
        search_job = create_search_job("siksin", "강남맛집", 5)
        print(f"   검색 작업 생성: {search_job.keyword}")
        
        # JSON 직렬화 테스트
        json_data = job.json()
        print(f"   JSON 크기: {len(json_data)}바이트")
        
    except Exception as e:
        print(f"❌ CrawlJob 생성 실패: {e}")