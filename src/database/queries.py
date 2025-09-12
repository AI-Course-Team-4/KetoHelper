"""
📝 SQL 쿼리 모음
- 자주 사용되는 쿼리 정의
- 복잡한 쿼리 관리
- 쿼리 버전 관리
"""

from typing import Dict, Any


class RestaurantQueries:
    """Restaurant 관련 쿼리들"""
    
    # 기본 CRUD
    CREATE = """
        INSERT INTO restaurants (
            name, address_road, address_jibun, lat, lng, phone, homepage_url,
            category, cuisine_type, rating, review_count, business_hours,
            source, source_url, source_id, quality_score
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
        ) RETURNING *
    """
    
    GET_BY_ID = "SELECT * FROM restaurants WHERE id = $1"
    
    GET_BY_SOURCE_URL = "SELECT * FROM restaurants WHERE source = $1 AND source_url = $2"
    
    # 중복 검색
    FIND_BY_NAME_ADDRESS = """
        SELECT * FROM restaurants 
        WHERE name = $1 AND address_road = $2
        LIMIT 5
    """
    
    FIND_BY_PHONE = "SELECT * FROM restaurants WHERE phone = $1 LIMIT 5"
    
    FIND_BY_COORDINATES = """
        SELECT *, 
        (6371 * acos(cos(radians($1)) * cos(radians(lat)) * 
         cos(radians(lng) - radians($2)) + sin(radians($1)) * 
         sin(radians(lat)))) as distance
        FROM restaurants 
        WHERE lat IS NOT NULL AND lng IS NOT NULL
        HAVING distance <= $3
        ORDER BY distance
        LIMIT 10
    """
    
    # 통계 쿼리
    BASIC_STATS = """
        SELECT 
            COUNT(*) as total_count,
            COUNT(CASE WHEN lat IS NOT NULL AND lng IS NOT NULL THEN 1 END) as geocoded_count,
            COUNT(CASE WHEN quality_score >= 80 THEN 1 END) as high_quality_count,
            ROUND(AVG(rating), 2) as avg_rating,
            ROUND(AVG(quality_score), 2) as avg_quality_score,
            MAX(created_at) as last_added
        FROM restaurants
    """
    
    STATS_BY_SOURCE = """
        SELECT source, 
               COUNT(*) as count,
               ROUND(AVG(quality_score), 2) as avg_quality,
               COUNT(CASE WHEN lat IS NOT NULL AND lng IS NOT NULL THEN 1 END) as geocoded
        FROM restaurants 
        GROUP BY source 
        ORDER BY count DESC
    """
    
    STATS_BY_CATEGORY = """
        SELECT category, 
               COUNT(*) as count,
               ROUND(AVG(rating), 2) as avg_rating
        FROM restaurants 
        WHERE category IS NOT NULL 
        GROUP BY category 
        ORDER BY count DESC
    """
    
    # 검색 쿼리 (기본)
    SEARCH_BASE = """
        SELECT * FROM restaurants 
        WHERE ($1::text IS NULL OR name ILIKE '%' || $1 || '%')
          AND ($2::text IS NULL OR category = $2)
          AND ($3::text IS NULL OR source = $3)
          AND ($4::numeric IS NULL OR rating >= $4)
          AND ($5::boolean IS NULL OR 
               ($5 = true AND lat IS NOT NULL AND lng IS NOT NULL) OR
               ($5 = false AND (lat IS NULL OR lng IS NULL)))
          AND ($6::integer IS NULL OR quality_score >= $6)
    """
    
    # 고급 검색
    SEARCH_WITH_DISTANCE = """
        SELECT *, 
        (6371 * acos(cos(radians($7)) * cos(radians(lat)) * 
         cos(radians(lng) - radians($8)) + sin(radians($7)) * 
         sin(radians(lat)))) as distance
        FROM restaurants 
        WHERE ($1::text IS NULL OR name ILIKE '%' || $1 || '%')
          AND ($2::text IS NULL OR category = $2)
          AND ($3::text IS NULL OR source = $3)
          AND ($4::numeric IS NULL OR rating >= $4)
          AND ($5::boolean IS NULL OR 
               ($5 = true AND lat IS NOT NULL AND lng IS NOT NULL) OR
               ($5 = false AND (lat IS NULL OR lng IS NULL)))
          AND ($6::integer IS NULL OR quality_score >= $6)
          AND lat IS NOT NULL AND lng IS NOT NULL
        HAVING distance <= $9
        ORDER BY distance
    """
    
    # 데이터 품질 분석
    QUALITY_ANALYSIS = """
        SELECT 
            CASE 
                WHEN quality_score >= 80 THEN 'High'
                WHEN quality_score >= 60 THEN 'Medium'
                ELSE 'Low'
            END as quality_grade,
            COUNT(*) as count,
            ROUND(AVG(quality_score), 2) as avg_score,
            COUNT(CASE WHEN lat IS NOT NULL AND lng IS NOT NULL THEN 1 END) as with_coords,
            COUNT(CASE WHEN phone IS NOT NULL THEN 1 END) as with_phone
        FROM restaurants 
        GROUP BY quality_grade
        ORDER BY avg_score DESC
    """


