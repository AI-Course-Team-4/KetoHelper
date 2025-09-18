"""
ChromaDB에 레시피 데이터 추가
벡터 검색을 위한 임베딩 데이터 생성
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tools.recipe_rag import RecipeRAGTool

async def add_recipes_to_chromadb():
    """ChromaDB에 레시피 데이터 추가"""
    try:
        print("🔍 ChromaDB에 레시피 데이터 추가 시작")
        
        # RecipeRAGTool 인스턴스 생성
        rag_tool = RecipeRAGTool()
        
        # 샘플 레시피 데이터
        sample_recipes = [
            {
                "title": "키토 김치볶음밥",
                "content": "콜리플라워 라이스로 만드는 저탄수화물 김치볶음밥. 김치의 신맛과 고춧가루의 매운맛이 조화롭게 어우러진 한국형 키토 요리입니다. 아침 식사로 완벽하며, 콜리플라워의 식감이 밥과 비슷해서 만족감을 줍니다.",
                "ingredients": [
                    {"name": "콜리플라워 라이스", "amount": "200g"},
                    {"name": "김치", "amount": "100g"},
                    {"name": "달걀", "amount": "2개"},
                    {"name": "고춧가루", "amount": "1큰술"},
                    {"name": "마늘", "amount": "2쪽"},
                    {"name": "대파", "amount": "1대"},
                    {"name": "참기름", "amount": "1작은술"}
                ],
                "steps": [
                    "콜리플라워를 잘게 다져 라이스 형태로 만듭니다.",
                    "김치를 적당한 크기로 썹니다.",
                    "팬에 기름을 두르고 마늘을 볶습니다.",
                    "김치를 넣고 볶다가 콜리플라워 라이스를 넣습니다.",
                    "고춧가루와 대파를 넣고 볶습니다.",
                    "달걀을 풀어서 넣고 볶아 완성합니다."
                ],
                "nutrition": {
                    "calories": 180,
                    "carbs": 8,
                    "protein": 12,
                    "fat": 10
                },
                "category": "아침",
                "difficulty": "쉬움",
                "cooking_time": 15,
                "keto_score": 0.9
            },
            {
                "title": "아보카도 에그 토스트",
                "content": "아보카도와 달걀을 올린 저탄수화물 토스트. 아보카도의 부드러운 질감과 달걀의 고소함이 만나 완벽한 아침 식사가 됩니다. 키토 빵을 사용하여 탄수화물을 최소화했습니다.",
                "ingredients": [
                    {"name": "아보카도", "amount": "1개"},
                    {"name": "달걀", "amount": "2개"},
                    {"name": "키토 빵", "amount": "2조각"},
                    {"name": "레몬즙", "amount": "1큰술"},
                    {"name": "소금", "amount": "약간"},
                    {"name": "후추", "amount": "약간"},
                    {"name": "올리브 오일", "amount": "1큰술"}
                ],
                "steps": [
                    "키토 빵을 토스터에 구워줍니다.",
                    "아보카도를 으깨어 레몬즙, 소금, 후추로 간을 맞춥니다.",
                    "달걀을 프라이팬에 구워줍니다.",
                    "구운 빵에 아보카도를 발라주고 달걀을 올립니다.",
                    "올리브 오일을 뿌려 완성합니다."
                ],
                "nutrition": {
                    "calories": 320,
                    "carbs": 6,
                    "protein": 18,
                    "fat": 28
                },
                "category": "아침",
                "difficulty": "쉬움",
                "cooking_time": 10,
                "keto_score": 0.95
            },
            {
                "title": "키토 불고기",
                "content": "설탕 대신 에리스리톨을 사용한 저탄수화물 불고기. 한국인의 입맛에 맞는 달콤짭짤한 맛을 키토 식단에 맞게 조정했습니다. 소고기의 풍부한 단백질과 지방이 키토 다이어트에 완벽합니다.",
                "ingredients": [
                    {"name": "소고기", "amount": "300g"},
                    {"name": "양파", "amount": "1/2개"},
                    {"name": "대파", "amount": "2대"},
                    {"name": "마늘", "amount": "3쪽"},
                    {"name": "에리스리톨", "amount": "2큰술"},
                    {"name": "간장", "amount": "3큰술"},
                    {"name": "참기름", "amount": "1큰술"},
                    {"name": "고춧가루", "amount": "1큰술"}
                ],
                "steps": [
                    "소고기를 적당한 크기로 썹니다.",
                    "양파와 대파를 썹니다.",
                    "마늘을 다져서 양념장을 만듭니다.",
                    "고기를 양념에 재워둡니다.",
                    "팬에 고기를 볶다가 채소를 넣어 함께 볶습니다.",
                    "참기름을 넣고 마무리합니다."
                ],
                "nutrition": {
                    "calories": 280,
                    "carbs": 5,
                    "protein": 25,
                    "fat": 18
                },
                "category": "점심",
                "difficulty": "보통",
                "cooking_time": 30,
                "keto_score": 0.85
            },
            {
                "title": "키토 된장찌개",
                "content": "콩나물과 두부를 넣은 저탄수화물 된장찌개. 된장의 깊은 맛과 콩나물의 아삭한 식감이 조화롭게 어우러진 한국형 키토 요리입니다. 따뜻한 국물이 몸을 따뜻하게 해줍니다.",
                "ingredients": [
                    {"name": "된장", "amount": "2큰술"},
                    {"name": "콩나물", "amount": "100g"},
                    {"name": "두부", "amount": "1/2모"},
                    {"name": "대파", "amount": "1대"},
                    {"name": "마늘", "amount": "2쪽"},
                    {"name": "고춧가루", "amount": "1작은술"},
                    {"name": "멸치육수", "amount": "2컵"}
                ],
                "steps": [
                    "멸치육수를 끓입니다.",
                    "된장을 체에 걸러 넣습니다.",
                    "콩나물을 넣고 끓입니다.",
                    "두부를 넣고 끓입니다.",
                    "대파와 마늘을 넣고 끓입니다.",
                    "고춧가루를 넣고 마무리합니다."
                ],
                "nutrition": {
                    "calories": 120,
                    "carbs": 6,
                    "protein": 8,
                    "fat": 6
                },
                "category": "저녁",
                "difficulty": "쉬움",
                "cooking_time": 20,
                "keto_score": 0.8
            },
            {
                "title": "키토 김치찌개",
                "content": "돼지고기와 김치를 넣은 저탄수화물 김치찌개. 김치의 신맛과 돼지고기의 고소함이 조화롭게 어우러진 한국형 키토 요리입니다. 매운맛이 있어서 식욕을 돋워줍니다.",
                "ingredients": [
                    {"name": "김치", "amount": "200g"},
                    {"name": "돼지고기", "amount": "200g"},
                    {"name": "두부", "amount": "1/2모"},
                    {"name": "대파", "amount": "1대"},
                    {"name": "마늘", "amount": "3쪽"},
                    {"name": "고춧가루", "amount": "2큰술"},
                    {"name": "멸치육수", "amount": "3컵"}
                ],
                "steps": [
                    "돼지고기를 볶습니다.",
                    "김치를 넣고 볶습니다.",
                    "멸치육수를 넣고 끓입니다.",
                    "두부를 넣고 끓입니다.",
                    "대파와 마늘을 넣고 끓입니다.",
                    "고춧가루를 넣고 마무리합니다."
                ],
                "nutrition": {
                    "calories": 200,
                    "carbs": 8,
                    "protein": 15,
                    "fat": 12
                },
                "category": "저녁",
                "difficulty": "보통",
                "cooking_time": 25,
                "keto_score": 0.82
            }
        ]
        
        # 각 레시피를 ChromaDB에 추가
        for i, recipe in enumerate(sample_recipes, 1):
            print(f"\n{i}. {recipe['title']} 추가 중...")
            
            try:
                # ChromaDB에 레시피 추가
                result = await rag_tool.add_recipe_to_vector_store(recipe)
                
                if result:
                    print(f"   ✅ {recipe['title']} 추가 성공")
                else:
                    print(f"   ❌ {recipe['title']} 추가 실패")
                    
            except Exception as e:
                print(f"   ❌ {recipe['title']} 추가 오류: {e}")
        
        print(f"\n🎉 ChromaDB에 {len(sample_recipes)}개 레시피 추가 완료!")
        
        # 검색 테스트
        print("\n🔍 검색 테스트:")
        test_results = await rag_tool.search("키토 아침 메뉴", "", max_results=3)
        print(f"검색 결과: {len(test_results)}개")
        for i, result in enumerate(test_results, 1):
            print(f"  {i}. {result['title']} (유사도: {result['similarity']:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB 데이터 추가 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(add_recipes_to_chromadb())
