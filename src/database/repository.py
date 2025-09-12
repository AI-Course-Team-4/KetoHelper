"""
🗃️ Repository 패턴 구현
- 데이터 접근 로직 추상화
- CRUD 작업 표준화
- 중복 제거 및 검증 로직
"""

import json
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from abc import ABC, abstractmethod

from ..models import (
    Restaurant, RestaurantCreate, RestaurantUpdate, RestaurantSearch,
    Menu, MenuCreate, MenuUpdate, MenuSearch,
    CrawlJob, CrawlJobCreate, CrawlJobUpdate, CrawlJobSearch, JobStatus
)
from ..utils.text_utils import calculate_restaurant_similarity, calculate_coordinate_distance
from ..utils.logger import get_logger, log_database_operation, log_duplicate_found
from .connection import get_database


class BaseRepository(ABC):
    """기본 Repository 추상 클래스"""
    
    def __init__(self):
        self.logger = get_logger(f"repo_{self.__class__.__name__.lower()}")
    
    @abstractmethod
    def get_table_name(self) -> str:
        """테이블 이름 반환"""
        pass
    
    async def _execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """쿼리 실행"""
        db = await get_database()
        return await db.execute_query(query, *args)
    
    async def _execute_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """단일 레코드 조회"""
        db = await get_database()
        return await db.execute_one(query, *args)
    
    async def _execute_write(self, query: str, *args) -> str:
        """쓰기 작업"""
        db = await get_database()
        return await db.execute_write(query, *args)


