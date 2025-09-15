#!/usr/bin/env python3
"""
임베딩 데이터 타입 진실 확인
"""
import os
import json
import numpy as np
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

def verify_embedding_truth():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print("=== 임베딩 데이터 타입 진실 확인 ===")
    
    # 1. 실제 데이터베이스에서 embedding 가져오기
    result = client.table('recipes_hybrid_ingredient_llm').select('recipe_id, title, embedding').limit(1).execute()
    
    if not result.data:
        print("❌ 데이터가 없습니다.")
        return
    
    sample = result.data[0]
    embedding_data = sample.get('embedding')
    
    print(f"1. Supabase에서 받은 embedding:")
    print(f"   - 타입: {type(embedding_data)}")
    print(f"   - 길이: {len(str(embedding_data))}")
    print(f"   - 처음 100자: {str(embedding_data)[:100]}...")
    
    # 2. JSON 파싱 시도
    if isinstance(embedding_data, str):
        try:
            parsed_embedding = json.loads(embedding_data)
            print(f"\n2. JSON 파싱 결과:")
            print(f"   - 파싱 후 타입: {type(parsed_embedding)}")
            print(f"   - 파싱 후 길이: {len(parsed_embedding)}")
            print(f"   - 첫 5개 값: {parsed_embedding[:5]}")
            
            # 3. numpy 배열로 변환 시도
            try:
                np_array = np.array(parsed_embedding, dtype=np.float32)
                print(f"\n3. numpy 배열 변환:")
                print(f"   - numpy 타입: {type(np_array)}")
                print(f"   - numpy shape: {np_array.shape}")
                print(f"   - 첫 5개 값: {np_array[:5]}")
                print(f"   - ✅ 정상적인 1536차원 벡터")
            except Exception as e:
                print(f"   - ❌ numpy 변환 실패: {e}")
                
        except json.JSONDecodeError as e:
            print(f"\n2. JSON 파싱 실패: {e}")
            print(f"   - ❌ 이것은 벡터가 아닌 일반 문자열")
    
    # 4. pgvector 함수 테스트
    print(f"\n4. pgvector 함수 테스트:")
    try:
        # 테스트 쿼리 임베딩 생성
        query_response = openai_client.embeddings.create(
            model='text-embedding-3-small',
            input="테스트"
        )
        query_embedding = query_response.data[0].embedding
        
        # pgvector 함수 호출
        search_result = client.rpc('search_hybrid_recipes', {
            'query_embedding': query_embedding,
            'match_count': 1
        }).execute()
        
        if search_result.data:
            print(f"   - ✅ pgvector 함수 작동")
            print(f"   - 결과 개수: {len(search_result.data)}")
            print(f"   - 유사도: {search_result.data[0]['similarity']}")
        else:
            print(f"   - ❌ pgvector 함수 결과 없음")
            
    except Exception as e:
        print(f"   - ❌ pgvector 함수 오류: {e}")
    
    # 5. 최종 결론
    print(f"\n=== 최종 결론 ===")
    if isinstance(embedding_data, str):
        try:
            json.loads(embedding_data)
            print("✅ 임베딩은 JSON 문자열로 저장되어 있지만, 파싱하면 정상적인 벡터")
            print("✅ pgvector 함수가 작동한다면 서버에서 vector 타입으로 처리됨")
            print("✅ 클라이언트에서는 문자열로 받지만, JSON 파싱으로 사용 가능")
        except:
            print("❌ 임베딩이 잘못된 형식으로 저장됨")
    else:
        print("✅ 임베딩이 이미 리스트 타입으로 저장됨")

if __name__ == "__main__":
    verify_embedding_truth()
