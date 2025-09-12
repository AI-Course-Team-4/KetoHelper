"""
📋 큐 관리자
- 크롤링 작업 큐 관리
- 작업 스케줄링 및 우선순위
- 동시성 제어 및 속도 제한
- 재시도 로직 관리
"""

import asyncio
import heapq
from uuid import uuid4
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..models import JobStatus, JobType
from ..utils.logger import get_logger
from ..utils.config_loader import get_config


class TaskPriority(Enum):
    """작업 우선순위"""
    LOW = 3
    NORMAL = 2  
    HIGH = 1
    URGENT = 0


@dataclass
class CrawlTask:
    """크롤링 작업"""
    id: str = field(default_factory=lambda: str(uuid4()))
    job_type: JobType = JobType.RESTAURANT_SEARCH
    site: str = "siksin"
    keyword: str = ""
    restaurant_url: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    retry_delay: float = 1.0  # seconds
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: JobStatus = JobStatus.QUEUED
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """우선순위 큐를 위한 비교 연산자"""
        if self.priority != other.priority:
            return self.priority.value < other.priority.value
        return self.scheduled_at < other.scheduled_at


class QueueManager:
    """큐 관리자"""
    
    def __init__(self, max_concurrent_tasks: int = 3):
        self.config = get_config()
        self.logger = get_logger("queue_manager")
        
        # 큐 설정
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_queue: List[CrawlTask] = []  # 우선순위 큐
        self.running_tasks: Dict[str, CrawlTask] = {}
        self.completed_tasks: Dict[str, CrawlTask] = {}
        self.failed_tasks: Dict[str, CrawlTask] = {}
        
        # 사이트별 속도 제한
        self.site_last_request: Dict[str, datetime] = {}
        self.site_request_intervals: Dict[str, float] = {
            "siksin": 0.5,  # 0.5초 간격
            "default": 1.0
        }
        
        # 동시성 제어
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        
        # 통계
        self.stats = {
            "total_enqueued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_retries": 0,
            "current_queue_size": 0,
            "current_running": 0,
        }
    
    async def start(self):
        """큐 매니저 시작"""
        if self._running:
            self.logger.warning("큐 매니저가 이미 실행 중입니다")
            return
        
        self._running = True
        self.logger.info(f"큐 매니저 시작 (최대 동시 작업: {self.max_concurrent_tasks})")
        
        # 워커 태스크들 시작
        for i in range(self.max_concurrent_tasks):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.append(worker)
    
    async def stop(self):
        """큐 매니저 중지"""
        if not self._running:
            return
        
        self.logger.info("큐 매니저 중지 중...")
        self._running = False
        
        # 모든 워커 태스크 종료 대기
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
            self._worker_tasks.clear()
        
        self.logger.info("큐 매니저 중지 완료")
    
    def add_task(self, task: CrawlTask) -> str:
        """작업 추가"""
        heapq.heappush(self.task_queue, task)
        self.stats["total_enqueued"] += 1
        self.stats["current_queue_size"] = len(self.task_queue)
        
        self.logger.info(f"작업 추가: {task.id} ({task.job_type.value}, 우선순위: {task.priority.value})")
        return task.id
    
    def add_restaurant_search_task(self, keyword: str, site: str = "siksin", 
                                 priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """식당 검색 작업 추가"""
        task = CrawlTask(
            job_type=JobType.RESTAURANT_SEARCH,
            site=site,
            keyword=keyword,
            priority=priority,
            metadata={"manual_trigger": True}
        )
        return self.add_task(task)
    
    def add_restaurant_detail_task(self, restaurant_url: str, site: str = "siksin",
                                 priority: TaskPriority = TaskPriority.HIGH) -> str:
        """식당 상세 크롤링 작업 추가"""
        task = CrawlTask(
            job_type=JobType.RESTAURANT_DETAIL,
            site=site,
            restaurant_url=restaurant_url,
            priority=priority
        )
        return self.add_task(task)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        # 실행 중인 작업에서 찾기
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            return self._task_to_status_dict(task)
        
        # 완료된 작업에서 찾기
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return self._task_to_status_dict(task)
        
        # 실패한 작업에서 찾기
        if task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
            return self._task_to_status_dict(task)
        
        # 대기 중인 작업에서 찾기
        for task in self.task_queue:
            if task.id == task_id:
                return self._task_to_status_dict(task)
        
        return None
    
    def _task_to_status_dict(self, task: CrawlTask) -> Dict[str, Any]:
        """작업을 상태 딕셔너리로 변환"""
        return {
            "id": task.id,
            "job_type": task.job_type.value,
            "site": task.site,
            "keyword": task.keyword,
            "restaurant_url": task.restaurant_url,
            "priority": task.priority.value,
            "status": task.status.value,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
            "metadata": task.metadata
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """작업 취소"""
        # 대기 중인 작업에서 제거
        new_queue = []
        cancelled = False
        
        while self.task_queue:
            task = heapq.heappop(self.task_queue)
            if task.id == task_id:
                task.status = JobStatus.CANCELLED
                self.failed_tasks[task_id] = task
                cancelled = True
                self.logger.info(f"작업 취소: {task_id}")
            else:
                new_queue.append(task)
        
        # 큐 재구성
        self.task_queue = new_queue
        heapq.heapify(self.task_queue)
        self.stats["current_queue_size"] = len(self.task_queue)
        
        return cancelled
    
    async def _worker_loop(self, worker_name: str):
        """워커 루프"""
        self.logger.info(f"워커 시작: {worker_name}")
        
        while self._running:
            try:
                # 작업 가져오기
                task = await self._get_next_task()
                if not task:
                    await asyncio.sleep(0.1)  # 잠시 대기
                    continue
                
                self.logger.info(f"{worker_name}: 작업 시작 - {task.id}")
                
                # 작업 실행
                await self._execute_task(task)
                
            except Exception as e:
                self.logger.error(f"{worker_name}: 워커 에러 - {e}")
                await asyncio.sleep(1.0)  # 에러 발생 시 잠시 대기
        
        self.logger.info(f"워커 종료: {worker_name}")
    
    async def _get_next_task(self) -> Optional[CrawlTask]:
        """다음 작업 가져오기"""
        if not self.task_queue:
            return None
        
        # 우선순위가 가장 높은 작업 가져오기
        task = heapq.heappop(self.task_queue)
        
        # 스케줄링된 시간 체크
        if task.scheduled_at > datetime.now():
            # 아직 실행할 시간이 아님 - 다시 큐에 넣기
            heapq.heappush(self.task_queue, task)
            return None
        
        # 사이트별 속도 제한 체크
        if not await self._check_rate_limit(task.site):
            # 속도 제한 - 다시 큐에 넣고 잠시 후 재시도하도록 스케줄링
            task.scheduled_at = datetime.now() + timedelta(seconds=0.1)
            heapq.heappush(self.task_queue, task)
            return None
        
        # 실행 중인 작업으로 이동
        task.status = JobStatus.RUNNING
        task.started_at = datetime.now()
        self.running_tasks[task.id] = task
        
        self.stats["current_queue_size"] = len(self.task_queue)
        self.stats["current_running"] = len(self.running_tasks)
        
        return task
    
    async def _check_rate_limit(self, site: str) -> bool:
        """사이트별 속도 제한 체크"""
        interval = self.site_request_intervals.get(site, self.site_request_intervals["default"])
        last_request = self.site_last_request.get(site)
        
        if last_request:
            elapsed = (datetime.now() - last_request).total_seconds()
            if elapsed < interval:
                return False
        
        self.site_last_request[site] = datetime.now()
        return True
    
    async def _execute_task(self, task: CrawlTask):
        """작업 실행"""
        try:
            from .crawler_engine import CrawlerEngine
            
            # 크롤러 엔진 인스턴스 생성
            engine = CrawlerEngine()
            await engine.initialize()
            
            try:
                if task.job_type == JobType.RESTAURANT_SEARCH:
                    # 식당 검색 작업
                    result = await engine.crawl_restaurant_by_name(task.keyword, task.site)
                    
                    if result.success:
                        await self._complete_task(task, result.metadata)
                    else:
                        await self._fail_task(task, "; ".join(result.errors))
                
                elif task.job_type == JobType.RESTAURANT_DETAIL:
                    # 식당 상세 정보 작업 (향후 구현)
                    await self._complete_task(task, {"message": "상세 정보 작업 완료"})
                
                else:
                    await self._fail_task(task, f"지원되지 않는 작업 유형: {task.job_type}")
                    
            finally:
                await engine.cleanup()
                
        except Exception as e:
            await self._fail_task(task, str(e))
    
    async def _complete_task(self, task: CrawlTask, metadata: Optional[Dict[str, Any]] = None):
        """작업 완료 처리"""
        task.status = JobStatus.COMPLETED
        task.completed_at = datetime.now()
        
        if metadata:
            task.metadata.update(metadata)
        
        # 실행 중에서 완료로 이동
        if task.id in self.running_tasks:
            del self.running_tasks[task.id]
        
        self.completed_tasks[task.id] = task
        
        self.stats["total_completed"] += 1
        self.stats["current_running"] = len(self.running_tasks)
        
        self.logger.info(f"작업 완료: {task.id}")
    
    async def _fail_task(self, task: CrawlTask, error_message: str):
        """작업 실패 처리"""
        task.error_message = error_message
        task.retry_count += 1
        
        # 재시도 가능한지 확인
        if task.retry_count < task.max_retries:
            # 재시도 스케줄링
            retry_delay = task.retry_delay * (2 ** (task.retry_count - 1))  # 지수 백오프
            task.scheduled_at = datetime.now() + timedelta(seconds=retry_delay)
            task.status = JobStatus.QUEUED
            
            # 실행 중에서 제거하고 큐에 다시 추가
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
            
            heapq.heappush(self.task_queue, task)
            
            self.stats["total_retries"] += 1
            self.stats["current_queue_size"] = len(self.task_queue)
            self.stats["current_running"] = len(self.running_tasks)
            
            self.logger.warning(f"작업 재시도 스케줄링: {task.id} ({task.retry_count}/{task.max_retries})")
            
        else:
            # 최대 재시도 횟수 초과
            task.status = JobStatus.FAILED
            task.completed_at = datetime.now()
            
            # 실행 중에서 실패로 이동
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
            
            self.failed_tasks[task.id] = task
            
            self.stats["total_failed"] += 1
            self.stats["current_running"] = len(self.running_tasks)
            
            self.logger.error(f"작업 최종 실패: {task.id} - {error_message}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """큐 상태 정보"""
        return {
            "running": self._running,
            "queue_size": len(self.task_queue),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "max_concurrent": self.max_concurrent_tasks,
            "stats": self.stats.copy(),
            "site_intervals": self.site_request_intervals.copy()
        }
    
    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """실행 중인 작업 목록"""
        return [self._task_to_status_dict(task) for task in self.running_tasks.values()]
    
    def get_recent_completed_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 완료된 작업 목록"""
        tasks = sorted(
            self.completed_tasks.values(),
            key=lambda t: t.completed_at or datetime.min,
            reverse=True
        )
        return [self._task_to_status_dict(task) for task in tasks[:limit]]


# 전역 큐 매니저 인스턴스
_queue_manager = None


def get_queue_manager() -> QueueManager:
    """큐 매니저 싱글톤 반환"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = QueueManager()
    return _queue_manager


if __name__ == "__main__":
    import asyncio
    
    async def test_queue_manager():
        """큐 매니저 테스트"""
        print("=== 큐 매니저 테스트 ===")
        
        manager = QueueManager(max_concurrent_tasks=2)
        
        try:
            await manager.start()
            
            # 테스트 작업 추가
            task_id1 = manager.add_restaurant_search_task("강남 맛집", priority=TaskPriority.HIGH)
            task_id2 = manager.add_restaurant_search_task("홍대 맛집", priority=TaskPriority.NORMAL)
            
            print(f"작업 추가: {task_id1}, {task_id2}")
            
            # 잠시 실행 대기
            await asyncio.sleep(5)
            
            # 상태 확인
            status = manager.get_queue_status()
            print(f"큐 상태: {status}")
            
        finally:
            await manager.stop()
    
    asyncio.run(test_queue_manager())