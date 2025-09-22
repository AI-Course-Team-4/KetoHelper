"""
레시피 RAG (Retrieval-Augmented Generation) 도구
하이브리드 검색과 AI 생성을 결합한 레시피 추천
"""

from typing import List, Dict, Any, Optional
from app.tools.shared.hybrid_search import HybridSearchTool

class RecipeRAGTool:
    """레시피 RAG 도구 클래스"""
    
    def __init__(self):
        self.hybrid_search = HybridSearchTool()
    
    async def search_recipes(
        self,
        query: str,
        profile: str = "",
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """레시피 검색"""
        
        try:
            print(f"🍳 레시피 RAG 검색 시작: '{query}'")
            
            # 하이브리드 검색 실행
            results = await self.hybrid_search.search(query, profile, max_results)
            
            if not results:
                print("❌ 검색 결과가 없습니다.")
                return []
            
            print(f"✅ 검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            print(f"❌ 레시피 RAG 검색 오류: {e}")
            return []
    
    async def get_recipe_suggestions(
        self,
        ingredients: List[str],
        dietary_restrictions: List[str] = [],
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """재료 기반 레시피 추천"""
        
        try:
            # 재료를 검색 쿼리로 변환
            ingredient_query = " ".join(ingredients)
            
            # 식단 제한사항을 프로필로 변환
            profile_parts = []
            if dietary_restrictions:
                profile_parts.extend(dietary_restrictions)
            profile = " ".join(profile_parts)
            
            print(f"🥗 재료 기반 검색: '{ingredient_query}' (제한사항: {profile})")
            
            # 검색 실행
            results = await self.search_recipes(ingredient_query, profile, max_results)
            
            # 재료 매칭도 기반 정렬
            scored_results = []
            for result in results:
                score = self._calculate_ingredient_match_score(
                    ingredients, 
                    result.get('content', '')
                )
                result['ingredient_match_score'] = score
                scored_results.append(result)
            
            # 재료 매칭도 순으로 정렬
            scored_results.sort(key=lambda x: x['ingredient_match_score'], reverse=True)
            
            return scored_results
            
        except Exception as e:
            print(f"❌ 재료 기반 추천 오류: {e}")
            return []
    
    def _calculate_ingredient_match_score(
        self,
        user_ingredients: List[str],
        recipe_content: str
    ) -> float:
        """사용자 재료와 레시피 재료의 매칭 점수 계산"""
        
        if not user_ingredients or not recipe_content:
            return 0.0
        
        content_lower = recipe_content.lower()
        matches = 0
        
        for ingredient in user_ingredients:
            if ingredient.lower() in content_lower:
                matches += 1
        
        # 매칭 비율 계산
        match_ratio = matches / len(user_ingredients)
        return match_ratio
    
    async def search_by_category(
        self,
        category: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """카테고리별 레시피 검색"""
        
        category_queries = {
            "breakfast": "아침 아침식사 브런치 오믈렛 샐러드",
            "lunch": "점심 점심식사 도시락 볶음 구이",
            "dinner": "저녁 저녁식사 메인요리 스테이크 찜",
            "snack": "간식 디저트 견과류 치즈",
            "soup": "국 탕 찌개 국물요리",
            "salad": "샐러드 쌈 채소요리",
            "meat": "고기 육류 스테이크 구이",
            "seafood": "생선 해산물 회 구이",
            "dessert": "디저트 달콤한 케이크",
            "keto": "키토 저탄수 고지방"
        }
        
        query = category_queries.get(category.lower(), category)
        
        try:
            print(f"📂 카테고리 검색: '{category}' -> '{query}'")
            
            results = await self.search_recipes(query, "", max_results)
            
            # 카테고리 관련성 점수 추가
            for result in results:
                result['category_relevance'] = self._calculate_category_relevance(
                    category, 
                    result.get('title', '') + " " + result.get('content', '')
                )
            
            # 카테고리 관련성 순으로 정렬
            results.sort(key=lambda x: x['category_relevance'], reverse=True)
            
            return results
            
        except Exception as e:
            print(f"❌ 카테고리 검색 오류: {e}")
            return []
    
    def _calculate_category_relevance(
        self,
        category: str,
        recipe_text: str
    ) -> float:
        """카테고리 관련성 점수 계산"""
        
        category_keywords = {
            "breakfast": ["아침", "브런치", "오믈렛", "토스트", "시리얼"],
            "lunch": ["점심", "도시락", "샌드위치", "파스타", "볶음밥"],
            "dinner": ["저녁", "메인", "스테이크", "구이", "찜"],
            "snack": ["간식", "견과류", "치즈", "과일"],
            "soup": ["국", "탕", "찌개", "수프"],
            "salad": ["샐러드", "쌈", "채소"],
            "meat": ["고기", "육류", "소고기", "돼지고기", "닭고기"],
            "seafood": ["생선", "해산물", "연어", "참치", "새우"],
            "dessert": ["디저트", "케이크", "쿠키", "초콜릿"],
            "keto": ["키토", "저탄수", "고지방", "무탄수"]
        }
        
        keywords = category_keywords.get(category.lower(), [category])
        if not keywords:
            return 0.0
        
        text_lower = recipe_text.lower()
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        
        return matches / len(keywords)

# 전역 레시피 RAG 도구 인스턴스
recipe_rag_tool = RecipeRAGTool()