class MenuQueries:
    """Menu 관련 쿼리들"""
    
    # 기본 CRUD
    CREATE = """
        INSERT INTO menus (
            restaurant_id, name, price, currency, description,
            category, is_signature, is_recommended, image_url,
            popularity_score, order_count
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        ) RETURNING *
    """
    
    GET_BY_ID = "SELECT * FROM menus WHERE id = $1"
    
    GET_BY_RESTAURANT = """
        SELECT * FROM menus 
        WHERE restaurant_id = $1 
        ORDER BY is_signature DESC, name ASC
    """
    
    GET_BY_RESTAURANT_AND_NAME = """
        SELECT * FROM menus 
        WHERE restaurant_id = $1 AND name = $2
    """
    
    # 통계 쿼리
    MENU_STATS = """
        SELECT 
            COUNT(*) as total_count,
            COUNT(CASE WHEN price IS NOT NULL THEN 1 END) as with_price,
            COUNT(CASE WHEN is_signature THEN 1 END) as signature_count,
            COUNT(CASE WHEN is_recommended THEN 1 END) as recommended_count,
            COUNT(CASE WHEN image_url IS NOT NULL THEN 1 END) as with_image,
            ROUND(AVG(price), 0) as avg_price,
            MIN(price) as min_price,
            MAX(price) as max_price
        FROM menus
        WHERE price > 0
    """
    
    MENU_STATS_BY_CATEGORY = """
        SELECT category,
               COUNT(*) as count,
               ROUND(AVG(price), 0) as avg_price,
               COUNT(CASE WHEN is_signature THEN 1 END) as signature_count
        FROM menus 
        WHERE category IS NOT NULL AND price > 0
        GROUP BY category 
        ORDER BY count DESC
    """
    
    # 가격대별 분석
    PRICE_DISTRIBUTION = """
        SELECT 
            CASE 
                WHEN price <= 5000 THEN '저가 (5천원 이하)'
                WHEN price <= 15000 THEN '중가 (5천원-1만5천원)'
                WHEN price <= 30000 THEN '고가 (1만5천원-3만원)'
                ELSE '최고가 (3만원 이상)'
            END as price_range,
            COUNT(*) as count,
            ROUND(AVG(price), 0) as avg_price
        FROM menus 
        WHERE price > 0
        GROUP BY price_range
        ORDER BY avg_price ASC
    """
    
    # 인기 메뉴 조회
    TOP_SIGNATURE_MENUS = """
        SELECT m.*, r.name as restaurant_name, r.category as restaurant_category
        FROM menus m
        JOIN restaurants r ON m.restaurant_id = r.id
        WHERE m.is_signature = true
        ORDER BY m.popularity_score DESC, r.rating DESC
        LIMIT $1
    """
    
    # 식당별 메뉴 통계
    RESTAURANT_MENU_STATS = """
        SELECT 
            restaurant_id,
            COUNT(*) as menu_count,
            COUNT(CASE WHEN price IS NOT NULL THEN 1 END) as with_price_count,
            ROUND(AVG(price), 0) as avg_price,
            COUNT(CASE WHEN is_signature THEN 1 END) as signature_count
        FROM menus
        GROUP BY restaurant_id
        HAVING COUNT(*) >= $1
        ORDER BY menu_count DESC
    """


