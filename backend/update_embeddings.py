# backend/update_embeddings.py
import asyncio
import openai
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase 클라이언트
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# OpenAI 클라이언트
openai.api_key = os.getenv("OPENAI_API_KEY")

async def create_embedding(text: str) -> list:
    """텍스트를 임베딩으로 변환"""
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

async def update_all_embeddings():
    """모든 레시피의 임베딩 업데이트"""
    # 레시피 데이터 가져오기
    recipes = supabase.table('recipes_keto_enhanced').select('*').execute()
    
    for recipe in recipes.data:
        print(f"임베딩 생성 중: {recipe['title']}")
        
        # 제목과 내용을 합쳐서 임베딩 생성
        text = f"{recipe['title']} {recipe['content']}"
        embedding = await create_embedding(text)
        
        # Supabase에 임베딩 업데이트
        supabase.rpc('update_recipe_embedding', {
            'recipe_id': recipe['id'],
            'embedding_vector': embedding
        }).execute()
        
        print(f"✅ {recipe['title']} 임베딩 완료")
    
    print("🎉 모든 임베딩 업데이트 완료!")

if __name__ == "__main__":
    asyncio.run(update_all_embeddings())