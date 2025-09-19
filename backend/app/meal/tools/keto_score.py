"""
키토 스코어 계산 도구
규칙 기반 키토 친화도 점수 계산 (0-100)
"""

from typing import Dict, List, Any
import re

class KetoScoreCalculator:
    """키토 스코어 계산기"""
    
    def __init__(self):
        # 키토 친화적 키워드들
        self.positive_keywords = {
            "protein_high": ["삼겹살", "목살", "등심", "갈비", "스테이크", "치킨", "닭다리", "계란", "회", "연어", "참치"],
            "vegetables": ["샐러드", "상추", "양배추", "브로콜리", "시금치", "나물", "쌈"],
            "fat_friendly": ["버터", "치즈", "아보카도", "올리브", "견과류"],
            "cooking_method": ["구이", "찜", "탕", "볶음", "무침"],
            "keto_options": ["밥빼기", "면빼기", "쌈추가", "치즈추가", "샤브샤브", "무한리필"]
        }
        
        # 키토 비친화적 키워드들
        self.negative_keywords = {
            "carbs_high": ["밥", "면", "국수", "파스타", "떡", "빵", "피자", "버거", "김밥", "초밥"],
            "sugary": ["달콤한", "단맛", "설탕", "꿀", "시럽", "디저트", "케이크"],
            "starchy": ["감자", "고구마", "전분", "튀김", "부침개"],
            "processed": ["라면", "컵라면", "인스턴트", "햄버거", "핫도그"]
        }
        
        # 카테고리별 기본 점수
        self.category_scores = {
            "고기": 30,
            "구이": 25,
            "한식": 20,
            "일식": 20,
            "양식": 25,
            "중식": 15,
            "분식": -20,
            "패스트푸드": -30,
            "디저트": -40
        }
    
    def calculate_score(
        self,
        name: str,
        category: str = "",
        address: str = "",
        description: str = ""
    ) -> Dict[str, Any]:
        """
        키토 스코어 계산
        
        Args:
            name: 식당명
            category: 카테고리
            address: 주소
            description: 설명
        
        Returns:
            점수, 이유, 팁을 포함한 딕셔너리
        """
        
        # 기본 점수 50에서 시작
        score = 50
        reasons = []
        tips = []
        
        # 텍스트 통합
        full_text = f"{name} {category} {description}".lower()
        
        # 1. 카테고리 기본 점수 적용
        category_bonus = self._get_category_score(category)
        if category_bonus != 0:
            score += category_bonus
            if category_bonus > 0:
                reasons.append(f"키토 친화적 카테고리 (+{category_bonus})")
            else:
                reasons.append(f"키토 비친화적 카테고리 ({category_bonus})")
        
        # 2. 긍정적 키워드 점수
        positive_score, positive_reasons = self._calculate_positive_score(full_text)
        score += positive_score
        reasons.extend(positive_reasons)
        
        # 3. 부정적 키워드 점수
        negative_score, negative_reasons = self._calculate_negative_score(full_text)
        score += negative_score
        reasons.extend(negative_reasons)
        
        # 4. 특별 보너스/패널티
        bonus_score, bonus_reasons, bonus_tips = self._calculate_special_bonus(full_text, name)
        score += bonus_score
        reasons.extend(bonus_reasons)
        tips.extend(bonus_tips)
        
        # 5. 점수 범위 제한 (0-100)
        score = max(0, min(100, score))
        
        # 6. 기본 키토 팁 추가
        tips.extend(self._get_basic_keto_tips(score, full_text))
        
        return {
            "score": int(score),
            "reasons": reasons[:5],  # 최대 5개 이유
            "tips": tips[:3]         # 최대 3개 팁
        }
    
    def _get_category_score(self, category: str) -> int:
        """카테고리별 기본 점수"""
        
        category_lower = category.lower()
        
        for key, score in self.category_scores.items():
            if key in category_lower:
                return score
        
        # 세부 카테고리 검사
        if any(word in category_lower for word in ["구이", "삼겹", "갈비", "스테이크"]):
            return 25
        elif any(word in category_lower for word in ["샤브", "전골", "찜"]):
            return 20
        elif any(word in category_lower for word in ["회", "초밥", "일식"]):
            return 15
        elif any(word in category_lower for word in ["피자", "햄버거", "치킨"]):
            return -10
        
        return 0
    
    def _calculate_positive_score(self, text: str) -> tuple[int, List[str]]:
        """긍정적 키워드 점수 계산"""
        
        score = 0
        reasons = []
        
        # 단백질 중심 메뉴
        protein_count = sum(1 for keyword in self.positive_keywords["protein_high"] if keyword in text)
        if protein_count > 0:
            protein_score = min(protein_count * 15, 30)  # 최대 30점
            score += protein_score
            reasons.append(f"고단백 메뉴 위주 (+{protein_score})")
        
        # 채소/쌈채소
        veg_count = sum(1 for keyword in self.positive_keywords["vegetables"] if keyword in text)
        if veg_count > 0:
            veg_score = min(veg_count * 10, 20)  # 최대 20점
            score += veg_score
            reasons.append(f"신선한 채소 반찬 (+{veg_score})")
        
        # 키토 옵션 가능
        option_count = sum(1 for keyword in self.positive_keywords["keto_options"] if keyword in text)
        if option_count > 0:
            option_score = min(option_count * 12, 25)  # 최대 25점
            score += option_score
            reasons.append(f"키토 맞춤 주문 가능 (+{option_score})")
        
        return score, reasons
    
    def _calculate_negative_score(self, text: str) -> tuple[int, List[str]]:
        """부정적 키워드 점수 계산"""
        
        score = 0
        reasons = []
        
        # 고탄수화물 주식
        carb_count = sum(1 for keyword in self.negative_keywords["carbs_high"] if keyword in text)
        if carb_count > 0:
            carb_penalty = min(carb_count * 15, 35)  # 최대 -35점
            score -= carb_penalty
            reasons.append(f"고탄수화물 주식 포함 (-{carb_penalty})")
        
        # 당분/단맛
        sugar_count = sum(1 for keyword in self.negative_keywords["sugary"] if keyword in text)
        if sugar_count > 0:
            sugar_penalty = min(sugar_count * 10, 20)  # 최대 -20점
            score -= sugar_penalty
            reasons.append(f"당분/단맛 양념 주의 (-{sugar_penalty})")
        
        # 가공식품
        processed_count = sum(1 for keyword in self.negative_keywords["processed"] if keyword in text)
        if processed_count > 0:
            processed_penalty = min(processed_count * 12, 25)  # 최대 -25점
            score -= processed_penalty
            reasons.append(f"가공식품/인스턴트 (-{processed_penalty})")
        
        return score, reasons
    
    def _calculate_special_bonus(self, text: str, name: str) -> tuple[int, List[str], List[str]]:
        """특별 보너스/패널티 및 팁 계산"""
        
        score = 0
        reasons = []
        tips = []
        
        # 무제한/뷔페 보너스
        if any(word in text for word in ["무한", "무제한", "뷔페", "샐러드바"]):
            score += 15
            reasons.append("무제한 메뉴로 양 조절 가능 (+15)")
            tips.append("채소와 단백질 위주로 섭취하세요")
        
        # 커스터마이징 가능
        if any(word in text for word in ["주문제작", "맞춤", "선택", "빼기가능"]):
            score += 10
            reasons.append("주문 커스터마이징 가능 (+10)")
            tips.append("밥/면 빼고 주문 가능한지 문의하세요")
        
        # 체인점 패널티 (일부)
        chain_penalties = ["맥도날드", "버거킹", "롯데리아", "파파존스"]
        if any(chain in name for chain in chain_penalties):
            score -= 20
            reasons.append("패스트푸드 체인점 (-20)")
            tips.append("샐러드나 그릴 메뉴 위주로 선택하세요")
        
        # 한정식/정식 주의
        if any(word in text for word in ["한정식", "정식", "코스"]):
            score -= 5
            reasons.append("정해진 코스 메뉴 (-5)")
            tips.append("밥 대신 추가 반찬 요청 가능한지 확인하세요")
        
        return score, reasons, tips
    
    def _get_basic_keto_tips(self, score: int, text: str) -> List[str]:
        """점수대별 기본 키토 팁"""
        
        tips = []
        
        if score >= 80:
            tips.append("키토에 매우 적합한 식당입니다!")
        elif score >= 60:
            tips.append("키토 친화적인 메뉴 선택 가능")
        elif score >= 40:
            tips.append("메뉴 선택 시 주의가 필요합니다")
        else:
            tips.append("키토 식단에는 권장하지 않습니다")
        
        # 일반적인 팁
        if "구이" in text or "고기" in text:
            tips.append("양념보다는 소금구이 추천")
        
        if "샐러드" in text:
            tips.append("드레싱은 올리브오일/발사믹 선택")
        
        if "치킨" in text:
            tips.append("튀김보다는 구이/찜 메뉴 선택")
        
        return tips
    
    def get_score_explanation(self, score: int) -> str:
        """점수대별 설명"""
        
        if score >= 90:
            return "완벽한 키토 식당"
        elif score >= 80:
            return "키토에 매우 적합"
        elif score >= 70:
            return "키토 친화적"
        elif score >= 60:
            return "키토 가능 (주의 필요)"
        elif score >= 40:
            return "키토 어려움"
        elif score >= 20:
            return "키토 부적합"
        else:
            return "키토 절대 금지"
    
    def batch_calculate_scores(
        self,
        places: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """여러 장소의 키토 스코어 일괄 계산"""
        
        scored_places = []
        
        for place in places:
            score_result = self.calculate_score(
                name=place.get("name", ""),
                category=place.get("category", ""),
                address=place.get("address", ""),
                description=place.get("description", "")
            )
            
            place_with_score = place.copy()
            place_with_score.update(score_result)
            scored_places.append(place_with_score)
        
        # 키토 스코어 순으로 정렬
        scored_places.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_places