class CrawlJobQueries:
    """CrawlJob 관련 쿼리들"""
    
    # 기본 CRUD
    CREATE = """
        INSERT INTO crawl_jobs (
            job_type, site, url, keyword, status, priority,
            max_attempts, config, metadata, scheduled_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
        ) RETURNING *
    """
    
    GET_BY_ID = "SELECT * FROM crawl_jobs WHERE id = $1"
    
    # 작업 큐 관련
    GET_NEXT_JOBS = """
        SELECT * FROM crawl_jobs 
        WHERE status = 'queued' 
          AND scheduled_at <= NOW()
          AND attempts < max_attempts
        ORDER BY priority DESC, scheduled_at ASC
        LIMIT $1
    """
    
    GET_RETRYABLE_JOBS = """
        SELECT * FROM crawl_jobs 
        WHERE status = 'failed' 
          AND attempts < max_attempts
          AND last_error_code != 'validation_error'
        ORDER BY last_error_at ASC
        LIMIT $1
    """
    
    # 상태 업데이트
    UPDATE_TO_RUNNING = """
        UPDATE crawl_jobs 
        SET status = 'running', started_at = NOW(), updated_at = NOW()
        WHERE id = $1 AND status = 'queued'
    """
    
    UPDATE_TO_COMPLETED = """
        UPDATE crawl_jobs 
        SET status = 'completed', completed_at = NOW(), updated_at = NOW()
        WHERE id = $1
    """
    
    UPDATE_TO_FAILED = """
        UPDATE crawl_jobs 
        SET status = 'failed', attempts = attempts + 1,
            last_error_code = $2, last_error_message = $3,
            last_error_at = NOW(), updated_at = NOW()
        WHERE id = $1
    """
    
    # 통계 쿼리
    JOB_STATS = """
        SELECT 
            COUNT(*) as total_count,
            COUNT(CASE WHEN status = 'queued' THEN 1 END) as queued_count,
            COUNT(CASE WHEN status = 'running' THEN 1 END) as running_count,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
            COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_count,
            COUNT(CASE WHEN status = 'failed' AND attempts < max_attempts THEN 1 END) as retryable_count
        FROM crawl_jobs
    """
    
    JOB_STATS_BY_SITE = """
        SELECT site,
               COUNT(*) as total,
               COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
               COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
               ROUND(
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*), 2
               ) as success_rate
        FROM crawl_jobs 
        GROUP BY site
        ORDER BY total DESC
    """
    
    JOB_PERFORMANCE = """
        SELECT 
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
            AVG(EXTRACT(EPOCH FROM (started_at - scheduled_at))) as avg_wait_seconds,
            COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END) as completed_jobs
        FROM crawl_jobs
        WHERE started_at IS NOT NULL
    """
    
    # 에러 분석
    ERROR_ANALYSIS = """
        SELECT 
            last_error_code,
            COUNT(*) as count,
            COUNT(DISTINCT site) as affected_sites,
            MAX(last_error_at) as last_occurrence
        FROM crawl_jobs 
        WHERE last_error_code IS NOT NULL
        GROUP BY last_error_code
        ORDER BY count DESC
    """
    
    # 작업 정리
    CLEANUP_OLD_COMPLETED = """
        DELETE FROM crawl_jobs 
        WHERE status = 'completed' 
          AND completed_at < NOW() - INTERVAL '$1 days'
    """
    
    CLEANUP_OLD_FAILED = """
        DELETE FROM crawl_jobs 
        WHERE status = 'failed' 
          AND attempts >= max_attempts
          AND last_error_at < NOW() - INTERVAL '$1 days'
    """


