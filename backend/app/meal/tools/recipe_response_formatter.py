"""
레시피 검색 결과 포맷팅 도구
하이브리드 검색 결과를 사용자 친화적인 응답으로 변환
"""

from typing import List, Dict, Any
from app.meal.agents.recipe_generator import RecipeGeneratorAgent

class RecipeResponseFormatter:
    """레시피 검색 결과 포맷터"""
    
    def __init__(self):
        self.recipe_generator = RecipeGeneratorAgent()
    
    async def format_hybrid_response(self, message: str, recipes: List[Dict[str, Any]], profile_context: str = "") -> str:
        """하이브리드 방식으로 레시피 응답 생성"""
        
        if not recipes:
            # 검색 결과가 없는 경우 - AI로 새 레시피 생성
            print(f"🤖 검색 실패 - AI로 '{message}' 레시피 생성 시작")
            return await self.recipe_generator.generate_recipe(message, profile_context)
        
        # 검색 전략 확인
        first_recipe = recipes[0]
        search_strategy = first_recipe.get('search_strategy', 'unknown')
        search_message = first_recipe.get('search_message', '')
        
        if search_strategy == 'exact':
            # 정확한 매칭이 있는 경우: 깔끔한 형식으로 반환
            return self._format_exact_match_response(message, recipes)
        
        elif search_strategy == 'partial':
            # 부분 매칭만 있는 경우 - 관련성 필터링
            relevant_recipes = self._filter_relevant_recipes(message, recipes)
            
            if relevant_recipes:
                return self._format_partial_match_response(message, relevant_recipes)
            else:
                # 관련성이 낮은 경우 AI 레시피 생성으로 넘어감
                print(f"🤖 부분 매칭 관련성 부족 - AI로 '{message}' 레시피 생성 시작")
                return await self.recipe_generator.generate_recipe(message, profile_context)
        
        else:
            # 기타 경우 (하이브리드 등)
            return self._format_general_response(message, recipes)
    
    def _format_exact_match_response(self, message: str, recipes: List[Dict[str, Any]]) -> str:
        """정확한 매칭 결과 포맷팅"""
        recipe_info = f"✅ '{message}'에 대한 레시피를 찾았습니다!\n\n"
        
        for i, recipe in enumerate(recipes[:2], 1):
            title = recipe.get('title', '제목 없음')
            content = recipe.get('content', '')
            
            recipe_info += f"📋 {i}. {title}\n"
            
            # blob 데이터 파싱
            if content:
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('요약:'):
                        recipe_info += f"   요약: {line.replace('요약:', '').strip()}\n"
                    elif line.startswith('재료:'):
                        recipe_info += f"   재료: {line.replace('재료:', '').strip()}\n"
                    elif line.startswith('알레르기:'):
                        recipe_info += f"   알레르기: {line.replace('알레르기:', '').strip()}\n"
                    elif line.startswith('태그:'):
                        recipe_info += f"   태그: {line.replace('태그:', '').strip()}\n"
                    elif line.startswith('보조 키워드:'):
                        recipe_info += f"   키워드: {line.replace('보조 키워드:', '').strip()}\n"
            
            recipe_info += "\n"
        
        recipe_info += f"💡 '{message}'에 대한 키토 조언:\n"
        recipe_info += "- 키토 식단에 적합한 조리법\n"
        recipe_info += "- 대체 재료 제안\n"
        recipe_info += "- 영양 성분 고려사항\n"
        recipe_info += "- 조리 팁 및 주의사항\n\n"
        recipe_info += f"위 레시피를 참고하여 '{message}'를 만들어보세요!"
        
        return recipe_info
    
    def _filter_relevant_recipes(self, message: str, recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """관련성 있는 레시피 필터링"""
        relevant_recipes = []
        
        for recipe in recipes:
            similarity = recipe.get('final_score', recipe.get('similarity', 0))
            title = recipe.get('title', '').lower()
            content = recipe.get('content', '').lower()
            
            # 관련성 검증
            is_relevant = False
            
            if similarity >= 0.7:  # 높은 유사도
                print(f"🔧 디버깅 - 높은 유사도 ({similarity}), 관련성 있음")
                is_relevant = True
            elif similarity >= 0.3:  # 중간 유사도인 경우 키워드 검증
                search_keywords = message.lower().split()
                
                # 중요한 키워드만 필터링
                important_keywords = []
                exclude_words = ['키토', '레시피', '만들어', '알려줘', '해줘', '요리', '음식', '만들']
                for keyword in search_keywords:
                    if len(keyword) > 3 and keyword not in exclude_words:
                        important_keywords.append(keyword)
                
                print(f"🔧 디버깅 - 검색어: '{message}'")
                print(f"🔧 디버깅 - 중요 키워드: {important_keywords}")
                print(f"🔧 디버깅 - 레시피 제목: '{title}'")
                print(f"🔧 디버깅 - 유사도: {similarity}")
                
                # 중요 키워드가 2개 미만이면 관련성 없음
                if len(important_keywords) < 2:
                    print(f"🔧 디버깅 - 중요 키워드 부족 ({len(important_keywords)}개), 관련성 없음")
                    is_relevant = False
                else:
                    # 모든 중요 키워드가 제목에 포함되어야 관련성 인정
                    keyword_matches = 0
                    matched_keywords = []
                    for keyword in important_keywords:
                        if keyword in title:
                            keyword_matches += 1
                            matched_keywords.append(keyword)
                    
                    print(f"🔧 디버깅 - 매칭된 키워드: {matched_keywords} ({keyword_matches}/{len(important_keywords)})")
                    
                    # 모든 중요 키워드가 매칭되어야 관련성 인정
                    if keyword_matches == len(important_keywords):
                        print(f"🔧 디버깅 - 모든 키워드 매칭, 관련성 있음")
                        is_relevant = True
                    else:
                        print(f"🔧 디버깅 - 키워드 불완전 매칭, 관련성 없음")
                        is_relevant = False
            
            if is_relevant:
                relevant_recipes.append(recipe)
        
        return relevant_recipes
    
    def _format_partial_match_response(self, message: str, recipes: List[Dict[str, Any]]) -> str:
        """부분 매칭 결과 포맷팅"""
        recipe_info = f"✅ '{message}'에 대한 레시피를 찾았습니다!\n\n"
        
        for i, recipe in enumerate(recipes[:2], 1):
            title = recipe.get('title', '제목 없음')
            content = recipe.get('content', '')
            
            recipe_info += f"📋 {i}. {title}\n"
            
            # blob 데이터 파싱
            if content:
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('요약:'):
                        recipe_info += f"   요약: {line.replace('요약:', '').strip()}\n"
                    elif line.startswith('재료:'):
                        recipe_info += f"   재료: {line.replace('재료:', '').strip()}\n"
                    elif line.startswith('알레르기:'):
                        recipe_info += f"   알레르기: {line.replace('알레르기:', '').strip()}\n"
                    elif line.startswith('태그:'):
                        recipe_info += f"   태그: {line.replace('태그:', '').strip()}\n"
                    elif line.startswith('보조 키워드:'):
                        recipe_info += f"   키워드: {line.replace('보조 키워드:', '').strip()}\n"
            
            recipe_info += "\n"
        
        recipe_info += f"💡 '{message}'에 대한 키토 조언:\n"
        recipe_info += "- 키토 식단에 적합한 조리법\n"
        recipe_info += "- 대체 재료 제안\n"
        recipe_info += "- 영양 성분 고려사항\n"
        recipe_info += "- 조리 팁 및 주의사항\n\n"
        recipe_info += f"위 레시피를 참고하여 '{message}'를 만들어보세요!"
        
        return recipe_info
    
    def _format_general_response(self, message: str, recipes: List[Dict[str, Any]]) -> str:
        """일반적인 검색 결과 포맷팅"""
        recipe_info = ""
        for i, recipe in enumerate(recipes[:2], 1):
            recipe_info += f"\n{i}. {recipe.get('title', '제목 없음')}\n"
            recipe_info += self._format_recipe_blob(recipe.get('content', ''))
            recipe_info += f"   유사도: {recipe.get('similarity', 0):.2f}\n"
            metadata = recipe.get('metadata', {})
            if metadata.get('ingredients'):
                ings = metadata['ingredients']
                if isinstance(ings, list):
                    ings = ", ".join(map(str, ings))
                recipe_info += f"   재료 목록: {ings}\n"
            if metadata.get('tags'):
                tags = metadata['tags']
                if isinstance(tags, list):
                    tags = ", ".join(map(str, tags))
                recipe_info += f"   태그: {tags}\n"
            if metadata.get('allergens'):
                al = metadata['allergens']
                if isinstance(al, list):
                    al = ", ".join(map(str, al))
                recipe_info += f"   알레르기: {al}\n"
        
        return f"""
🔍 '{message}'에 대한 검색 결과입니다.

📋 검색된 레시피:
{recipe_info}

💡 '{message}'에 대한 키토 조언:
- 키토 식단의 기본 원칙
- 대체 재료 제안
- 조리법 팁
- 영양 성분 고려사항

위 정보를 참고하여 맛있는 키토 요리를 만들어보세요!
친근하고 도움이 되는 톤으로 답변해주세요.
"""
    
    def _format_recipe_blob(self, blob_text: str) -> str:
        """크롤링 blob(text)에서 섹션을 추출해 요약 포맷으로 변환."""
        if not blob_text:
            return "   내용: 내용 없음\n"
        lines = [l.strip() for l in str(blob_text).splitlines() if l.strip()]
        sections = {
            '제목': '', '핵심 요약': '', '재료': '', '태그': '', '알레르기': '', '보조 키워드': ''
        }
        current = None
        for line in lines:
            if ':' in line:
                k, v = line.split(':', 1)
                k, v = k.strip(), v.strip()
                if k in sections:
                    sections[k] = v
                    current = k
                    continue
            if current and not (':' in line and line.split(':',1)[0].strip() in sections):
                sections[current] = (sections[current] + ' ' + line).strip()
        parts = []
        if sections['핵심 요약']:
            parts.append(f"   요약: {sections['핵심 요약']}")
        if sections['재료']:
            parts.append(f"   재료: {sections['재료']}")
        if sections['알레르기']:
            parts.append(f"   알레르기: {sections['알레르기']}")
        if sections['태그']:
            parts.append(f"   태그: {sections['태그']}")
        if sections['보조 키워드']:
            parts.append(f"   키워드: {sections['보조 키워드']}")
        if parts:
            return "\n".join(parts) + "\n"
        snippet = " ".join(lines)
        if len(snippet) > 160:
            snippet = snippet[:160] + '...'
        return f"   내용: {snippet}\n"
