"""
🔄 크롤링 엔진
- 전체 크롤링 프로세스 오케스트레이션
- 파서와 데이터베이스 연동
- 에러 처리 및 재시도 로직
- 진행 상황 추적 및 통계
"""

import asyncio
import traceback
from uuid import uuid4
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..models import (
    Restaurant, RestaurantCreate, RestaurantUpdate,
    Menu, MenuCreate, MenuUpdate, 
    CrawlJob, CrawlJobCreate, CrawlJobUpdate,
    JobStatus, JobType
)
from ..database import (
    get_restaurant_repository,
    get_menu_repository, 
    get_crawl_job_repository,
    get_database
)
from ..parsers import get_parser_factory, get_parser
from ..utils.logger import get_logger
from ..utils.config_loader import get_config
from ..utils.http_client import HttpClient
from ..utils.text_utils import calculate_similarity


@dataclass
class CrawlingResult:
    """크롤링 결과"""
    job_id: str
    success: bool
    restaurant_count: int
    menu_count: int
    duplicate_count: int
    error_count: int
    processing_time: float
    errors: List[str]
    metadata: Dict[str, Any]


class CrawlerEngine:
    """크롤링 엔진 메인 클래스"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("crawler_engine")
        
        # 컴포넌트 초기화
        self.http_client = None
        self.parser_factory = None
        
        # 통계
        self.stats = {
            "total_jobs": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
            "restaurants_crawled": 0,
            "menus_crawled": 0,
            "duplicates_found": 0,
            "errors_encountered": 0
        }
        
    async def initialize(self):
        """엔진 초기화"""
        try:
            self.logger.info("크롤링 엔진 초기화 시작")
            
            # HTTP 클라이언트 초기화
            self.http_client = HttpClient(self.config)
            await self.http_client.initialize()
            
            # 파서 팩토리 초기화
            self.parser_factory = get_parser_factory()
            
            # 데이터베이스 연결 확인
            async with get_database() as db:
                result = await db.execute_query("SELECT 1")
                if not result:
                    raise Exception("데이터베이스 연결 실패")
            
            self.logger.info("크롤링 엔진 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"엔진 초기화 실패: {e}")
            raise
            
    async def cleanup(self):
        """리소스 정리"""
        try:
            if self.http_client:
                await self.http_client.cleanup()
            self.logger.info("크롤링 엔진 정리 완료")
        except Exception as e:
            self.logger.error(f"정리 중 오류: {e}")
    
    async def crawl_restaurant_by_name(self, restaurant_name: str, site: str = "siksin") -> CrawlingResult:
        """식당명으로 크롤링"""
        job_id = str(uuid4())
        start_time = datetime.now()
        
        self.logger.info(f"식당 크롤링 시작: {restaurant_name} (사이트: {site})")
        
        try:
            # 크롤 작업 생성
            crawl_job_repo = get_crawl_job_repository()
            job_data = CrawlJobCreate(
                job_type=JobType.RESTAURANT_SEARCH,
                site=site,
                keyword=restaurant_name,
                status=JobStatus.RUNNING,
                metadata={"manual_trigger": True}
            )
            
            job = await crawl_job_repo.create(job_data)
            job_id = str(job.id)
            
            # 파서 획득
            parser = get_parser(site, self.http_client)
            if not parser:
                raise Exception(f"지원되지 않는 사이트: {site}")
            
            # 검색 실행
            search_result = await parser.search(restaurant_name, page=1)
            
            if not search_result.restaurants:
                await self._update_job_status(job_id, JobStatus.COMPLETED, 
                                            f"검색 결과 없음: {restaurant_name}")
                return CrawlingResult(
                    job_id=job_id,
                    success=True,
                    restaurant_count=0,
                    menu_count=0,
                    duplicate_count=0,
                    error_count=0,
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    errors=[],
                    metadata={"message": "검색 결과 없음"}
                )
            
            # 상세 정보 크롤링
            return await self._process_restaurant_list(
                job_id, search_result.restaurants, site, start_time
            )
            
        except Exception as e:
            error_msg = f"크롤링 실패: {str(e)}"
            self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
            
            await self._update_job_status(job_id, JobStatus.FAILED, error_msg)
            
            return CrawlingResult(
                job_id=job_id,
                success=False,
                restaurant_count=0,
                menu_count=0,
                duplicate_count=0,
                error_count=1,
                processing_time=(datetime.now() - start_time).total_seconds(),
                errors=[error_msg],
                metadata={"exception": str(e)}
            )
    
    async def _process_restaurant_list(self, job_id: str, restaurants: List[RestaurantCreate], 
                                     site: str, start_time: datetime) -> CrawlingResult:
        """식당 목록 처리"""
        restaurant_count = 0
        menu_count = 0
        duplicate_count = 0
        error_count = 0
        errors = []
        
        parser = get_parser(site, self.http_client)
        restaurant_repo = get_restaurant_repository()
        menu_repo = get_menu_repository()
        
        for restaurant_data in restaurants:
            try:
                self.logger.info(f"식당 처리: {restaurant_data.name}")
                
                # 중복 체크
                existing = await self._check_duplicate_restaurant(restaurant_data)
                if existing:
                    self.logger.info(f"중복 식당 발견: {restaurant_data.name}")
                    duplicate_count += 1
                    
                    # 기존 데이터 업데이트
                    await self._update_existing_restaurant(existing, restaurant_data)
                    continue
                
                # 상세 정보 크롤링 (URL이 있는 경우)
                menus = []
                if restaurant_data.source_url:
                    detail_result = await parser.parse_restaurant_detail(restaurant_data.source_url)
                    if detail_result.success and detail_result.data:
                        # 식당 상세 정보 업데이트
                        detail_restaurant = detail_result.data.get('restaurant', {})
                        restaurant_data = self._merge_restaurant_data(restaurant_data, detail_restaurant)
                        
                        # 메뉴 정보
                        menu_data_list = detail_result.data.get('menus', [])
                        for menu_data in menu_data_list:
                            menus.append(MenuCreate(**menu_data))
                
                # 데이터 품질 검증
                quality_score = self._calculate_quality_score(restaurant_data, menus)
                restaurant_data.quality_score = quality_score
                
                # 식당 저장
                restaurant = await restaurant_repo.create(restaurant_data)
                restaurant_count += 1
                self.logger.info(f"식당 저장 완료: {restaurant.name} (ID: {restaurant.id})")
                
                # 메뉴 저장
                for menu_data in menus:
                    menu_data.restaurant_id = restaurant.id
                    await menu_repo.create(menu_data)
                    menu_count += 1
                
                # 통계 업데이트
                self.stats["restaurants_crawled"] += 1
                self.stats["menus_crawled"] += len(menus)
                
            except Exception as e:
                error_msg = f"식당 처리 실패 ({restaurant_data.name}): {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                error_count += 1
                self.stats["errors_encountered"] += 1
        
        # 작업 완료 처리
        processing_time = (datetime.now() - start_time).total_seconds()
        
        status = JobStatus.COMPLETED if error_count == 0 else JobStatus.COMPLETED_WITH_ERRORS
        status_message = f"완료 - 식당: {restaurant_count}, 메뉴: {menu_count}, 중복: {duplicate_count}, 에러: {error_count}"
        
        await self._update_job_status(job_id, status, status_message, {
            "restaurant_count": restaurant_count,
            "menu_count": menu_count,
            "duplicate_count": duplicate_count,
            "error_count": error_count,
            "processing_time": processing_time
        })
        
        # 통계 업데이트
        self.stats["total_jobs"] += 1
        if error_count == 0:
            self.stats["successful_jobs"] += 1
        else:
            self.stats["failed_jobs"] += 1
        self.stats["duplicates_found"] += duplicate_count
        
        return CrawlingResult(
            job_id=job_id,
            success=True,
            restaurant_count=restaurant_count,
            menu_count=menu_count,
            duplicate_count=duplicate_count,
            error_count=error_count,
            processing_time=processing_time,
            errors=errors,
            metadata={
                "site": site,
                "total_processed": len(restaurants)
            }
        )
    
    async def _check_duplicate_restaurant(self, restaurant_data: RestaurantCreate) -> Optional[Restaurant]:
        """중복 식당 체크"""
        restaurant_repo = get_restaurant_repository()
        
        # 이름 기반 검색
        similar = await restaurant_repo.find_similar_by_name(restaurant_data.name, threshold=0.8)
        if similar:
            for existing in similar:
                # 추가 유사성 체크 (주소, 전화번호 등)
                if self._is_same_restaurant(existing, restaurant_data):
                    return existing
        
        return None
    
    def _is_same_restaurant(self, existing: Restaurant, new_data: RestaurantCreate) -> bool:
        """같은 식당인지 판단"""
        # 이름 유사도
        name_similarity = calculate_similarity(existing.name, new_data.name)
        if name_similarity < 0.7:
            return False
        
        # 주소 유사도 (있는 경우)
        if existing.address_road and new_data.address_road:
            addr_similarity = calculate_similarity(existing.address_road, new_data.address_road)
            if addr_similarity > 0.6:
                return True
        
        # 전화번호 일치 (있는 경우)
        if existing.phone and new_data.phone:
            return existing.phone == new_data.phone
        
        # 좌표 거리 (있는 경우)
        if (existing.lat and existing.lng and 
            new_data.lat and new_data.lng):
            distance = self._calculate_distance(
                existing.lat, existing.lng,
                new_data.lat, new_data.lng
            )
            if distance < 0.1:  # 100m 이내
                return True
        
        return name_similarity > 0.9  # 이름이 매우 유사하면 동일로 판단
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """두 좌표 간 거리 계산 (km)"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # 지구 반지름 (km)
        
        lat1_rad = radians(lat1)
        lng1_rad = radians(lng1)
        lat2_rad = radians(lat2)
        lng2_rad = radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    async def _update_existing_restaurant(self, existing: Restaurant, new_data: RestaurantCreate):
        """기존 식당 정보 업데이트"""
        restaurant_repo = get_restaurant_repository()
        
        # 더 나은 정보로 업데이트
        update_data = {}
        
        # 평점이 더 좋은 정보로 업데이트
        if new_data.rating and (not existing.rating or new_data.rating > existing.rating):
            update_data['rating'] = new_data.rating
        
        # 리뷰 수가 더 많은 정보로 업데이트
        if new_data.review_count and (not existing.review_count or new_data.review_count > existing.review_count):
            update_data['review_count'] = new_data.review_count
        
        # 빈 필드 채우기
        for field in ['phone', 'homepage_url', 'business_hours', 'lat', 'lng']:
            if not getattr(existing, field) and getattr(new_data, field):
                update_data[field] = getattr(new_data, field)
        
        if update_data:
            update_data['updated_at'] = datetime.now()
            await restaurant_repo.update(existing.id, RestaurantUpdate(**update_data))
            self.logger.info(f"기존 식당 정보 업데이트: {existing.name}")
    
    def _merge_restaurant_data(self, base_data: RestaurantCreate, detail_data: Dict[str, Any]) -> RestaurantCreate:
        """기본 데이터와 상세 데이터 병합"""
        # 더 완전한 정보로 업데이트
        for field, value in detail_data.items():
            if value and (not getattr(base_data, field, None) or 
                         getattr(base_data, field, None) == ""):
                setattr(base_data, field, value)
        
        return base_data
    
    def _calculate_quality_score(self, restaurant: RestaurantCreate, menus: List[MenuCreate]) -> int:
        """데이터 품질 점수 계산 (0-100)"""
        score = 0
        
        # 필수 정보 (40점)
        if restaurant.name: score += 20
        if restaurant.address_road: score += 10
        if restaurant.phone: score += 10
        
        # 위치 정보 (20점)
        if restaurant.lat and restaurant.lng: score += 20
        
        # 평점/리뷰 정보 (20점)
        if restaurant.rating: score += 10
        if restaurant.review_count: score += 10
        
        # 메뉴 정보 (20점)
        if menus:
            score += min(len(menus) * 2, 15)  # 메뉴 개수
            if any(menu.price for menu in menus): score += 5  # 가격 정보
        
        return min(score, 100)
    
    async def _update_job_status(self, job_id: str, status: JobStatus, 
                               message: str, metadata: Optional[Dict[str, Any]] = None):
        """작업 상태 업데이트"""
        try:
            crawl_job_repo = get_crawl_job_repository()
            update_data = CrawlJobUpdate(
                status=status,
                progress_message=message,
                completed_at=datetime.now() if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.COMPLETED_WITH_ERRORS] else None
            )
            
            if metadata:
                update_data.metadata = metadata
            
            await crawl_job_repo.update(job_id, update_data)
            
        except Exception as e:
            self.logger.error(f"작업 상태 업데이트 실패: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """엔진 통계 반환"""
        return {
            **self.stats,
            "parser_stats": self.parser_factory.get_parser_info() if self.parser_factory else {},
            "http_client_stats": self.http_client.get_stats() if self.http_client else {}
        }
    
    def reset_stats(self):
        """통계 초기화"""
        self.stats = {k: 0 for k in self.stats.keys()}


# 편의 함수들
async def crawl_restaurant(restaurant_name: str, site: str = "siksin") -> CrawlingResult:
    """식당 크롤링 편의 함수"""
    engine = CrawlerEngine()
    try:
        await engine.initialize()
        return await engine.crawl_restaurant_by_name(restaurant_name, site)
    finally:
        await engine.cleanup()


if __name__ == "__main__":
    import asyncio
    
    async def test_crawler():
        """크롤러 테스트"""
        print("=== 크롤러 엔진 테스트 ===")
        
        # 테스트 실행
        result = await crawl_restaurant("강남 맛집")
        
        print(f"결과:")
        print(f"  성공: {result.success}")
        print(f"  식당 수: {result.restaurant_count}")
        print(f"  메뉴 수: {result.menu_count}")
        print(f"  중복 수: {result.duplicate_count}")
        print(f"  에러 수: {result.error_count}")
        print(f"  처리 시간: {result.processing_time:.2f}초")
        
        if result.errors:
            print(f"  에러:")
            for error in result.errors[:3]:  # 처음 3개만
                print(f"    - {error}")
    
    asyncio.run(test_crawler())