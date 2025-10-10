"""
채팅 메시지에서 임시 불호 식재료를 추출하는 도구
하이브리드 접근: 키워드 패턴 매칭 → LLM 보조 (구체적 재료명만 추출)
"""

import re
import json
from typing import List, Set
from app.core.llm_factory import create_chat_llm
from langchain.schema import HumanMessage


class TemporaryDislikesExtractor:
    """채팅 메시지에서 임시 불호 식재료를 추출하는 클래스"""
    
    def __init__(self):
        # 일반적인 식재료 목록 (참고용 - LLM 프롬프트에 사용)
        self.common_ingredients = {
            # 육류
            "돼지고기", "소고기", "닭고기", "양고기", "오리고기", "햄", "베이컨", "소시지",
            # 해산물
            "새우", "게", "랍스터", "굴", "조개", "문어", "오징어", "연어", "참치", "고등어", "갈치",
            # 채소
            "양파", "마늘", "생강", "대파", "파", "당근", "브로콜리", "양배추", "배추", "무", "감자", "고구마",
            "토마토", "오이", "호박", "가지", "피망", "청양고추", "고추", "시금치", "상추", "깻잎",
            # 계란/유제품
            "계란", "달걀", "지단", "계란찜", "달걀찜", "스크램블", "우유", "치즈", "버터", "요거트", "크림",
            # 견과류
            "땅콩", "호두", "아몬드", "잣", "피스타치오", "캐슈넛", "마카다미아", "헤이즐넛",
            # 곡물/콩류
            "밀", "밀가루", "쌀", "현미", "보리", "귀리", "콩", "팥", "강낭콩", "완두콩", "렌틸콩",
            # 기타
            "두부", "콩나물", "숙주", "버섯", "김", "미역", "다시마", "참기름", "들기름", "올리브오일",
            "깨", "참깨", "들깨", "고춧가루", "간장", "된장", "고추장", "식초", "설탕", "소금"
        }
        
        # 너무 짧거나 의미 없는 단어 제외 (최소 검증용)
        self.invalid_words = {
            "것", "거", "게", "도", "를", "을", "이", "가", "은", "는", "에", "의", "와", "과",
            "하는", "있는", "없는", "좋은", "나쁜", "맛있는", "맛없는", "새로운", "오래된"
        }
        
        # LLM 초기화 (Lazy loading)
        self._llm = None
    
    @property
    def llm(self):
        """LLM Lazy loading"""
        if self._llm is None:
            try:
                self._llm = create_chat_llm()
                print("✅ LLM 초기화 성공 (임시 불호 추출용)")
            except Exception as e:
                print(f"⚠️ LLM 초기화 실패: {e}")
                self._llm = False  # 재시도 방지
        return self._llm if self._llm is not False else None
    
    async def _extract_with_llm(self, message: str) -> List[str]:
        """LLM으로 명시적으로 언급된 구체적인 식재료만 추출 (추론 금지)
        
        Args:
            message: 사용자의 채팅 메시지
            
        Returns:
            List[str]: LLM이 추출한 식재료 목록
        """
        if not self.llm:
            return []
        
        # 식재료 목록을 문자열로 변환
        ingredients_list = ", ".join(sorted(self.common_ingredients))
        
        prompt = f"""다음 메시지에서 사용자가 **명시적으로 언급한 구체적인 식재료만** 추출해주세요.

중요한 규칙:
1. **추론하지 말 것**: "매운 거", "기름진 음식" 같은 카테고리/형용사는 무시
2. **구체적인 재료명만**: "양파", "마늘", "계란", "지단" 같이 명확한 식재료만 추출
3. **제외/회피 의도**: "빼고", "말고", "싫어", "안 좋아", "피하고" 등의 표현과 함께 언급된 재료
4. 아래 식재료 목록은 참고용이며, 목록에 없더라도 명확한 식재료라면 추출

참고 식재료 목록 (전체는 아님):
{ingredients_list}

사용자 메시지: "{message}"

JSON 형식으로만 응답하세요:
{{"ingredients": ["재료1", "재료2"]}}

예시:
- "오늘은 양파는 좀..." → {{"ingredients": ["양파"]}}
- "마늘 넣지 말아줘" → {{"ingredients": ["마늘"]}}
- "지단 빼고" → {{"ingredients": ["지단"]}}
- "매운 거 말고" → {{"ingredients": []}}  (구체적 재료명 없음)
- "기름진 음식 피하고 싶어" → {{"ingredients": []}}  (구체적 재료명 없음)
- "계란이랑 우유는 빼줘" → {{"ingredients": ["계란", "우유"]}}
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            result_text = response.content.strip()
            
            # JSON 파싱
            # 코드 블록 제거 (```json ... ``` 형식 대응)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            ingredients = result.get("ingredients", [])
            
            # 의미 없는 단어만 필터링 (화이트리스트 방식 제거)
            valid_ingredients = [
                ing for ing in ingredients 
                if ing and len(ing) >= 2 and ing not in self.invalid_words
            ]
            
            if valid_ingredients:
                print(f"🤖 LLM 추출 성공: {valid_ingredients}")
            
            return valid_ingredients
            
        except Exception as e:
            print(f"⚠️ LLM 추출 실패: {e}")
            return []
    
    async def extract_from_message_async(self, message: str) -> List[str]:
        """
        채팅 메시지에서 임시 불호 식재료를 추출 (비동기, LLM 포함)
        
        Args:
            message: 사용자의 채팅 메시지
            
        Returns:
            List[str]: 추출된 불호 식재료 목록
        """
        temp_dislikes = set()
        
        # 1단계: 키워드 패턴 매칭
        keyword_results = self.extract_from_message(message)
        temp_dislikes.update(keyword_results)
        
        # 2단계: LLM 보조 (키워드로 못 잡은 경우)
        if not temp_dislikes:
            print("🤖 키워드 패턴 매칭 실패 → LLM 보조 시작")
            llm_results = await self._extract_with_llm(message)
            temp_dislikes.update(llm_results)
        else:
            print(f"✅ 키워드 패턴으로 추출 완료: {list(temp_dislikes)}")
        
        return list(temp_dislikes)
    
    def extract_from_message(self, message: str) -> List[str]:
        """
        채팅 메시지에서 임시 불호 식재료를 추출 (동기, 키워드만)
        
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
                # 의미 없는 단어가 아니고, 최소 2글자 이상이면 추출
                if ingredient and len(ingredient) >= 2 and ingredient not in self.invalid_words:
                    temp_dislikes.add(ingredient)
                    print(f"📝 임시 불호 식재료 추출: '{ingredient}' (패턴 매칭)")
        
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
                # 의미 없는 단어가 아니고, 최소 2글자 이상이면 추출
                if ingredient and len(ingredient) >= 2 and ingredient not in self.invalid_words:
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
            r"(\w+)(?:을|를|은|는|이|가)?\s*(?:넣지\s*말|넣지말)",  # "마늘 넣지 말아", "마늘을 넣지말"
        ]
        
        for pattern in dislike_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                ingredient = match.strip()
                # 의미 없는 단어가 아니고, 최소 2글자 이상이면 추출
                if ingredient and len(ingredient) >= 2 and ingredient not in self.invalid_words:
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