class RestaurantRepository(BaseRepository):
    """Restaurant 데이터 접근 레포지토리"""
    
    def get_table_name(self) -> str:
        return "restaurants"
    
    async def create(self, restaurant: RestaurantCreate) -> Restaurant:
        """식당 생성"""
        # 중복 검사
        duplicates = await self.find_duplicates(restaurant)
        if duplicates:
            existing = duplicates[0]
            log_duplicate_found(
                "restaurant", 
                f"{restaurant.name}@{restaurant.address_road}", 
                restaurant.source, 
                existing.source
            )
            
            # 기존 레코드 업데이트 (더 좋은 품질의 데이터로)
            if restaurant.dict().get('quality_score', 0) > existing.quality_score:
                return await self.update(existing.id, RestaurantUpdate(**restaurant.dict()))
            else:
                return existing
        
        # 새 레코드 생성
        query = """
            INSERT INTO restaurants (
                name, address_road, address_jibun, lat, lng, phone, homepage_url,
                category, cuisine_type, rating, review_count, business_hours,
                source, source_url, source_id, quality_score
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
            ) RETURNING id, created_at, updated_at
        """
        
        restaurant_dict = restaurant.dict()
        args = [
            restaurant_dict.get('name'),
            restaurant_dict.get('address_road'),
            restaurant_dict.get('address_jibun'),
            restaurant_dict.get('lat'),
            restaurant_dict.get('lng'),
            restaurant_dict.get('phone'),
            restaurant_dict.get('homepage_url'),
            restaurant_dict.get('category'),
            restaurant_dict.get('cuisine_type'),
            restaurant_dict.get('rating'),
            restaurant_dict.get('review_count', 0),
            restaurant_dict.get('business_hours'),
            restaurant_dict.get('source'),
            restaurant_dict.get('source_url'),
            restaurant_dict.get('source_id'),
            restaurant_dict.get('quality_score', 0),
        ]
        
        result = await self._execute_one(query, *args)
        if not result:
            raise Exception("식당 생성에 실패했습니다")
        
        # 생성된 레코드 반환
        created = Restaurant(**restaurant_dict, **result)
        
        log_database_operation("INSERT", "restaurants", 1)
        self.logger.info(f"식당 생성: {created.name} (ID: {created.id})")
        
        return created
    
    async def get_by_id(self, restaurant_id: UUID) -> Optional[Restaurant]:
        """ID로 식당 조회"""
        query = "SELECT * FROM restaurants WHERE id = $1"
        result = await self._execute_one(query, restaurant_id)
        
        if result:
            return Restaurant(**result)
        return None
    
    async def get_by_source_url(self, source: str, source_url: str) -> Optional[Restaurant]:
        """소스 URL로 식당 조회"""
        query = "SELECT * FROM restaurants WHERE source = $1 AND source_url = $2"
        result = await self._execute_one(query, source, source_url)
        
        if result:
            return Restaurant(**result)
        return None
    
    async def update(self, restaurant_id: UUID, update_data: RestaurantUpdate) -> Optional[Restaurant]:
        """식당 정보 업데이트"""
        # 업데이트할 필드만 추출
        update_dict = update_data.dict(exclude_unset=True, exclude_none=True)
        if not update_dict:
            return await self.get_by_id(restaurant_id)
        
        # 동적 쿼리 생성
        set_clauses = []
        values = []
        param_count = 1
        
        for field, value in update_dict.items():
            set_clauses.append(f"{field} = ${param_count}")
            values.append(value)
            param_count += 1
        
        values.append(restaurant_id)  # WHERE 조건용
        
        query = f"""
            UPDATE restaurants 
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE id = ${param_count}
            RETURNING *
        """
        
        result = await self._execute_one(query, *values)
        
        if result:
            updated = Restaurant(**result)
            log_database_operation("UPDATE", "restaurants", 1)
            self.logger.info(f"식당 업데이트: {updated.name} (ID: {restaurant_id})")
            return updated
        
        return None
    
    async def delete(self, restaurant_id: UUID) -> bool:
        """식당 삭제"""
        query = "DELETE FROM restaurants WHERE id = $1"
        result = await self._execute_write(query, restaurant_id)
        
        if "DELETE 1" in result:
            log_database_operation("DELETE", "restaurants", 1)
            self.logger.info(f"식당 삭제: ID {restaurant_id}")
            return True
        
        return False
    
    async def find_duplicates(self, restaurant: Union[Restaurant, RestaurantCreate]) -> List[Restaurant]:
        """중복 식당 검색"""
        candidates = []
        
        # 1. 정확한 이름 + 주소 매칭
        if hasattr(restaurant, 'name') and hasattr(restaurant, 'address_road') and restaurant.address_road:
            query = """
                SELECT * FROM restaurants 
                WHERE name = $1 AND address_road = $2
                LIMIT 5
            """
            results = await self._execute_query(query, restaurant.name, restaurant.address_road)
            candidates.extend([Restaurant(**r) for r in results])
        
        # 2. 전화번호 매칭
        if hasattr(restaurant, 'phone') and restaurant.phone:
            query = "SELECT * FROM restaurants WHERE phone = $1 LIMIT 5"
            results = await self._execute_query(query, restaurant.phone)
            candidates.extend([Restaurant(**r) for r in results])
        
        # 3. 좌표 기반 매칭 (반경 50m 이내)
        if (hasattr(restaurant, 'lat') and hasattr(restaurant, 'lng') and 
            restaurant.lat and restaurant.lng):
            query = """
                SELECT * FROM restaurants 
                WHERE lat IS NOT NULL AND lng IS NOT NULL
                AND ABS(lat - $1) < 0.001 AND ABS(lng - $2) < 0.001
                LIMIT 10
            """
            results = await self._execute_query(query, restaurant.lat, restaurant.lng)
            
            # 정확한 거리 계산
            for result in results:
                candidate = Restaurant(**result)
                distance = calculate_coordinate_distance(
                    restaurant.lat, restaurant.lng,
                    candidate.lat, candidate.lng
                )
                if distance <= 50:  # 50m 이내
                    candidates.append(candidate)
        
        # 중복 제거 및 유사도 계산
        unique_candidates = []
        seen_ids = set()
        
        restaurant_dict = restaurant.dict() if hasattr(restaurant, 'dict') else restaurant.__dict__
        
        for candidate in candidates:
            if candidate.id not in seen_ids:
                similarity = calculate_restaurant_similarity(restaurant_dict, candidate.dict())
                if similarity >= 0.8:  # 80% 이상 유사
                    unique_candidates.append(candidate)
                    seen_ids.add(candidate.id)
        
        return unique_candidates
    
    async def search(self, search_params: RestaurantSearch) -> Dict[str, Any]:
        """식당 검색"""
        conditions = []
        values = []
        param_count = 1
        
        # 검색 조건 구성
        if search_params.keyword:
            conditions.append(f"name ILIKE ${param_count}")
            values.append(f"%{search_params.keyword}%")
            param_count += 1
        
        if search_params.category:
            conditions.append(f"category = ${param_count}")
            values.append(search_params.category)
            param_count += 1
        
        if search_params.source:
            conditions.append(f"source = ${param_count}")
            values.append(search_params.source)
            param_count += 1
        
        if search_params.min_rating:
            conditions.append(f"rating >= ${param_count}")
            values.append(search_params.min_rating)
            param_count += 1
        
        if search_params.has_coordinates is not None:
            if search_params.has_coordinates:
                conditions.append("lat IS NOT NULL AND lng IS NOT NULL")
            else:
                conditions.append("lat IS NULL OR lng IS NULL")
        
        if search_params.min_quality_score:
            conditions.append(f"quality_score >= ${param_count}")
            values.append(search_params.min_quality_score)
            param_count += 1
        
        # 위치 기반 검색
        if (search_params.center_lat and search_params.center_lng and 
            search_params.radius_km):
            # 간단한 바운딩 박스 검색 (정확한 거리는 애플리케이션에서 계산)
            lat_range = search_params.radius_km / 111.0  # 대략 1도 = 111km
            lng_range = search_params.radius_km / (111.0 * 0.8)  # 위도 보정
            
            conditions.append(f"""
                lat BETWEEN ${param_count} AND ${param_count + 1}
                AND lng BETWEEN ${param_count + 2} AND ${param_count + 3}
            """)
            values.extend([
                search_params.center_lat - lat_range,
                search_params.center_lat + lat_range,
                search_params.center_lng - lng_range,
                search_params.center_lng + lng_range
            ])
            param_count += 4
        
        # WHERE 절 구성
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # 정렬
        sort_direction = "DESC" if search_params.sort_desc else "ASC"
        order_clause = f"ORDER BY {search_params.sort_by} {sort_direction}"
        
        # 페이지네이션
        offset = (search_params.page - 1) * search_params.size
        limit_clause = f"LIMIT {search_params.size} OFFSET {offset}"
        
        # 총 개수 조회
        count_query = f"SELECT COUNT(*) as total FROM restaurants {where_clause}"
        count_result = await self._execute_one(count_query, *values)
        total_count = count_result['total'] if count_result else 0
        
        # 데이터 조회
        data_query = f"""
            SELECT * FROM restaurants 
            {where_clause} 
            {order_clause} 
            {limit_clause}
        """
        
        results = await self._execute_query(data_query, *values)
        restaurants = [Restaurant(**r) for r in results]
        
        # 위치 기반 검색 시 정확한 거리 계산 및 필터링
        if (search_params.center_lat and search_params.center_lng and 
            search_params.radius_km):
            filtered_restaurants = []
            for restaurant in restaurants:
                if restaurant.lat and restaurant.lng:
                    distance = calculate_coordinate_distance(
                        search_params.center_lat, search_params.center_lng,
                        restaurant.lat, restaurant.lng
                    ) / 1000  # km로 변환
                    
                    if distance <= search_params.radius_km:
                        filtered_restaurants.append(restaurant)
            
            restaurants = filtered_restaurants
        
        return {
            "items": restaurants,
            "total": total_count,
            "page": search_params.page,
            "size": search_params.size,
            "total_pages": (total_count + search_params.size - 1) // search_params.size
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """식당 통계"""
        stats_query = """
            SELECT 
                COUNT(*) as total_count,
                COUNT(CASE WHEN lat IS NOT NULL AND lng IS NOT NULL THEN 1 END) as geocoded_count,
                COUNT(CASE WHEN quality_score >= 80 THEN 1 END) as high_quality_count,
                ROUND(AVG(rating), 2) as avg_rating,
                ROUND(AVG(quality_score), 2) as avg_quality_score
            FROM restaurants
        """
        
        result = await self._execute_one(stats_query)
        if not result:
            return {}
        
        # 소스별 통계
        source_query = "SELECT source, COUNT(*) as count FROM restaurants GROUP BY source"
        source_results = await self._execute_query(source_query)
        by_source = {r['source']: r['count'] for r in source_results}
        
        # 카테고리별 통계
        category_query = """
            SELECT category, COUNT(*) as count 
            FROM restaurants 
            WHERE category IS NOT NULL 
            GROUP BY category 
            ORDER BY count DESC
        """
        category_results = await self._execute_query(category_query)
        by_category = {r['category']: r['count'] for r in category_results}
        
        return {
            **result,
            "by_source": by_source,
            "by_category": by_category,
            "last_updated": datetime.utcnow()
        }


class MenuRepository(BaseRepository):
    """Menu 데이터 접근 레포지토리"""
    
    def get_table_name(self) -> str:
        return "menus"
    
    async def create(self, menu: MenuCreate) -> Menu:
        """메뉴 생성"""
        query = """
            INSERT INTO menus (
                restaurant_id, name, price, currency, description,
                category, is_signature, is_recommended, image_url,
                popularity_score, order_count
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            ) RETURNING id, created_at, updated_at
        """
        
        menu_dict = menu.dict()
        args = [
            menu_dict.get('restaurant_id'),
            menu_dict.get('name'),
            menu_dict.get('price'),
            menu_dict.get('currency', 'KRW'),
            menu_dict.get('description'),
            menu_dict.get('category'),
            menu_dict.get('is_signature', False),
            menu_dict.get('is_recommended', False),
            menu_dict.get('image_url'),
            menu_dict.get('popularity_score', 0),
            menu_dict.get('order_count', 0),
        ]
        
        try:
            result = await self._execute_one(query, *args)
            if not result:
                raise Exception("메뉴 생성에 실패했습니다")
            
            created = Menu(**menu_dict, **result)
            
            log_database_operation("INSERT", "menus", 1)
            self.logger.info(f"메뉴 생성: {created.name} (ID: {created.id})")
            
            return created
            
        except Exception as e:
            # 중복 키 에러 처리 (restaurant_id + name 유니크 제약)
            if "unique constraint" in str(e).lower():
                # 기존 메뉴 조회
                existing = await self.get_by_restaurant_and_name(
                    menu.restaurant_id, menu.name
                )
                if existing:
                    self.logger.info(f"중복 메뉴 발견: {menu.name}")
                    return existing
            
            raise e
    
    async def get_by_id(self, menu_id: UUID) -> Optional[Menu]:
        """ID로 메뉴 조회"""
        query = "SELECT * FROM menus WHERE id = $1"
        result = await self._execute_one(query, menu_id)
        
        if result:
            return Menu(**result)
        return None
    
    async def get_by_restaurant_and_name(self, restaurant_id: UUID, name: str) -> Optional[Menu]:
        """식당 ID와 메뉴명으로 조회"""
        query = "SELECT * FROM menus WHERE restaurant_id = $1 AND name = $2"
        result = await self._execute_one(query, restaurant_id, name)
        
        if result:
            return Menu(**result)
        return None
    
    async def get_by_restaurant(self, restaurant_id: UUID) -> List[Menu]:
        """식당별 메뉴 목록"""
        query = "SELECT * FROM menus WHERE restaurant_id = $1 ORDER BY name"
        results = await self._execute_query(query, restaurant_id)
        
        return [Menu(**r) for r in results]
    
    async def search(self, search_params: MenuSearch) -> Dict[str, Any]:
        """메뉴 검색"""
        conditions = []
        values = []
        param_count = 1
        
        # 검색 조건 구성
        if search_params.restaurant_id:
            conditions.append(f"restaurant_id = ${param_count}")
            values.append(search_params.restaurant_id)
            param_count += 1
        
        if search_params.keyword:
            conditions.append(f"name ILIKE ${param_count}")
            values.append(f"%{search_params.keyword}%")
            param_count += 1
        
        if search_params.category:
            conditions.append(f"category = ${param_count}")
            values.append(search_params.category)
            param_count += 1
        
        if search_params.min_price:
            conditions.append(f"price >= ${param_count}")
            values.append(search_params.min_price)
            param_count += 1
        
        if search_params.max_price:
            conditions.append(f"price <= ${param_count}")
            values.append(search_params.max_price)
            param_count += 1
        
        if search_params.is_signature is not None:
            conditions.append(f"is_signature = ${param_count}")
            values.append(search_params.is_signature)
            param_count += 1
        
        if search_params.is_recommended is not None:
            conditions.append(f"is_recommended = ${param_count}")
            values.append(search_params.is_recommended)
            param_count += 1
        
        if search_params.has_image is not None:
            if search_params.has_image:
                conditions.append("image_url IS NOT NULL")
            else:
                conditions.append("image_url IS NULL")
        
        # 쿼리 실행 (RestaurantRepository와 유사한 로직)
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        sort_direction = "DESC" if search_params.sort_desc else "ASC"
        order_clause = f"ORDER BY {search_params.sort_by} {sort_direction}"
        offset = (search_params.page - 1) * search_params.size
        limit_clause = f"LIMIT {search_params.size} OFFSET {offset}"
        
        # 총 개수 및 데이터 조회
        count_query = f"SELECT COUNT(*) as total FROM menus {where_clause}"
        count_result = await self._execute_one(count_query, *values)
        total_count = count_result['total'] if count_result else 0
        
        data_query = f"SELECT * FROM menus {where_clause} {order_clause} {limit_clause}"
        results = await self._execute_query(data_query, *values)
        menus = [Menu(**r) for r in results]
        
        return {
            "items": menus,
            "total": total_count,
            "page": search_params.page,
            "size": search_params.size,
            "total_pages": (total_count + search_params.size - 1) // search_params.size
        }


class CrawlJobRepository(BaseRepository):
    """CrawlJob 데이터 접근 레포지토리"""
    
    def get_table_name(self) -> str:
        return "crawl_jobs"
    
    async def create(self, job: CrawlJobCreate) -> CrawlJob:
        """크롤링 작업 생성"""
        query = """
            INSERT INTO crawl_jobs (
                job_type, site, url, keyword, status, priority,
                max_attempts, config, metadata, scheduled_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
            ) RETURNING id, created_at, updated_at
        """
        
        job_dict = job.dict()
        args = [
            job_dict.get('job_type'),
            job_dict.get('site'),
            job_dict.get('url'),
            job_dict.get('keyword'),
            job_dict.get('status', JobStatus.QUEUED),
            job_dict.get('priority', 0),
            job_dict.get('max_attempts', 3),
            json.dumps(job_dict.get('config')) if job_dict.get('config') else None,
            json.dumps(job_dict.get('metadata')) if job_dict.get('metadata') else None,
            job_dict.get('scheduled_at'),
        ]
        
        result = await self._execute_one(query, *args)
        if not result:
            raise Exception("크롤링 작업 생성에 실패했습니다")
        
        created = CrawlJob(**job_dict, **result)
        
        log_database_operation("INSERT", "crawl_jobs", 1)
        self.logger.info(f"크롤링 작업 생성: {created.job_type} - {created.site}")
        
        return created
    
    async def get_by_id(self, job_id: UUID) -> Optional[CrawlJob]:
        """ID로 작업 조회"""
        query = "SELECT * FROM crawl_jobs WHERE id = $1"
        result = await self._execute_one(query, job_id)
        
        if result:
            # JSON 필드 파싱
            if result.get('config'):
                result['config'] = json.loads(result['config'])
            if result.get('metadata'):
                result['metadata'] = json.loads(result['metadata'])
            
            return CrawlJob(**result)
        return None
    
    async def get_next_jobs(self, limit: int = 10) -> List[CrawlJob]:
        """다음 실행할 작업들 조회"""
        query = """
            SELECT * FROM crawl_jobs 
            WHERE status = 'queued' AND scheduled_at <= NOW()
            ORDER BY priority DESC, scheduled_at ASC
            LIMIT $1
        """
        
        results = await self._execute_query(query, limit)
        jobs = []
        
        for result in results:
            # JSON 필드 파싱
            if result.get('config'):
                result['config'] = json.loads(result['config'])
            if result.get('metadata'):
                result['metadata'] = json.loads(result['metadata'])
            
            jobs.append(CrawlJob(**result))
        
        return jobs
    
    async def update_status(self, job_id: UUID, status: JobStatus, 
                           error_code: str = None, error_message: str = None) -> bool:
        """작업 상태 업데이트"""
        now = datetime.utcnow()
        
        if status == JobStatus.RUNNING:
            query = """
                UPDATE crawl_jobs 
                SET status = $1, started_at = $2, updated_at = $3
                WHERE id = $4
            """
            args = [status, now, now, job_id]
            
        elif status == JobStatus.COMPLETED:
            query = """
                UPDATE crawl_jobs 
                SET status = $1, completed_at = $2, updated_at = $3
                WHERE id = $4
            """
            args = [status, now, now, job_id]
            
        elif status == JobStatus.FAILED:
            query = """
                UPDATE crawl_jobs 
                SET status = $1, attempts = attempts + 1, 
                    last_error_code = $2, last_error_message = $3,
                    last_error_at = $4, updated_at = $5
                WHERE id = $6
            """
            args = [status, error_code, error_message, now, now, job_id]
            
        else:
            query = """
                UPDATE crawl_jobs 
                SET status = $1, updated_at = $2
                WHERE id = $3
            """
            args = [status, now, job_id]
        
        result = await self._execute_write(query, *args)
        return "UPDATE 1" in result


# 전역 레포지토리 인스턴스
_restaurant_repo = None
_menu_repo = None
_crawl_job_repo = None


def get_restaurant_repository() -> RestaurantRepository:
    """RestaurantRepository 싱글톤 반환"""
    global _restaurant_repo
    if _restaurant_repo is None:
        _restaurant_repo = RestaurantRepository()
    return _restaurant_repo


def get_menu_repository() -> MenuRepository:
    """MenuRepository 싱글톤 반환"""
    global _menu_repo
    if _menu_repo is None:
        _menu_repo = MenuRepository()
    return _menu_repo


def get_crawl_job_repository() -> CrawlJobRepository:
    """CrawlJobRepository 싱글톤 반환"""
    global _crawl_job_repo
    if _crawl_job_repo is None:
        _crawl_job_repo = CrawlJobRepository()
    return _crawl_job_repo