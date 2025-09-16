"""
ChromaDB에 샘플 키토 레시피 데이터 초기화
"""
import asyncio
from app.tools.recipe_rag import RecipeRAGTool

async def init_sample_data():
    """샘플 키토 레시피 데이터 추가"""
    
    rag_tool = RecipeRAGTool()
    
    sample_recipes = [
        {
            "id": "keto_001",
            "title": "키토 김치볶음밥",
            "ingredients": [
                {"name": "콜리플라워 라이스", "amount": 200, "unit": "g"},
                {"name": "김치", "amount": 100, "unit": "g"},
                {"name": "돼지고기", "amount": 80, "unit": "g"},
                {"name": "달걀", "amount": 2, "unit": "개"},
                {"name": "코코넛오일", "amount": 1, "unit": "큰술"},
                {"name": "대파", "amount": 1, "unit": "대"}
            ],
            "steps": [
                "콜리플라워를 쌀알 크기로 다진다",
                "팬에 코코넛오일을 두르고 돼지고기를 볶는다",
                "김치를 넣고 함께 볶는다",
                "콜리플라워 라이스를 넣고 볶는다",
                "달걀을 풀어넣고 섞는다",
                "대파를 올려 완성"
            ],
            "tips": [
                "콜리플라워는 수분을 충분히 제거해야 합니다",
                "김치는 신맛이 강한 것을 사용하세요"
            ],
            "macros": {"kcal": 320, "carb": 8, "protein": 22, "fat": 24},
            "tags": ["키토", "한식", "볶음밥", "저탄수"],
            "ketoized": True,
            "allergen_flags": ["달걀"]
        },
        {
            "id": "keto_002", 
            "title": "키토 삼겹살 상추쌈",
            "ingredients": [
                {"name": "삼겹살", "amount": 200, "unit": "g"},
                {"name": "상추", "amount": 10, "unit": "장"},
                {"name": "깻잎", "amount": 5, "unit": "장"},
                {"name": "마늘", "amount": 3, "unit": "쪽"},
                {"name": "아보카도", "amount": 0.5, "unit": "개"},
                {"name": "올리브오일", "amount": 1, "unit": "큰술"}
            ],
            "steps": [
                "삼겹살을 구워낸다",
                "마늘은 편으로 썬다",
                "아보카도는 슬라이스한다",
                "상추와 깻잎을 준비한다",
                "구운 삼겹살을 상추에 싸서 먹는다"
            ],
            "tips": [
                "삼겹살은 기름기를 충분히 빼고 구우세요",
                "아보카도는 익은 것을 사용하세요"
            ],
            "macros": {"kcal": 450, "carb": 6, "protein": 28, "fat": 38},
            "tags": ["키토", "한식", "구이", "저탄수"],
            "ketoized": True,
            "allergen_flags": []
        },
        {
            "id": "keto_003",
            "title": "키토 아보카도 치즈 샐러드",
            "ingredients": [
                {"name": "아보카도", "amount": 1, "unit": "개"},
                {"name": "모짜렐라 치즈", "amount": 100, "unit": "g"},
                {"name": "방울토마토", "amount": 5, "unit": "개"},
                {"name": "올리브오일", "amount": 2, "unit": "큰술"},
                {"name": "레몬즙", "amount": 1, "unit": "큰술"},
                {"name": "소금", "amount": 0.5, "unit": "작은술"}
            ],
            "steps": [
                "아보카도를 큼직하게 썬다",
                "모짜렐라 치즈를 한입 크기로 자른다",
                "방울토마토를 반으로 자른다",
                "올리브오일과 레몬즙을 섞어 드레싱을 만든다",
                "모든 재료를 섞고 드레싱을 뿌린다"
            ],
            "tips": [
                "아보카도는 너무 익지 않은 것이 좋습니다",
                "드레싱은 먹기 직전에 뿌리세요"
            ],
            "macros": {"kcal": 380, "carb": 12, "protein": 18, "fat": 32},
            "tags": ["키토", "샐러드", "치즈", "저탄수"],
            "ketoized": True,
            "allergen_flags": ["유제품"]
        },
        {
            "id": "keto_004",
            "title": "키토 닭가슴살 버터구이",
            "ingredients": [
                {"name": "닭가슴살", "amount": 200, "unit": "g"},
                {"name": "버터", "amount": 2, "unit": "큰술"},
                {"name": "로즈마리", "amount": 1, "unit": "가지"},
                {"name": "마늘", "amount": 2, "unit": "쪽"},
                {"name": "소금", "amount": 0.5, "unit": "작은술"},
                {"name": "후추", "amount": 0.3, "unit": "작은술"}
            ],
            "steps": [
                "닭가슴살에 소금과 후추로 밑간한다",
                "팬에 버터를 녹인다",
                "마늘과 로즈마리를 넣고 향을 낸다",
                "닭가슴살을 넣고 구워낸다",
                "버터 소스를 끼얹어 완성"
            ],
            "tips": [
                "닭가슴살은 너무 오래 굽지 마세요",
                "버터 향이 날아가지 않도록 주의하세요"
            ],
            "macros": {"kcal": 340, "carb": 2, "protein": 35, "fat": 22},
            "tags": ["키토", "닭고기", "구이", "저탄수"],
            "ketoized": True,
            "allergen_flags": ["유제품"]
        },
        {
            "id": "keto_005",
            "title": "키토 코코넛 커피",
            "ingredients": [
                {"name": "블랙커피", "amount": 1, "unit": "컵"},
                {"name": "코코넛오일", "amount": 1, "unit": "큰술"},
                {"name": "버터", "amount": 1, "unit": "큰술"},
                {"name": "에리스리톨", "amount": 1, "unit": "작은술"}
            ],
            "steps": [
                "뜨거운 블랙커피를 준비한다",
                "코코넛오일과 버터를 넣는다",
                "에리스리톨을 넣는다",
                "믹서기로 30초간 블렌딩한다",
                "거품이 생기면 완성"
            ],
            "tips": [
                "블렌딩할 때 뚜껑을 꼭 닫으세요",
                "뜨거울 때 마셔야 맛있습니다"
            ],
            "macros": {"kcal": 200, "carb": 1, "protein": 1, "fat": 22},
            "tags": ["키토", "음료", "커피", "저탄수"],
            "ketoized": True,
            "allergen_flags": ["유제품"]
        }
    ]
    
    print("🚀 샘플 키토 레시피 데이터 초기화를 시작합니다...")
    
    for recipe in sample_recipes:
        try:
            recipe_id = await rag_tool.add_recipe_to_vector_store(recipe)
            if recipe_id:
                print(f"✅ '{recipe['title']}' 추가 완료 (ID: {recipe_id})")
            else:
                print(f"❌ '{recipe['title']}' 추가 실패")
        except Exception as e:
            print(f"❌ '{recipe['title']}' 추가 중 오류: {e}")
    
    # 통계 확인
    stats = rag_tool.vector_store.get_collection_stats()
    print(f"\n📊 ChromaDB 통계:")
    print(f"   - 컬렉션 이름: {stats['collection_name']}")
    print(f"   - 총 문서 수: {stats['document_count']}")
    
    print("\n🎉 샘플 데이터 초기화 완료!")

if __name__ == "__main__":
    asyncio.run(init_sample_data())