class AnalyticsQueries:
    """분석용 복합 쿼리들"""
    
    # 크롤링 대시보드
    CRAWLING_DASHBOARD = """
        SELECT 
            r.source,
            COUNT(r.*) as restaurant_count,
            COUNT(m.*) as menu_count,
            COUNT(CASE WHEN r.lat IS NOT NULL AND r.lng IS NOT NULL THEN 1 END) as geocoded_count,
            ROUND(AVG(r.quality_score), 2) as avg_quality,
            MAX(r.created_at) as last_crawled
        FROM restaurants r
        LEFT JOIN menus m ON r.id = m.restaurant_id
        GROUP BY r.source
        ORDER BY restaurant_count DESC
    """
    
    # 데이터 품질 리포트
    DATA_QUALITY_REPORT = """
        WITH restaurant_quality AS (
            SELECT 
                source,
                COUNT(*) as total,
                COUNT(CASE WHEN quality_score >= 80 THEN 1 END) as high_quality,
                COUNT(CASE WHEN lat IS NOT NULL AND lng IS NOT NULL THEN 1 END) as with_coords,
                COUNT(CASE WHEN phone IS NOT NULL THEN 1 END) as with_phone,
                ROUND(AVG(quality_score), 2) as avg_quality
            FROM restaurants
            GROUP BY source
        ),
        menu_quality AS (
            SELECT 
                r.source,
                COUNT(m.*) as menu_count,
                COUNT(CASE WHEN m.price IS NOT NULL THEN 1 END) as with_price,
                COUNT(CASE WHEN m.image_url IS NOT NULL THEN 1 END) as with_image
            FROM restaurants r
            LEFT JOIN menus m ON r.id = m.restaurant_id
            GROUP BY r.source
        )
        SELECT 
            rq.*,
            mq.menu_count,
            mq.with_price,
            mq.with_image,
            ROUND(mq.menu_count::numeric / rq.total, 2) as avg_menus_per_restaurant
        FROM restaurant_quality rq
        LEFT JOIN menu_quality mq ON rq.source = mq.source
        ORDER BY rq.total DESC
    """
    
    # 지역별 분석 (좌표 기반)
    REGIONAL_ANALYSIS = """
        SELECT 
            CASE 
                WHEN lat BETWEEN 37.5 AND 37.6 AND lng BETWEEN 126.9 AND 127.1 THEN '강남/서초'
                WHEN lat BETWEEN 37.5 AND 37.6 AND lng BETWEEN 126.8 AND 126.9 THEN '마포/용산'
                WHEN lat BETWEEN 37.6 AND 37.7 AND lng BETWEEN 126.9 AND 127.1 THEN '종로/중구'
                ELSE '기타 지역'
            END as region,
            COUNT(*) as restaurant_count,
            ROUND(AVG(rating), 2) as avg_rating,
            COUNT(DISTINCT category) as category_diversity
        FROM restaurants 
        WHERE lat IS NOT NULL AND lng IS NOT NULL
        GROUP BY region
        ORDER BY restaurant_count DESC
    """


# 쿼리 실행 헬퍼 함수들
def get_query(query_class: str, query_name: str) -> str:
    """쿼리 클래스에서 특정 쿼리 반환"""
    query_classes = {
        'restaurant': RestaurantQueries,
        'menu': MenuQueries,
        'crawl_job': CrawlJobQueries,
        'analytics': AnalyticsQueries,
    }
    
    if query_class not in query_classes:
        raise ValueError(f"Unknown query class: {query_class}")
    
    cls = query_classes[query_class]
    if not hasattr(cls, query_name.upper()):
        raise ValueError(f"Unknown query: {query_name} in {query_class}")
    
    return getattr(cls, query_name.upper())


def format_search_query(base_query: str, conditions: list, order_by: str = "created_at", 
                       limit: int = 20, offset: int = 0) -> str:
    """검색 쿼리 포맷팅"""
    where_clause = ""
    if conditions:
        where_clause = f"WHERE {' AND '.join(conditions)}"
    
    return f"""
        {base_query}
        {where_clause}
        ORDER BY {order_by}
        LIMIT {limit} OFFSET {offset}
    """


if __name__ == "__main__":
    # 쿼리 테스트
    print("=== Restaurant Queries ===")
    print(f"CREATE: {RestaurantQueries.CREATE[:100]}...")
    print(f"STATS: {RestaurantQueries.BASIC_STATS[:100]}...")
    
    print("\n=== Menu Queries ===")
    print(f"CREATE: {MenuQueries.CREATE[:100]}...")
    print(f"STATS: {MenuQueries.MENU_STATS[:100]}...")
    
    print("\n=== CrawlJob Queries ===")
    print(f"CREATE: {CrawlJobQueries.CREATE[:100]}...")
    print(f"NEXT_JOBS: {CrawlJobQueries.GET_NEXT_JOBS[:100]}...")
    
    # 헬퍼 함수 테스트
    try:
        query = get_query('restaurant', 'basic_stats')
        print(f"\n헬퍼 함수 테스트: {query[:100]}...")
    except Exception as e:
        print(f"헬퍼 함수 에러: {e}")
    
    print("\n✅ 쿼리 테스트 완료!")