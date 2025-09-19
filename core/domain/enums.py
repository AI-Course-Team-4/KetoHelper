"""
도메인 열거형 정의
"""

from core.domain.base import BaseEnum

class CarbBase(BaseEnum):
    """탄수화물 베이스 타입"""
    RICE = "rice"                    # 밥류
    NOODLE = "noodle"               # 면류
    BREAD = "bread"                 # 빵류
    NONE = "none"                   # 탄수화물 없음
    KONJAC_RICE = "konjac_rice"     # 곤약밥
    CAULI_RICE = "cauli_rice"       # 콜리플라워 라이스
    TOFU_NOODLE = "tofu_noodle"     # 두부면
    UNKNOWN = "unknown"             # 알 수 없음

class SourceType(BaseEnum):
    """데이터 소스 타입"""
    DININGCODE = "diningcode"
    SIKSIN = "siksin"
    MANGOPLATE = "mangoplate"
    YOGIYO = "yogiyo"
    MANUAL = "manual"

class MenuCategory(BaseEnum):
    """메뉴 카테고리"""
    MAIN = "main"                   # 메인 메뉴
    SIDE = "side"                   # 사이드 메뉴
    DRINK = "drink"                 # 음료
    DESSERT = "dessert"             # 디저트
    SET = "set"                     # 세트 메뉴
    UNKNOWN = "unknown"

class IngredientRole(BaseEnum):
    """재료 역할"""
    MAIN = "main"                   # 주재료
    AUX = "aux"                     # 부재료
    SEASONING = "seasoning"         # 조미료
    GARNISH = "garnish"             # 고명

class IngredientSource(BaseEnum):
    """재료 정보 소스"""
    RULE = "rule"                   # 룰 기반 추정
    MANUAL = "manual"               # 수동 입력
    LLM = "llm"                     # LLM 추정
    CRAWLED = "crawled"             # 크롤링 수집

class ReviewStatus(BaseEnum):
    """검토 상태"""
    PENDING = "pending"             # 검토 대기
    IN_PROGRESS = "in_progress"     # 검토 중
    APPROVED = "approved"           # 승인됨
    REJECTED = "rejected"           # 거부됨
    NEEDS_REVISION = "needs_revision"  # 수정 필요

class CrawlJobStatus(BaseEnum):
    """크롤링 작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CrawlJobType(BaseEnum):
    """크롤링 작업 타입"""
    FULL = "full"                   # 전체 크롤링
    INCREMENTAL = "incremental"     # 증분 크롤링
    MANUAL = "manual"               # 수동 크롤링
    RETRY = "retry"                 # 재시도

class PriceRange(BaseEnum):
    """가격대"""
    LOW = "low"                     # 저렴 (1만원 미만)
    MEDIUM = "medium"               # 보통 (1-3만원)
    HIGH = "high"                   # 비쌈 (3만원 이상)
    PREMIUM = "premium"             # 프리미엄 (5만원 이상)

class SpiceLevel(BaseEnum):
    """매운 정도"""
    NONE = 0                        # 안매움
    MILD = 1                        # 순함
    MEDIUM = 2                      # 보통
    HOT = 3                         # 매움
    VERY_HOT = 4                    # 아주 매움
    EXTREME = 5                     # 극강매움