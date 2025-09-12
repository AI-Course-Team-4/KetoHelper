"""
📝 로깅 설정 모듈
- loguru 기반 고급 로깅
- 파일별, 레벨별 로깅
- 자동 로테이션 및 압축
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

from .config_loader import get_config


class CrawlerLogger:
    """크롤링 시스템 전용 로거"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = get_config(config_path)
        self.is_initialized = False
        self._setup_logger()
    
    def _setup_logger(self):
        """로거 설정"""
        if self.is_initialized:
            return
            
        # 기존 핸들러 제거
        logger.remove()
        
        # 로그 디렉토리 생성
        self._ensure_log_directories()
        
        # 콘솔 로거 설정
        self._setup_console_logger()
        
        # 파일 로거 설정
        self._setup_file_loggers()
        
        self.is_initialized = True
        logger.info("로깅 시스템 초기화 완료")
    
    def _ensure_log_directories(self):
        """로그 디렉토리 생성"""
        log_files = self.config.logging.files
        
        for log_file in log_files.values():
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _setup_console_logger(self):
        """콘솔 로거 설정"""
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.add(
            sys.stdout,
            format=console_format,
            level=self.config.logging.level,
            colorize=True,
            backtrace=True,
            diagnose=True,
            filter=self._filter_console_logs
        )
    
    def _setup_file_loggers(self):
        """파일 로거 설정"""
        log_config = self.config.logging
        
        # 메인 로그 파일 (모든 레벨)
        logger.add(
            log_config.files["main"],
            format=log_config.format,
            level="DEBUG",
            rotation=log_config.rotation["size"],
            retention=log_config.rotation["retention"],
            compression="zip",
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )
        
        # 에러 로그 파일 (ERROR 이상만)
        logger.add(
            log_config.files["error"],
            format=log_config.format,
            level="ERROR",
            rotation=log_config.rotation["size"],
            retention=log_config.rotation["retention"],
            compression="zip",
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )
        
        # 액세스 로그 파일 (HTTP 요청 관련)
        logger.add(
            log_config.files["access"],
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="INFO",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            filter=lambda record: record["extra"].get("type") == "access"
        )
    
    def _filter_console_logs(self, record) -> bool:
        """콘솔 로그 필터링"""
        # 액세스 로그는 콘솔에 출력하지 않음
        if record["extra"].get("type") == "access":
            return False
        
        # 디버그 모드가 아니면 DEBUG 로그 숨김
        if not self.config.is_debug() and record["level"].name == "DEBUG":
            return False
            
        return True
    
    def get_logger(self, name: str = "crawler") -> Any:
        """이름이 지정된 로거 반환"""
        return logger.bind(name=name)
    
    def log_request(self, method: str, url: str, status_code: int, 
                   response_time: float, site: str = "unknown"):
        """HTTP 요청 로깅"""
        logger.bind(type="access").info(
            f"{method} {url} - {status_code} - {response_time:.2f}s - {site}"
        )
    
    def log_crawl_start(self, site: str, keyword: str, job_id: str):
        """크롤링 시작 로깅"""
        logger.bind(name="crawler").info(
            f"크롤링 시작: {site} | 키워드: {keyword} | Job ID: {job_id}"
        )
    
    def log_crawl_complete(self, site: str, restaurants_found: int, 
                          menus_found: int, duration: float, job_id: str):
        """크롤링 완료 로깅"""
        logger.bind(name="crawler").info(
            f"크롤링 완료: {site} | 식당: {restaurants_found}개 | "
            f"메뉴: {menus_found}개 | 소요시간: {duration:.2f}s | Job ID: {job_id}"
        )
    
    def log_crawl_error(self, site: str, error: str, url: str = "", job_id: str = ""):
        """크롤링 에러 로깅"""
        logger.bind(name="crawler").error(
            f"크롤링 에러: {site} | URL: {url} | 에러: {error} | Job ID: {job_id}"
        )
    
    def log_parser_error(self, site: str, selector: str, url: str, error: str):
        """파싱 에러 로깅"""
        logger.bind(name="parser").error(
            f"파싱 에러: {site} | 셀렉터: {selector} | URL: {url} | 에러: {error}"
        )
    
    def log_blocking_detected(self, site: str, url: str, indicator: str):
        """차단 감지 로깅"""
        logger.bind(name="security").warning(
            f"차단 감지: {site} | URL: {url} | 지표: {indicator}"
        )
    
    def log_rate_limit(self, site: str, current_qps: float, new_qps: float):
        """속도 제한 로깅"""
        logger.bind(name="rate_limit").warning(
            f"속도 제한 적용: {site} | {current_qps:.2f} -> {new_qps:.2f} QPS"
        )
    
    def log_database_operation(self, operation: str, table: str, 
                              record_count: int = 1, duration: float = 0):
        """데이터베이스 작업 로깅"""
        logger.bind(name="database").debug(
            f"DB 작업: {operation} | 테이블: {table} | "
            f"레코드: {record_count}개 | 소요시간: {duration:.3f}s"
        )
    
    def log_validation_error(self, data_type: str, field: str, value: Any, error: str):
        """데이터 검증 에러 로깅"""
        logger.bind(name="validator").warning(
            f"검증 실패: {data_type}.{field} = {value} | 에러: {error}"
        )
    
    def log_duplicate_found(self, data_type: str, key: str, source1: str, source2: str):
        """중복 데이터 발견 로깅"""
        logger.bind(name="deduplicator").info(
            f"중복 발견: {data_type} | 키: {key} | 소스: {source1} vs {source2}"
        )
    
    def log_performance(self, operation: str, duration: float, 
                       throughput: float = 0, unit: str = "ops/s"):
        """성능 메트릭 로깅"""
        logger.bind(name="performance").info(
            f"성능: {operation} | 소요시간: {duration:.2f}s | "
            f"처리량: {throughput:.2f} {unit}"
        )


