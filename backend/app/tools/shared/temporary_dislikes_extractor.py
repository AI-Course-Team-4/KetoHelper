"""
채팅 메시지에서 임시 불호 식재료를 추출하는 도구
"""

import re
from typing import List, Set


class TemporaryDislikesExtractor:
    """채팅 메시지에서 임시 불호 식재료를 추출하는 클래스"""
    
    def __init__(self):
        # 일반적인 식재료 목록 (한국어)
        self.common_ingredients = {
            # 육류
            "돼지고기", "소고기", "닭고기", "양고기", "오리고기", "햄", "베이컨", "소시지",
            # 해산물
            "새우", "게", "랍스터", "굴", "조개", "문어", "오징어", "연어", "참치", "고등어", "갈치",
            # 채소
            "양파", "마늘", "생강", "대파", "파", "당근", "브로콜리", "양배추", "배추", "무", "감자", "고구마",
            "토마토", "오이", "호박", "가지", "피망", "청양고추", "고추", "시금치", "상추", "깻잎",
            # 계란/유제품
            "계란", "달걀", "우유", "치즈", "버터", "요거트", "크림",
            # 견과류
            "땅콩", "호두", "아몬드", "잣", "피스타치오", "캐슈넛", "마카다미아", "헤이즐넛",
            # 곡물/콩류
            "밀", "밀가루", "쌀", "현미", "보리", "귀리", "콩", "팥", "강낭콩", "완두콩", "렌틸콩",
            # 기타
            "두부", "콩나물", "숙주", "버섯", "김", "미역", "다시마", "참기름", "들기름", "올리브오일",
            "깨", "참깨", "들깨", "고춧가루", "간장", "된장", "고추장", "식초", "설탕", "소금"
        }
        
        # 제외 패턴들 (동사, 형용사 등)
        self.exclude_patterns = [
            r".*\s+(뺀|제외|없는|안|말고|빼고)",  # "계란 뺀", "고기 없는" 등에서 뒤의 단어 제외
            r"(하는|있는|좋은|나쁜|맛있는|맛없는|새로운|오래된)"  # 형용사 제외
        ]
    
    def extract_from_message(self, message: str) -> List[str]:
        """
        채팅 메시지에서 임시 불호 식재료를 추출
        
        Args:
            message: 사용자의 채팅 메시지
            
        Returns:
            List[str]: 추출된 불호 식재료 목록
        """
        temp_dislikes = set()
        message_lower = message.lower()
        
        # 1. "X 뺀" 패턴 찾기 (조사 분리)
        exclude_patterns = [
            r"(\w+)(?:을|를|은|는|이|가)\s*뺀",  # "계란을 뺀", "계란은 뺀", "계란이 뺀"
            r"(\w+)\s+뺀",  # "계란 뺀"
            r"(\w+)(?:을|를|은|는|이|가)\s*제외",  # "계란을 제외", "계란은 제외", "계란이 제외"
            r"(\w+)\s+제외",  # "계란 제외"
            r"(\w+)(?:을|를|은|는|이|가)?\s*(?:없는|없이)",  # "계란을 없는", "계란은 없이", "계란이 없는", "계란 없는"
            r"(\w+)(?:을|를|은|는|이|가)?\s*(?:빼고|말고)",  # "계란을 빼고", "계란은 말고", "계란이 빼고", "계란 빼고"
            r"(\w+)(?:을|를|은|는|이|가)?\s*(?:안|못)",  # "계란을 안", "계란은 못", "계란이 안", "계란 안"
        ]
        
        for pattern in exclude_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                ingredient = match.strip()
                if ingredient in self.common_ingredients:
                    temp_dislikes.add(ingredient)
                    print(f"📝 임시 불호 식재료 추출: '{ingredient}' (패턴: {pattern})")
        
        # 2. "X 알레르기" 패턴 찾기 (조사 분리)
        allergy_patterns = [
            r"(\w+)(?:을|를|은|는|이|가)\s*알레르기",  # "새우를 알레르기", "새우는 알레르기"
            r"(\w+)\s+알레르기",  # "새우 알레르기"
            r"(\w+)(?:을|를|은|는|이|가)\s*(?:에|)\s*알러지",  # "새우를 알러지", "새우는 알러지"
            r"(\w+)\s+(?:에|)\s*알러지",  # "새우 알러지", "새우에 알러지"
        ]
        
        for pattern in allergy_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                ingredient = match.strip()
                if ingredient in self.common_ingredients:
                    temp_dislikes.add(ingredient)
                    print(f"📝 임시 불호 식재료 추출 (알레르기): '{ingredient}'")
        
        # 3. "X 싫어해" 패턴 찾기 (조사 분리)
        dislike_patterns = [
            r"(\w+)(?:을|를|은|는|이|가)\s*싫어",  # "브로콜리를 싫어", "브로콜리는 싫어", "브로콜리가 싫어"
            r"(\w+)\s+싫어",  # "브로콜리 싫어"
            r"(\w+)(?:을|를|은|는|이|가)\s*못\s*먹어",  # "새우를 못 먹어", "새우는 못 먹어", "새우가 못 먹어"
            r"(\w+)\s+못\s*먹어",  # "새우 못 먹어"
            r"(\w+)(?:을|를|은|는|이|가)\s*안\s*좋아",  # "양파를 안 좋아", "양파는 안 좋아", "양파가 안 좋아"
            r"(\w+)\s+안\s*좋아",  # "양파 안 좋아"
        ]
        
        for pattern in dislike_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                ingredient = match.strip()
                if ingredient in self.common_ingredients:
                    temp_dislikes.add(ingredient)
                    print(f"📝 임시 불호 식재료 추출 (싫어함): '{ingredient}'")
        
        return list(temp_dislikes)
    
    def combine_with_profile_dislikes(self, 
                                    temp_dislikes: List[str], 
                                    profile_dislikes: List[str]) -> List[str]:
        """
        임시 불호 식재료와 프로필의 불호 식재료를 합쳐서 중복 제거
        
        Args:
            temp_dislikes: 채팅에서 추출한 임시 불호 식재료
            profile_dislikes: DB에 저장된 프로필 불호 식재료
            
        Returns:
            List[str]: 합쳐진 불호 식재료 목록 (중복 제거됨)
        """
        combined = set()
        
        # 프로필 불호 식재료 추가
        if profile_dislikes:
            combined.update(profile_dislikes)
        
        # 임시 불호 식재료 추가
        if temp_dislikes:
            combined.update(temp_dislikes)
        
        combined_list = list(combined)
        print(f"🔗 합쳐진 불호 식재료: {combined_list}")
        return combined_list


# 전역 인스턴스 생성
temp_dislikes_extractor = TemporaryDislikesExtractor()
