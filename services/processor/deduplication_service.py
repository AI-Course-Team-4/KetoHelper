"""
중복 제거 서비스
"""

import re
from typing import List, Dict, Tuple, Set
from difflib import SequenceMatcher
import logging

from core.domain.restaurant import Restaurant

logger = logging.getLogger(__name__)

class DeduplicationService:
    """식당 중복 제거 서비스"""

    def __init__(
        self,
        name_similarity_threshold: float = 0.8,
        distance_threshold_km: float = 0.1,
        phone_match_weight: float = 0.5
    ):
        self.name_similarity_threshold = name_similarity_threshold
        self.distance_threshold_km = distance_threshold_km
        self.phone_match_weight = phone_match_weight

    async def deduplicate_restaurants(self, restaurants: List[Restaurant]) -> List[Restaurant]:
        """식당 리스트 중복 제거"""
        if not restaurants:
            return []

        logger.info(f"Starting deduplication for {len(restaurants)} restaurants")

        # 1. 정확한 중복 제거 (canonical_key 기반)
        exact_duplicates_removed = self._remove_exact_duplicates(restaurants)

        # 2. 유사 중복 제거 (이름, 위치, 전화번호 기반)
        fuzzy_duplicates_removed = await self._remove_fuzzy_duplicates(exact_duplicates_removed)

        logger.info(f"Deduplication completed: {len(restaurants)} -> {len(fuzzy_duplicates_removed)} restaurants")

        return fuzzy_duplicates_removed

    def _remove_exact_duplicates(self, restaurants: List[Restaurant]) -> List[Restaurant]:
        """정확한 중복 제거"""
        seen_keys = set()
        unique_restaurants = []

        for restaurant in restaurants:
            key = restaurant.canonical_key
            if key not in seen_keys:
                seen_keys.add(key)
                unique_restaurants.append(restaurant)
            else:
                logger.debug(f"Exact duplicate found: {restaurant.name}")

        return unique_restaurants

    async def _remove_fuzzy_duplicates(self, restaurants: List[Restaurant]) -> List[Restaurant]:
        """유사 중복 제거"""
        clusters = []
        processed = set()

        for i, restaurant in enumerate(restaurants):
            if i in processed:
                continue

            # 새 클러스터 시작
            cluster = [restaurant]
            processed.add(i)

            # 나머지 식당들과 비교
            for j, other_restaurant in enumerate(restaurants[i + 1:], start=i + 1):
                if j in processed:
                    continue

                if self._are_similar_restaurants(restaurant, other_restaurant):
                    cluster.append(other_restaurant)
                    processed.add(j)

            clusters.append(cluster)

        # 각 클러스터에서 대표 식당 선택
        deduplicated = []
        for cluster in clusters:
            representative = self._select_representative_restaurant(cluster)
            deduplicated.append(representative)

        return deduplicated

    def _are_similar_restaurants(self, restaurant1: Restaurant, restaurant2: Restaurant) -> bool:
        """두 식당이 유사한지 판단"""
        similarity_score = 0.0
        max_score = 0.0

        # 1. 이름 유사도 (가중치: 0.6)
        name_weight = 0.6
        name_sim = self._calculate_name_similarity(restaurant1.name, restaurant2.name)
        similarity_score += name_sim * name_weight
        max_score += name_weight

        # 2. 위치 유사도 (가중치: 0.3)
        location_weight = 0.3
        if restaurant1.has_location and restaurant2.has_location:
            distance_km = self._calculate_distance(restaurant1, restaurant2)
            if distance_km <= self.distance_threshold_km:
                location_sim = 1.0 - (distance_km / self.distance_threshold_km)
                similarity_score += location_sim * location_weight
            max_score += location_weight

        # 3. 전화번호 일치 (가중치: 0.1)
        phone_weight = 0.1
        if restaurant1.phone and restaurant2.phone:
            phone_sim = 1.0 if self._normalize_phone_for_comparison(restaurant1.phone) == \
                               self._normalize_phone_for_comparison(restaurant2.phone) else 0.0
            similarity_score += phone_sim * phone_weight
        max_score += phone_weight

        # 유사도 계산
        if max_score > 0:
            final_similarity = similarity_score / max_score
            return final_similarity >= self.name_similarity_threshold

        return False

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """이름 유사도 계산"""
        # 정규화
        norm_name1 = self._normalize_name_for_comparison(name1)
        norm_name2 = self._normalize_name_for_comparison(name2)

        if norm_name1 == norm_name2:
            return 1.0

        # SequenceMatcher를 사용한 유사도 계산
        return SequenceMatcher(None, norm_name1, norm_name2).ratio()

    def _normalize_name_for_comparison(self, name: str) -> str:
        """비교를 위한 이름 정규화"""
        if not name:
            return ""

        # 소문자 변환
        name = name.lower()

        # 공백 제거
        name = re.sub(r'\s+', '', name)

        # 특수문자 제거
        name = re.sub(r'[^\w가-힣]', '', name)

        # 일반적인 식당 키워드 제거
        remove_keywords = ['식당', '음식점', '맛집', '레스토랑', '카페', '까페']
        for keyword in remove_keywords:
            name = name.replace(keyword, '')

        return name

    def _calculate_distance(self, restaurant1: Restaurant, restaurant2: Restaurant) -> float:
        """두 식당 간 거리 계산 (km)"""
        if not (restaurant1.has_location and restaurant2.has_location):
            return float('inf')

        lat1 = float(restaurant1.address.latitude)
        lon1 = float(restaurant1.address.longitude)
        lat2 = float(restaurant2.address.latitude)
        lon2 = float(restaurant2.address.longitude)

        # Haversine 공식
        import math

        R = 6371  # 지구 반지름 (km)

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance

    def _normalize_phone_for_comparison(self, phone: str) -> str:
        """비교를 위한 전화번호 정규화"""
        if not phone:
            return ""

        # 숫자만 추출
        return re.sub(r'[^\d]', '', phone)

    def _select_representative_restaurant(self, cluster: List[Restaurant]) -> Restaurant:
        """클러스터에서 대표 식당 선택"""
        if len(cluster) == 1:
            return cluster[0]

        # 선택 기준:
        # 1. 가장 많은 정보를 가진 식당
        # 2. 평점이 있는 식당
        # 3. 소스가 많은 식당

        best_restaurant = cluster[0]
        best_score = self._calculate_restaurant_quality_score(best_restaurant)

        for restaurant in cluster[1:]:
            score = self._calculate_restaurant_quality_score(restaurant)
            if score > best_score:
                best_score = score
                best_restaurant = restaurant

        # 다른 식당들의 소스 정보를 대표 식당에 병합
        for restaurant in cluster:
            if restaurant != best_restaurant:
                for source in restaurant.sources:
                    best_restaurant.add_source(source)

        return best_restaurant

    def _calculate_restaurant_quality_score(self, restaurant: Restaurant) -> float:
        """식당 정보 품질 점수 계산"""
        score = 0.0

        # 기본 정보
        if restaurant.name:
            score += 1.0
        if restaurant.phone:
            score += 1.0
        if restaurant.address:
            score += 1.0
        if restaurant.has_location:
            score += 2.0

        # 추가 정보
        if restaurant.business_hours:
            score += 1.0
        if restaurant.cuisine_types:
            score += 1.0
        if restaurant.price_range:
            score += 0.5

        # 평점 정보
        if restaurant.rating_avg:
            score += 2.0
        if restaurant.review_count > 0:
            score += 1.0

        # 소스 수
        score += len(restaurant.sources) * 0.5

        return score

    def get_duplicate_statistics(self, original_count: int, deduplicated_count: int) -> Dict[str, any]:
        """중복 제거 통계"""
        duplicates_removed = original_count - deduplicated_count
        duplicate_rate = duplicates_removed / original_count if original_count > 0 else 0

        return {
            'original_count': original_count,
            'deduplicated_count': deduplicated_count,
            'duplicates_removed': duplicates_removed,
            'duplicate_rate': round(duplicate_rate * 100, 2),
            'compression_ratio': round(deduplicated_count / original_count if original_count > 0 else 1, 3)
        }