# 전역 로거 인스턴스
_crawler_logger = None


def get_logger(name: str = "crawler") -> Any:
    """전역 로거 인스턴스 반환"""
    global _crawler_logger
    
    if _crawler_logger is None:
        _crawler_logger = CrawlerLogger()
    
    return _crawler_logger.get_logger(name)


def setup_logging(config_path: Optional[str] = None):
    """로깅 시스템 설정"""
    global _crawler_logger
    _crawler_logger = CrawlerLogger(config_path)


# 편의 함수들
def log_request(method: str, url: str, status_code: int, 
                response_time: float, site: str = "unknown"):
    """HTTP 요청 로깅"""
    global _crawler_logger
    if _crawler_logger:
        _crawler_logger.log_request(method, url, status_code, response_time, site)


def log_crawl_start(site: str, keyword: str, job_id: str):
    """크롤링 시작 로깅"""
    global _crawler_logger
    if _crawler_logger:
        _crawler_logger.log_crawl_start(site, keyword, job_id)


def log_crawl_complete(site: str, restaurants_found: int, 
                      menus_found: int, duration: float, job_id: str):
    """크롤링 완료 로깅"""
    global _crawler_logger
    if _crawler_logger:
        _crawler_logger.log_crawl_complete(
            site, restaurants_found, menus_found, duration, job_id
        )


def log_crawl_error(site: str, error: str, url: str = "", job_id: str = ""):
    """크롤링 에러 로깅"""
    global _crawler_logger
    if _crawler_logger:
        _crawler_logger.log_crawl_error(site, error, url, job_id)


def log_parser_error(site: str, selector: str, url: str, error: str):
    """파싱 에러 로깅"""
    global _crawler_logger
    if _crawler_logger:
        _crawler_logger.log_parser_error(site, selector, url, error)


def log_blocking_detected(site: str, url: str, indicator: str):
    """차단 감지 로깅"""
    global _crawler_logger
    if _crawler_logger:
        _crawler_logger.log_blocking_detected(site, url, indicator)


def log_rate_limit(site: str, current_qps: float, new_qps: float):
    """속도 제한 로깅"""
    global _crawler_logger
    if _crawler_logger:
        _crawler_logger.log_rate_limit(site, current_qps, new_qps)


def log_database_operation(operation: str, table: str, 
                          record_count: int = 1, duration: float = 0):
    """데이터베이스 작업 로깅"""
    global _crawler_logger
    if _crawler_logger:
        _crawler_logger.log_database_operation(operation, table, record_count, duration)


def log_validation_error(data_type: str, field: str, value: Any, error: str):
    """데이터 검증 에러 로깅"""
    global _crawler_logger
    if _crawler_logger:
        _crawler_logger.log_validation_error(data_type, field, value, error)


def log_duplicate_found(data_type: str, key: str, source1: str, source2: str):
    """중복 데이터 발견 로깅"""
    global _crawler_logger
    if _crawler_logger:
        _crawler_logger.log_duplicate_found(data_type, key, source1, source2)


def log_performance(operation: str, duration: float, 
                   throughput: float = 0, unit: str = "ops/s"):
    """성능 메트릭 로깅"""
    global _crawler_logger
    if _crawler_logger:
        _crawler_logger.log_performance(operation, duration, throughput, unit)


if __name__ == "__main__":
    # 테스트 코드
    setup_logging()
    
    logger = get_logger("test")
    
    logger.info("테스트 로그 메시지")
    logger.debug("디버그 메시지")
    logger.warning("경고 메시지")
    logger.error("에러 메시지")
    
    # 전용 로깅 함수 테스트
    log_request("GET", "https://example.com", 200, 1.5, "test_site")
    log_crawl_start("test_site", "테스트 키워드", "job-123")
    log_crawl_complete("test_site", 5, 25, 10.5, "job-123")
    
    print("로깅 테스트 완료!")