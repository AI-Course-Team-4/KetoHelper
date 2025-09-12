"""
📝 텍스트 처리 유틸리티
- 텍스트 정규화 및 정제
- 주소, 전화번호, 가격 추출
- 중복 제거를 위한 유사도 계산
"""

import re
import unicodedata
from typing import List, Optional, Tuple, Dict, Any
from difflib import SequenceMatcher


class TextNormalizer:
    """텍스트 정규화 클래스"""
    
    def __init__(self):
        # 전화번호 패턴
        self.phone_patterns = [
            r'(\d{2,3})-(\d{3,4})-(\d{4})',  # 02-1234-5678
            r'(\d{2,3})\s*(\d{3,4})\s*(\d{4})',  # 02 1234 5678
            r'(\d{10,11})',  # 0212345678
        ]
        
        # 가격 패턴
        self.price_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*원',  # 15,000원
            r'₩\s*(\d{1,3}(?:,\d{3})*)',   # ₩15,000
            r'(\d{1,3}(?:,\d{3})*)\s*won', # 15,000won
        ]
        
        # 좌표 패턴
        self.coordinate_patterns = [
            r'lat[^0-9]*([0-9.]+)',
            r'latitude[^0-9]*([0-9.]+)',
            r'lng[^0-9]*([0-9.]+)',
            r'longitude[^0-9]*([0-9.]+)',
        ]
        
        # 정제할 불필요한 문자/단어
        self.cleanup_patterns = [
            r'\s+',              # 연속 공백 -> 단일 공백
            r'^[\s\n]+|[\s\n]+$', # 앞뒤 공백/개행 제거
            r'\n+',              # 연속 개행 -> 단일 개행
            r'[^\w\s가-힣.,()-]', # 특수문자 제거 (일부 제외)
        ]
    
    def normalize_text(self, text: str) -> str:
        """기본 텍스트 정규화"""
        if not text:
            return ""
        
        # 유니코드 정규화
        text = unicodedata.normalize('NFKC', text)
        
        # 불필요한 패턴 제거
        for pattern in self.cleanup_patterns:
            if pattern == r'\s+':
                text = re.sub(pattern, ' ', text)
            elif pattern == r'^[\s\n]+|[\s\n]+$':
                text = re.sub(pattern, '', text)
            elif pattern == r'\n+':
                text = re.sub(pattern, '\n', text)
            else:
                text = re.sub(pattern, '', text)
        
        return text.strip()
    
    def normalize_restaurant_name(self, name: str) -> str:
        """식당명 정규화"""
        name = self.normalize_text(name)
        
        # 식당명에서 불필요한 접미사 제거
        suffixes = ['본점', '분점', '지점', '매장', '식당', '레스토랑']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
                break
        
        return name
    
    def normalize_address(self, address: str) -> str:
        """주소 정규화"""
        address = self.normalize_text(address)
        
        # 주소 정규화 패턴
        patterns = [
            (r'\s+', ' '),  # 연속 공백 제거
            (r'(\d+)-(\d+)', r'\1-\2'),  # 번지수 정규화
            (r'(\d+)번지', r'\1'),  # '번지' 제거
            (r'(\d+)호', r'\1호'),  # 호수 정규화
        ]
        
        for pattern, replacement in patterns:
            address = re.sub(pattern, replacement, address)
        
        return address.strip()
    
    def extract_phone_number(self, text: str) -> Optional[str]:
        """전화번호 추출 및 정규화"""
        text = self.normalize_text(text)
        
        for pattern in self.phone_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 3:
                    # 분리된 형태
                    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                else:
                    # 연속된 숫자
                    number = match.group(1)
                    if len(number) == 10:
                        return f"{number[:2]}-{number[2:6]}-{number[6:]}"
                    elif len(number) == 11:
                        return f"{number[:3]}-{number[3:7]}-{number[7:]}"
        
        return None
    
    def extract_price(self, text: str) -> Optional[int]:
        """가격 추출 및 정규화"""
        text = self.normalize_text(text)
        
        for pattern in self.price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return int(price_str)
                except ValueError:
                    continue
        
        return None
    
    def extract_coordinates(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        """좌표 추출"""
        lat, lng = None, None
        
        for pattern in self.coordinate_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match)
                    if 'lat' in pattern.lower():
                        lat = value
                    elif 'lng' in pattern.lower() or 'lon' in pattern.lower():
                        lng = value
                except ValueError:
                    continue
        
        return lat, lng
    
    def extract_rating(self, text: str) -> Optional[float]:
        """평점 추출"""
        # 평점 패턴: 4.5/5, 4.5점, 4.5 out of 5
        patterns = [
            r'(\d+\.?\d*)\s*/\s*5',
            r'(\d+\.?\d*)\s*점',
            r'(\d+\.?\d*)\s*out\s*of\s*5',
            r'평점\s*(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    rating = float(match.group(1))
                    # 평점이 5점 척도인지 확인
                    if 0 <= rating <= 5:
                        return rating
                except ValueError:
                    continue
        
        return None


class SimilarityCalculator:
    """유사도 계산 클래스"""
    
    @staticmethod
    def text_similarity(text1: str, text2: str) -> float:
        """텍스트 유사도 계산 (0-1)"""
        if not text1 or not text2:
            return 0.0
        
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    @staticmethod
    def restaurant_similarity(restaurant1: Dict[str, Any], 
                            restaurant2: Dict[str, Any]) -> float:
        """식당 유사도 계산"""
        scores = []
        
        # 이름 유사도 (가중치: 0.5)
        name_sim = SimilarityCalculator.text_similarity(
            restaurant1.get("name", ""),
            restaurant2.get("name", "")
        )
        scores.append(("name", name_sim, 0.5))
        
        # 주소 유사도 (가중치: 0.3)
        address_sim = SimilarityCalculator.text_similarity(
            restaurant1.get("address_road", ""),
            restaurant2.get("address_road", "")
        )
        scores.append(("address", address_sim, 0.3))
        
        # 전화번호 일치 (가중치: 0.2)
        phone_sim = 1.0 if (restaurant1.get("phone") and 
                           restaurant2.get("phone") and
                           restaurant1["phone"] == restaurant2["phone"]) else 0.0
        scores.append(("phone", phone_sim, 0.2))
        
        # 가중 평균 계산
        total_weight = sum(weight for _, _, weight in scores)
        weighted_sum = sum(score * weight for _, score, weight in scores)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    @staticmethod
    def coordinate_distance(lat1: float, lng1: float, 
                          lat2: float, lng2: float) -> float:
        """좌표 간 거리 계산 (미터)"""
        import math
        
        # Haversine 공식
        R = 6371000  # 지구 반지름 (미터)
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


class CategoryClassifier:
    """카테고리 분류기"""
    
    def __init__(self):
        self.category_keywords = {
            "한식": ["김치", "불고기", "갈비", "비빔밥", "냉면", "삼겹살", "된장", "고추장"],
            "중식": ["짜장면", "짬뽕", "탕수육", "마파두부", "양장피", "볶음밥", "딤섬"],
            "일식": ["초밥", "사시미", "우동", "라멘", "돈카츠", "야키토리", "텐푸라"],
            "양식": ["스테이크", "파스타", "피자", "샐러드", "햄버거", "리조또", "스프"],
            "분식": ["떡볶이", "순대", "튀김", "김밥", "라면", "어묵", "만두"],
            "치킨": ["치킨", "닭", "프라이드", "양념", "후라이드"],
            "카페": ["커피", "라떼", "아메리카노", "디저트", "케이크", "빙수"],
            "술집": ["맥주", "소주", "안주", "포차", "호프", "치킨", "삼겹살"],
        }
        
        self.cooking_methods = {
            "구이": ["구이", "바베큐", "그릴", "로스트"],
            "볶음": ["볶음", "볶은", "stir", "fry"],
            "찜": ["찜", "steam", "braised"],
            "튀김": ["튀김", "프라이드", "fried", "tempura"],
            "국물": ["국", "탕", "찌개", "soup", "stew"],
            "무침": ["무침", "salad", "mix"],
        }
    
    def classify_cuisine_type(self, menu_names: List[str], 
                            restaurant_name: str = "") -> Optional[str]:
        """요리 타입 분류"""
        text = " ".join(menu_names + [restaurant_name]).lower()
        
        scores = {}
        for cuisine_type, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[cuisine_type] = score
        
        if scores:
            return max(scores.keys(), key=lambda k: scores[k])
        
        return None
    
    def classify_cooking_method(self, menu_name: str) -> Optional[str]:
        """조리법 분류"""
        menu_name_lower = menu_name.lower()
        
        for method, keywords in self.cooking_methods.items():
            if any(keyword in menu_name_lower for keyword in keywords):
                return method
        
        return None


# 전역 인스턴스
normalizer = TextNormalizer()
similarity_calculator = SimilarityCalculator()
category_classifier = CategoryClassifier()


# 편의 함수들
def normalize_text(text: str) -> str:
    """텍스트 정규화"""
    return normalizer.normalize_text(text)


def normalize_restaurant_name(name: str) -> str:
    """식당명 정규화"""
    return normalizer.normalize_restaurant_name(name)


def normalize_address(address: str) -> str:
    """주소 정규화"""
    return normalizer.normalize_address(address)


def extract_phone_number(text: str) -> Optional[str]:
    """전화번호 추출"""
    return normalizer.extract_phone_number(text)


def extract_price(text: str) -> Optional[int]:
    """가격 추출"""
    return normalizer.extract_price(text)


def extract_coordinates(text: str) -> Tuple[Optional[float], Optional[float]]:
    """좌표 추출"""
    return normalizer.extract_coordinates(text)


def extract_rating(text: str) -> Optional[float]:
    """평점 추출"""
    return normalizer.extract_rating(text)


def calculate_text_similarity(text1: str, text2: str) -> float:
    """텍스트 유사도 계산"""
    return similarity_calculator.text_similarity(text1, text2)


def calculate_restaurant_similarity(restaurant1: Dict[str, Any], 
                                  restaurant2: Dict[str, Any]) -> float:
    """식당 유사도 계산"""
    return similarity_calculator.restaurant_similarity(restaurant1, restaurant2)


def calculate_coordinate_distance(lat1: float, lng1: float, 
                                lat2: float, lng2: float) -> float:
    """좌표 간 거리 계산"""
    return similarity_calculator.coordinate_distance(lat1, lng1, lat2, lng2)


def classify_cuisine_type(menu_names: List[str], restaurant_name: str = "") -> Optional[str]:
    """요리 타입 분류"""
    return category_classifier.classify_cuisine_type(menu_names, restaurant_name)


def classify_cooking_method(menu_name: str) -> Optional[str]:
    """조리법 분류"""
    return category_classifier.classify_cooking_method(menu_name)


if __name__ == "__main__":
    # 테스트 코드
    test_cases = [
        ("  강남  맛집  본점  ", "강남 맛집"),
        ("02-1234-5678", "전화번호: 02-1234-5678"),
        ("15,000원", "가격: 15000"),
        ("lat: 37.123456, lng: 127.123456", "좌표: (37.123456, 127.123456)"),
        ("평점 4.5점", "평점: 4.5"),
    ]
    
    for input_text, expected in test_cases:
        if "맛집" in input_text:
            result = normalize_restaurant_name(input_text)
            print(f"식당명 정규화: '{input_text}' -> '{result}'")
        elif "02-" in input_text:
            result = extract_phone_number(input_text)
            print(f"전화번호 추출: '{input_text}' -> '{result}'")
        elif "원" in input_text:
            result = extract_price(input_text)
            print(f"가격 추출: '{input_text}' -> {result}")
        elif "lat:" in input_text:
            result = extract_coordinates(input_text)
            print(f"좌표 추출: '{input_text}' -> {result}")
        elif "평점" in input_text:
            result = extract_rating(input_text)
            print(f"평점 추출: '{input_text}' -> {result}")
    
    # 유사도 테스트
    rest1 = {"name": "강남맛집", "address_road": "서울시 강남구 테헤란로 123", "phone": "02-1234-5678"}
    rest2 = {"name": "강남맛집본점", "address_road": "서울시 강남구 테헤란로 123", "phone": "02-1234-5678"}
    similarity = calculate_restaurant_similarity(rest1, rest2)
    print(f"식당 유사도: {similarity:.2f}")
    
    # 카테고리 분류 테스트
    menus = ["김치찌개", "불고기", "된장찌개"]
    cuisine = classify_cuisine_type(menus)
    print(f"요리 타입: {cuisine}")
    
    cooking = classify_cooking_method("불고기구이")
    print(f"조리법: {cooking}")
    
    print("텍스트 유틸리티 테스트 완료!")