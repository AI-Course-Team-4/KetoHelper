"""
Supabase 테이블 생성 스크립트
하이브리드 검색을 위한 레시피 테이블 생성
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

def create_supabase_tables():
    """Supabase 테이블 생성"""
    try:
        # Supabase 클라이언트 생성
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase 환경변수가 설정되지 않았습니다.")
            print("   .env 파일에 다음을 추가하세요:")
            print("   SUPABASE_URL=your_supabase_url")
            print("   SUPABASE_ANON_KEY=your_supabase_anon_key")
            return False
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase 클라이언트 연결 성공")
        
        # 테이블이 이미 존재하는지 확인
        try:
            # 기존 테이블 확인
            existing_tables = supabase.table('recipes').select('id').limit(1).execute()
            print("✅ 레시피 테이블이 이미 존재합니다")
        except Exception as e:
            print("⚠️ 레시피 테이블이 존재하지 않습니다")
            print("💡 Supabase 대시보드에서 수동으로 테이블을 생성해주세요:")
            print("""
            CREATE TABLE recipes (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                difficulty TEXT,
                cooking_time INTEGER,
                keto_score FLOAT,
                ingredients JSONB,
                steps JSONB,
                nutrition_info JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """)
            print("또는 Supabase SQL Editor에서 위 SQL을 실행해주세요.")
            return False
        
        # 샘플 데이터 삽입
        sample_recipes = [
            {
                "title": "키토 김치볶음밥",
                "content": "콜리플라워 라이스로 만드는 저탄수화물 김치볶음밥. 김치의 신맛과 고춧가루의 매운맛이 조화롭게 어우러진 한국형 키토 요리입니다.",
                "category": "아침",
                "difficulty": "쉬움",
                "cooking_time": 15,
                "keto_score": 0.9,
                "ingredients": [
                    {"name": "콜리플라워 라이스", "amount": "200g"},
                    {"name": "김치", "amount": "100g"},
                    {"name": "달걀", "amount": "2개"},
                    {"name": "고춧가루", "amount": "1큰술"},
                    {"name": "마늘", "amount": "2쪽"},
                    {"name": "대파", "amount": "1대"}
                ],
                "steps": [
                    "콜리플라워를 잘게 다져 라이스 형태로 만듭니다.",
                    "김치를 적당한 크기로 썹니다.",
                    "팬에 기름을 두르고 마늘을 볶습니다.",
                    "김치를 넣고 볶다가 콜리플라워 라이스를 넣습니다.",
                    "고춧가루와 대파를 넣고 볶아 완성합니다."
                ],
                "nutrition_info": {
                    "calories": 180,
                    "carbs": 8,
                    "protein": 12,
                    "fat": 10
                }
            },
            {
                "title": "아보카도 에그 토스트",
                "content": "아보카도와 달걀을 올린 저탄수화물 토스트. 아보카도의 부드러운 질감과 달걀의 고소함이 만나 완벽한 아침 식사가 됩니다.",
                "category": "아침",
                "difficulty": "쉬움",
                "cooking_time": 10,
                "keto_score": 0.95,
                "ingredients": [
                    {"name": "아보카도", "amount": "1개"},
                    {"name": "달걀", "amount": "2개"},
                    {"name": "키토 빵", "amount": "2조각"},
                    {"name": "레몬즙", "amount": "1큰술"},
                    {"name": "소금", "amount": "약간"},
                    {"name": "후추", "amount": "약간"}
                ],
                "steps": [
                    "키토 빵을 토스터에 구워줍니다.",
                    "아보카도를 으깨어 레몬즙, 소금, 후추로 간을 맞춥니다.",
                    "달걀을 프라이팬에 구워줍니다.",
                    "구운 빵에 아보카도를 발라주고 달걀을 올립니다."
                ],
                "nutrition_info": {
                    "calories": 320,
                    "carbs": 6,
                    "protein": 18,
                    "fat": 28
                }
            },
            {
                "title": "키토 불고기",
                "content": "설탕 대신 에리스리톨을 사용한 저탄수화물 불고기. 한국인의 입맛에 맞는 달콤짭짤한 맛을 키토 식단에 맞게 조정했습니다.",
                "category": "점심",
                "difficulty": "보통",
                "cooking_time": 30,
                "keto_score": 0.85,
                "ingredients": [
                    {"name": "소고기", "amount": "300g"},
                    {"name": "양파", "amount": "1/2개"},
                    {"name": "대파", "amount": "2대"},
                    {"name": "마늘", "amount": "3쪽"},
                    {"name": "에리스리톨", "amount": "2큰술"},
                    {"name": "간장", "amount": "3큰술"},
                    {"name": "참기름", "amount": "1큰술"}
                ],
                "steps": [
                    "소고기를 적당한 크기로 썹니다.",
                    "양파와 대파를 썹니다.",
                    "마늘을 다져서 양념장을 만듭니다.",
                    "고기를 양념에 재워둡니다.",
                    "팬에 고기를 볶다가 채소를 넣어 함께 볶습니다."
                ],
                "nutrition_info": {
                    "calories": 280,
                    "carbs": 5,
                    "protein": 25,
                    "fat": 18
                }
            }
        ]
        
        # 샘플 데이터 삽입
        for recipe in sample_recipes:
            result = supabase.table('recipes').insert(recipe).execute()
            print(f"✅ 샘플 레시피 삽입: {recipe['title']}")
        
        print("🎉 Supabase 테이블 생성 및 샘플 데이터 삽입 완료!")
        print("   이제 하이브리드 검색이 가능합니다.")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase 테이블 생성 실패: {e}")
        return False

if __name__ == "__main__":
    create_supabase_tables()
