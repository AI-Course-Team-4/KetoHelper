"""
⚙️ 데이터 파이프라인
- 단계별 데이터 처리
- 정규화 및 검증
- 변환 및 enrichment
- 에러 처리 및 복구
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..models import RestaurantCreate, MenuCreate
from ..utils.logger import get_logger
from ..utils.text_utils import (
    normalize_restaurant_name, normalize_address, 
    extract_phone_number, extract_price, calculate_similarity
)


class PipelineStageType(Enum):
    """파이프라인 단계 유형"""
    VALIDATION = "validation"
    NORMALIZATION = "normalization"
    ENRICHMENT = "enrichment"
    DEDUPLICATION = "deduplication"
    QUALITY_CHECK = "quality_check"


@dataclass
class PipelineResult:
    """파이프라인 결과"""
    success: bool
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    stage_results: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}
        if self.stage_results is None:
            self.stage_results = {}


class PipelineStage(ABC):
    """파이프라인 단계 기본 클래스"""
    
    def __init__(self, name: str, stage_type: PipelineStageType):
        self.name = name
        self.stage_type = stage_type
        self.logger = get_logger(f"pipeline_{name}")
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "warnings": 0
        }
    
    @abstractmethod
    async def process(self, data: Any) -> PipelineResult:
        """데이터 처리"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """단계별 통계"""
        return {
            "name": self.name,
            "type": self.stage_type.value,
            **self.stats
        }


class ValidationStage(PipelineStage):
    """데이터 검증 단계"""
    
    def __init__(self, name: str = "validation"):
        super().__init__(name, PipelineStageType.VALIDATION)
        
        # 검증 규칙
        self.required_restaurant_fields = ['name']
        self.required_menu_fields = ['name']
        self.phone_pattern = r'^[0-9\-\+\(\)\s]+$'
        self.price_range = (0, 1000000)  # 0원 ~ 100만원
        self.rating_range = (0, 5)
    
    async def process(self, data: Any) -> PipelineResult:
        """데이터 검증"""
        self.stats["processed"] += 1
        errors = []
        warnings = []
        
        try:
            if isinstance(data, dict):
                # 단일 식당 데이터
                errors, warnings = await self._validate_restaurant_data(data)
                
            elif isinstance(data, list):
                # 여러 식당 데이터
                for i, item in enumerate(data):
                    item_errors, item_warnings = await self._validate_restaurant_data(item)
                    errors.extend([f"항목 {i}: {e}" for e in item_errors])
                    warnings.extend([f"항목 {i}: {w}" for w in item_warnings])
            
            if errors:
                self.stats["failed"] += 1
                return PipelineResult(success=False, data=data, errors=errors, warnings=warnings)
            else:
                self.stats["successful"] += 1
                if warnings:
                    self.stats["warnings"] += len(warnings)
                return PipelineResult(success=True, data=data, warnings=warnings)
                
        except Exception as e:
            self.stats["failed"] += 1
            return PipelineResult(success=False, data=data, errors=[str(e)])
    
    async def _validate_restaurant_data(self, data: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """식당 데이터 검증"""
        errors = []
        warnings = []
        
        # 필수 필드 검사
        for field in self.required_restaurant_fields:
            if field not in data or not data[field]:
                errors.append(f"필수 필드 누락: {field}")
        
        # 데이터 유형 및 범위 검사
        if 'rating' in data and data['rating']:
            try:
                rating = float(data['rating'])
                if not (self.rating_range[0] <= rating <= self.rating_range[1]):
                    warnings.append(f"평점 범위 초과: {rating}")
            except (ValueError, TypeError):
                warnings.append(f"평점 형식 오류: {data['rating']}")
        
        if 'phone' in data and data['phone']:
            import re
            if not re.match(self.phone_pattern, str(data['phone'])):
                warnings.append(f"전화번호 형식 의심: {data['phone']}")
        
        if 'lat' in data and data['lat']:
            try:
                lat = float(data['lat'])
                if not (-90 <= lat <= 90):
                    errors.append(f"위도 범위 오류: {lat}")
            except (ValueError, TypeError):
                errors.append(f"위도 형식 오류: {data['lat']}")
        
        if 'lng' in data and data['lng']:
            try:
                lng = float(data['lng'])
                if not (-180 <= lng <= 180):
                    errors.append(f"경도 범위 오류: {lng}")
            except (ValueError, TypeError):
                errors.append(f"경도 형식 오류: {data['lng']}")
        
        # 메뉴 데이터 검증 (있는 경우)
        if 'menus' in data and data['menus']:
            for i, menu in enumerate(data['menus']):
                menu_errors, menu_warnings = await self._validate_menu_data(menu)
                errors.extend([f"메뉴 {i}: {e}" for e in menu_errors])
                warnings.extend([f"메뉴 {i}: {w}" for w in menu_warnings])
        
        return errors, warnings
    
    async def _validate_menu_data(self, data: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """메뉴 데이터 검증"""
        errors = []
        warnings = []
        
        # 필수 필드 검사
        for field in self.required_menu_fields:
            if field not in data or not data[field]:
                errors.append(f"필수 필드 누락: {field}")
        
        # 가격 검사
        if 'price' in data and data['price']:
            try:
                price = int(data['price'])
                if not (self.price_range[0] <= price <= self.price_range[1]):
                    warnings.append(f"가격 범위 의심: {price}")
            except (ValueError, TypeError):
                warnings.append(f"가격 형식 오류: {data['price']}")
        
        return errors, warnings


class NormalizationStage(PipelineStage):
    """데이터 정규화 단계"""
    
    def __init__(self, name: str = "normalization"):
        super().__init__(name, PipelineStageType.NORMALIZATION)
    
    async def process(self, data: Any) -> PipelineResult:
        """데이터 정규화"""
        self.stats["processed"] += 1
        
        try:
            if isinstance(data, dict):
                normalized_data = await self._normalize_restaurant_data(data)
                
            elif isinstance(data, list):
                normalized_data = []
                for item in data:
                    normalized_item = await self._normalize_restaurant_data(item)
                    normalized_data.append(normalized_item)
            else:
                normalized_data = data
            
            self.stats["successful"] += 1
            return PipelineResult(success=True, data=normalized_data)
            
        except Exception as e:
            self.stats["failed"] += 1
            return PipelineResult(success=False, data=data, errors=[str(e)])
    
    async def _normalize_restaurant_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """식당 데이터 정규화"""
        normalized = data.copy()
        
        # 이름 정규화
        if 'name' in normalized and normalized['name']:
            normalized['name'] = normalize_restaurant_name(normalized['name'])
        
        # 주소 정규화
        if 'address_road' in normalized and normalized['address_road']:
            normalized['address_road'] = normalize_address(normalized['address_road'])
        
        if 'address_jibun' in normalized and normalized['address_jibun']:
            normalized['address_jibun'] = normalize_address(normalized['address_jibun'])
        
        # 전화번호 정규화
        if 'phone' in normalized and normalized['phone']:
            phone = extract_phone_number(str(normalized['phone']))
            if phone:
                normalized['phone'] = phone
        
        # 좌표 정규화
        for coord_field in ['lat', 'lng']:
            if coord_field in normalized and normalized[coord_field]:
                try:
                    normalized[coord_field] = float(normalized[coord_field])
                except (ValueError, TypeError):
                    normalized[coord_field] = None
        
        # 평점 정규화
        if 'rating' in normalized and normalized['rating']:
            try:
                rating = float(normalized['rating'])
                # 10점 만점을 5점 만점으로 변환
                if rating > 5:
                    rating = rating / 2
                normalized['rating'] = round(rating, 1)
            except (ValueError, TypeError):
                normalized['rating'] = None
        
        # 메뉴 데이터 정규화 (있는 경우)
        if 'menus' in normalized and normalized['menus']:
            normalized_menus = []
            for menu in normalized['menus']:
                normalized_menu = await self._normalize_menu_data(menu)
                normalized_menus.append(normalized_menu)
            normalized['menus'] = normalized_menus
        
        return normalized
    
    async def _normalize_menu_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """메뉴 데이터 정규화"""
        normalized = data.copy()
        
        # 메뉴명 정규화
        if 'name' in normalized and normalized['name']:
            normalized['name'] = normalized['name'].strip()
        
        # 가격 정규화
        if 'price' in normalized and normalized['price']:
            price = extract_price(str(normalized['price']))
            normalized['price'] = price
        
        # 설명 정규화
        if 'description' in normalized and normalized['description']:
            normalized['description'] = normalized['description'].strip()
        
        return normalized


class DeduplicationStage(PipelineStage):
    """중복 제거 단계"""
    
    def __init__(self, name: str = "deduplication", similarity_threshold: float = 0.8):
        super().__init__(name, PipelineStageType.DEDUPLICATION)
        self.similarity_threshold = similarity_threshold
    
    async def process(self, data: Any) -> PipelineResult:
        """중복 제거"""
        self.stats["processed"] += 1
        
        try:
            if isinstance(data, list):
                deduplicated_data, duplicates = await self._deduplicate_restaurants(data)
                
                metadata = {
                    "original_count": len(data),
                    "deduplicated_count": len(deduplicated_data),
                    "duplicates_removed": len(duplicates)
                }
                
                warnings = []
                if duplicates:
                    warnings.append(f"{len(duplicates)}개의 중복 항목 제거됨")
                
                self.stats["successful"] += 1
                return PipelineResult(
                    success=True,
                    data=deduplicated_data,
                    warnings=warnings,
                    metadata=metadata
                )
            else:
                # 단일 항목은 중복 제거 불필요
                self.stats["successful"] += 1
                return PipelineResult(success=True, data=data)
                
        except Exception as e:
            self.stats["failed"] += 1
            return PipelineResult(success=False, data=data, errors=[str(e)])
    
    async def _deduplicate_restaurants(self, restaurants: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """식당 중복 제거"""
        unique_restaurants = []
        duplicates = []
        
        for restaurant in restaurants:
            is_duplicate = False
            
            for existing in unique_restaurants:
                similarity = await self._calculate_restaurant_similarity(restaurant, existing)
                
                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    duplicates.append(restaurant)
                    
                    # 더 완전한 데이터로 업데이트
                    merged = await self._merge_restaurant_data(existing, restaurant)
                    # existing 위치의 데이터를 merged로 교체
                    idx = unique_restaurants.index(existing)
                    unique_restaurants[idx] = merged
                    break
            
            if not is_duplicate:
                unique_restaurants.append(restaurant)
        
        return unique_restaurants, duplicates
    
    async def _calculate_restaurant_similarity(self, r1: Dict[str, Any], r2: Dict[str, Any]) -> float:
        """식당간 유사도 계산"""
        name_sim = 0
        addr_sim = 0
        phone_sim = 0
        coord_sim = 0
        
        # 이름 유사도 (가중치: 0.4)
        if r1.get('name') and r2.get('name'):
            name_sim = calculate_similarity(r1['name'], r2['name']) * 0.4
        
        # 주소 유사도 (가중치: 0.3)
        if r1.get('address_road') and r2.get('address_road'):
            addr_sim = calculate_similarity(r1['address_road'], r2['address_road']) * 0.3
        
        # 전화번호 일치 (가중치: 0.2)
        if r1.get('phone') and r2.get('phone'):
            phone_sim = 0.2 if r1['phone'] == r2['phone'] else 0
        
        # 좌표 유사도 (가중치: 0.1)
        if (r1.get('lat') and r1.get('lng') and 
            r2.get('lat') and r2.get('lng')):
            distance = self._calculate_distance(
                r1['lat'], r1['lng'],
                r2['lat'], r2['lng']
            )
            # 100m 이내면 유사한 것으로 판단
            coord_sim = 0.1 if distance < 0.1 else 0
        
        return name_sim + addr_sim + phone_sim + coord_sim
    
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
    
    async def _merge_restaurant_data(self, base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """식당 데이터 병합 (더 완전한 정보로)"""
        merged = base.copy()
        
        # 빈 필드는 새 데이터로 채우기
        for key, value in new.items():
            if key not in merged or not merged[key]:
                if value:
                    merged[key] = value
            elif key == 'rating':
                # 평점은 더 높은 값으로
                try:
                    if float(value) > float(merged[key]):
                        merged[key] = value
                except (ValueError, TypeError):
                    pass
            elif key == 'review_count':
                # 리뷰 수는 더 많은 값으로
                try:
                    if int(value) > int(merged[key]):
                        merged[key] = value
                except (ValueError, TypeError):
                    pass
        
        return merged


class QualityCheckStage(PipelineStage):
    """데이터 품질 검사 단계"""
    
    def __init__(self, name: str = "quality_check", min_quality_score: int = 30):
        super().__init__(name, PipelineStageType.QUALITY_CHECK)
        self.min_quality_score = min_quality_score
    
    async def process(self, data: Any) -> PipelineResult:
        """품질 검사"""
        self.stats["processed"] += 1
        
        try:
            warnings = []
            
            if isinstance(data, dict):
                score = await self._calculate_quality_score(data)
                data['quality_score'] = score
                
                if score < self.min_quality_score:
                    warnings.append(f"품질 점수 낮음: {score}")
                
            elif isinstance(data, list):
                for item in data:
                    score = await self._calculate_quality_score(item)
                    item['quality_score'] = score
                    
                    if score < self.min_quality_score:
                        warnings.append(f"품질 점수 낮음 ({item.get('name', 'unknown')}): {score}")
            
            self.stats["successful"] += 1
            if warnings:
                self.stats["warnings"] += len(warnings)
            
            return PipelineResult(success=True, data=data, warnings=warnings)
            
        except Exception as e:
            self.stats["failed"] += 1
            return PipelineResult(success=False, data=data, errors=[str(e)])
    
    async def _calculate_quality_score(self, data: Dict[str, Any]) -> int:
        """품질 점수 계산 (0-100)"""
        score = 0
        
        # 필수 정보 (40점)
        if data.get('name'): score += 20
        if data.get('address_road'): score += 10
        if data.get('phone'): score += 10
        
        # 위치 정보 (20점)
        if data.get('lat') and data.get('lng'): score += 20
        
        # 평점/리뷰 정보 (20점)
        if data.get('rating'): score += 10
        if data.get('review_count'): score += 10
        
        # 메뉴 정보 (20점)
        menus = data.get('menus', [])
        if menus:
            score += min(len(menus) * 2, 15)  # 메뉴 개수
            if any(menu.get('price') for menu in menus): 
                score += 5  # 가격 정보
        
        return min(score, 100)


class DataPipeline:
    """데이터 파이프라인 메인 클래스"""
    
    def __init__(self, stages: List[PipelineStage] = None):
        self.logger = get_logger("data_pipeline")
        self.stages = stages or self._create_default_stages()
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
        }
    
    def _create_default_stages(self) -> List[PipelineStage]:
        """기본 파이프라인 단계 생성"""
        return [
            ValidationStage(),
            NormalizationStage(),
            DeduplicationStage(),
            QualityCheckStage()
        ]
    
    async def process(self, data: Any) -> PipelineResult:
        """파이프라인 실행"""
        self.stats["total_processed"] += 1
        current_data = data
        all_errors = []
        all_warnings = []
        stage_results = {}
        
        self.logger.info(f"파이프라인 시작: {len(self.stages)}개 단계")
        
        try:
            for stage in self.stages:
                self.logger.debug(f"단계 실행: {stage.name}")
                
                result = await stage.process(current_data)
                stage_results[stage.name] = {
                    "success": result.success,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "metadata": result.metadata
                }
                
                if result.errors:
                    all_errors.extend([f"[{stage.name}] {e}" for e in result.errors])
                
                if result.warnings:
                    all_warnings.extend([f"[{stage.name}] {w}" for w in result.warnings])
                
                if not result.success:
                    self.logger.error(f"단계 실패: {stage.name}")
                    self.stats["failed"] += 1
                    return PipelineResult(
                        success=False,
                        data=current_data,
                        errors=all_errors,
                        warnings=all_warnings,
                        stage_results=stage_results
                    )
                
                # 다음 단계로 데이터 전달
                current_data = result.data
            
            self.stats["successful"] += 1
            self.logger.info("파이프라인 완료")
            
            return PipelineResult(
                success=True,
                data=current_data,
                errors=all_errors,
                warnings=all_warnings,
                stage_results=stage_results
            )
            
        except Exception as e:
            self.stats["failed"] += 1
            self.logger.error(f"파이프라인 예외: {e}")
            return PipelineResult(
                success=False,
                data=data,
                errors=[str(e)],
                stage_results=stage_results
            )
    
    def add_stage(self, stage: PipelineStage):
        """단계 추가"""
        self.stages.append(stage)
        self.logger.info(f"파이프라인 단계 추가: {stage.name}")
    
    def remove_stage(self, name: str) -> bool:
        """단계 제거"""
        for i, stage in enumerate(self.stages):
            if stage.name == name:
                del self.stages[i]
                self.logger.info(f"파이프라인 단계 제거: {name}")
                return True
        return False
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """파이프라인 통계"""
        stage_stats = [stage.get_stats() for stage in self.stages]
        
        return {
            "pipeline": self.stats.copy(),
            "stages": stage_stats,
            "total_stages": len(self.stages)
        }


# 편의 함수들
def create_default_pipeline() -> DataPipeline:
    """기본 파이프라인 생성"""
    return DataPipeline()


def create_minimal_pipeline() -> DataPipeline:
    """최소한의 파이프라인 생성 (검증 + 정규화만)"""
    return DataPipeline([
        ValidationStage(),
        NormalizationStage()
    ])


if __name__ == "__main__":
    import asyncio
    
    async def test_pipeline():
        """파이프라인 테스트"""
        print("=== 데이터 파이프라인 테스트 ===")
        
        # 테스트 데이터
        test_data = [
            {
                "name": "  테스트 식당 1  ",
                "address_road": "서울 강남구 테스트로 123",
                "phone": "02-123-4567",
                "rating": "4.5",
                "lat": "37.123456",
                "lng": "127.123456",
                "menus": [
                    {"name": "김치찌개", "price": "8000원"},
                    {"name": "된장찌개", "price": "7000원"}
                ]
            },
            {
                "name": "테스트 식당 1",  # 중복
                "address_road": "서울 강남구 테스트로 123",
                "phone": "02-123-4567",
                "rating": "4.7",  # 더 높은 평점
            }
        ]
        
        pipeline = create_default_pipeline()
        result = await pipeline.process(test_data)
        
        print(f"파이프라인 결과:")
        print(f"  성공: {result.success}")
        print(f"  에러: {len(result.errors)}")
        print(f"  경고: {len(result.warnings)}")
        
        if result.warnings:
            print(f"  경고 메시지:")
            for warning in result.warnings:
                print(f"    - {warning}")
        
        if result.data:
            print(f"  처리된 데이터 수: {len(result.data) if isinstance(result.data, list) else 1}")
        
        # 단계별 통계
        stats = pipeline.get_pipeline_stats()
        print(f"\n파이프라인 통계:")
        for stage_stat in stats["stages"]:
            print(f"  {stage_stat['name']}: {stage_stat['successful']}성공/{stage_stat['processed']}처리")
    
    asyncio.run(test_pipeline())