#!/usr/bin/env python3
"""
Enhanced Blob 방식 수정 - LLM 프롬프트 개선
"""
import os
import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI

# .env 파일 로드
load_dotenv('../.env')

class FixedEnhancedBlobApproachSupabase:
    """수정된 Enhanced Blob 방식"""

    def __init__(self):
        self.approach_name = "fixed_enhanced_blob"
        self.table_name = "recipes_enhanced_blob"
        
        # OpenAI 클라이언트 설정
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_model = 'text-embedding-3-small'
        self.embedding_dimension = 1536

        # Supabase 클라이언트 설정
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL과 SUPABASE_ANON_KEY 환경변수가 필요합니다.")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    def normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        if not text:
            return ""

        # 기본 정규화
        text = text.strip()
        text = ' '.join(text.split())  # 여러 공백을 하나로

        # 특수문자 정리
        replacements = {
            '·': ' ', '∙': ' ', '※': '', '★': '', '♥': '', '♡': '',
            '[': '', ']': '', '(': '', ')': '', '{': '', '}': '',
            '!': '', '?': '', '~': '', '`': '', '"': '', "'": ''
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text.strip()

    def _create_simple_enhanced_blob(self, recipe: Dict[str, Any]) -> str:
        """간단하고 효과적인 Enhanced Blob 생성 (LLM 없이)"""
        
        # 원본 데이터 수집
        title = self.normalize_text(recipe.get('title', ''))
        description = self.normalize_text(recipe.get('summary', ''))
        tags = recipe.get('tags', [])
        ingredients = recipe.get('ingredients', [])
        
        # 태그 정규화
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = []
        
        # 재료 정보 정규화
        ingredients_text = ""
        if isinstance(ingredients, list):
            ingredients_text = ", ".join([str(ing) for ing in ingredients[:10]])  # 상위 10개만
        elif isinstance(ingredients, str):
            ingredients_text = ingredients

        # 간단한 키워드 추출
        keywords = []
        
        # 제목에서 키워드 추출
        title_lower = title.lower()
        if '김밥' in title_lower or 'gimbap' in title_lower:
            keywords.extend(['김밥', '한식', '간식'])
        if '머핀' in title_lower or 'muffin' in title_lower:
            keywords.extend(['머핀', '베이킹', '디저트'])
        if '케이크' in title_lower or 'cake' in title_lower:
            keywords.extend(['케이크', '베이킹', '디저트'])
        if '키토' in title_lower or 'keto' in title_lower:
            keywords.extend(['키토', '다이어트', '저탄수'])
        if '다이어트' in title_lower or 'diet' in title_lower:
            keywords.extend(['다이어트', '저칼로리'])
        
        # 재료에서 키워드 추출
        ingredients_lower = ingredients_text.lower()
        if '아몬드' in ingredients_lower:
            keywords.append('아몬드')
        if '계란' in ingredients_lower:
            keywords.append('계란')
        if '치즈' in ingredients_lower:
            keywords.append('치즈')
        if '초콜릿' in ingredients_lower or '초콜렛' in ingredients_lower:
            keywords.append('초콜릿')
        
        # 중복 제거
        keywords = list(set(keywords))
        
        # Enhanced Blob 생성
        blob_parts = []
        
        # 1. 핵심 키워드들
        if keywords:
            blob_parts.append(" ".join(keywords))
        
        # 2. 정규화된 제목 (마케팅 단어 제거)
        clean_title = title
        # 마케팅 단어 제거
        marketing_words = ['키토제닉]', '[키토제닉', 'No 설탕', 'No 코코아', 'No 밀가루', '저탄수', '다이어트']
        for word in marketing_words:
            clean_title = clean_title.replace(word, '').strip()
        clean_title = ' '.join(clean_title.split())  # 공백 정리
        
        if clean_title:
            blob_parts.append(f"제목: {clean_title}")
        
        # 3. 설명
        if description:
            blob_parts.append(f"설명: {description}")
        
        # 4. 주요 재료 (상위 5개만)
        if ingredients_text:
            main_ingredients = ingredients_text.split(',')[:5]
            blob_parts.append(f"주요 재료: {', '.join(main_ingredients)}")
        
        # 5. 태그
        if tags:
            tag_text = ", ".join([str(tag) for tag in tags[:5]])
            blob_parts.append(f"태그: {tag_text}")
        
        return "\n".join(blob_parts)

    def _get_openai_embedding(self, text: str) -> List[float]:
        """OpenAI text-embedding-3-small로 임베딩 생성"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI embedding error: {e}")
            return [0.0] * self.embedding_dimension

    def save_recipe_embedding(self, recipe: Dict[str, Any]) -> bool:
        """수정된 Enhanced Blob 방식용 레시피 임베딩 저장"""
        try:
            # 간단하고 효과적인 Enhanced Blob 생성
            enhanced_blob = self._create_simple_enhanced_blob(recipe)
            
            # OpenAI text-embedding-3-small로 임베딩 생성
            embedding = self._get_openai_embedding(enhanced_blob)
            
            # 데이터 구조
            data = {
                'recipe_id': recipe.get('source_recipe_id', ''),
                'title': recipe.get('title', ''),
                'description': recipe.get('summary', ''),
                'tags': recipe.get('tags', []),
                'ingredients': recipe.get('ingredients', []),
                'cooking_method': '',
                'enhanced_blob': enhanced_blob,
                'embedding': embedding,
                'metadata': {
                    'approach': self.approach_name,
                    'blob_length': len(enhanced_blob),
                    'has_title': bool(recipe.get('title', '').strip()),
                    'ingredient_count': len(recipe.get('ingredients', []))
                }
            }

            result = self.supabase.table(self.table_name).upsert(data, on_conflict='recipe_id').execute()
            return True

        except Exception as e:
            print(f"Error saving recipe {recipe.get('source_recipe_id', 'unknown')}: {e}")
            return False

    def search_similar_recipes(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """수정된 Enhanced Blob 방식용 유사 레시피 검색"""
        try:
            # 쿼리 임베딩
            query_embedding = self._get_openai_embedding(query)

            # Enhanced Blob 방식 전용 검색 함수 사용
            result = self.supabase.rpc('search_enhanced_recipes', {
                'query_embedding': query_embedding,
                'match_count': top_k
            }).execute()

            if result.data:
                return result.data
            else:
                # fallback: 모든 데이터를 가져와서 클라이언트에서 계산
                return self._fallback_search(query_embedding, top_k)

        except Exception as e:
            print(f"Error in search: {e}")
            # fallback 검색
            query_embedding = self._get_openai_embedding(query)
            return self._fallback_search(query_embedding, top_k)

    def _fallback_search(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """백업 검색 방법"""
        try:
            import numpy as np
            result = self.supabase.table(self.table_name).select('*').execute()

            results = []
            query_embedding = np.array(query_embedding, dtype=np.float32)
            
            for row in result.data:
                embedding_data = row.get('embedding')
                if not embedding_data:
                    continue
                
                if isinstance(embedding_data, str):
                    try:
                        embedding_data = json.loads(embedding_data)
                    except:
                        continue
                
                stored_embedding = np.array(embedding_data, dtype=np.float32)
                
                # 코사인 유사도 계산
                norm_query = np.linalg.norm(query_embedding)
                norm_stored = np.linalg.norm(stored_embedding)
                
                if norm_query == 0 or norm_stored == 0:
                    similarity = 0.0
                else:
                    similarity = np.dot(query_embedding, stored_embedding) / (norm_query * norm_stored)

                results.append({
                    'recipe_id': row['recipe_id'],
                    'title': row['title'],
                    'enhanced_blob': row.get('enhanced_blob', ''),
                    'metadata': row.get('metadata', {}),
                    'similarity': float(similarity)
                })

            # 유사도 기준 정렬 후 top_k 반환
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]

        except Exception as e:
            print(f"Error in fallback search: {e}")
            return []

if __name__ == "__main__":
    # 테스트 실행
    approach = FixedEnhancedBlobApproachSupabase()
    print("수정된 Enhanced Blob Approach 초기화 완료")
    
    # 샘플 레시피로 테스트
    sample_recipe = {
        'source_recipe_id': 'test_fixed_001',
        'title': '키토제닉] 고소한맛 가득 아몬드 머핀 - No 설탕, No 코코아, No 밀가루',
        'summary': '아몬드 가루로 만든 고소한 머핀',
        'tags': ['키토', '다이어트', '저탄수'],
        'ingredients': ['아몬드 가루', '계란', '스테비아']
    }
    
    # Enhanced Blob 생성 테스트
    enhanced_blob = approach._create_simple_enhanced_blob(sample_recipe)
    print(f"\n✅ 수정된 Enhanced Blob:")
    print(enhanced_blob)
    
    # 저장 테스트
    if approach.save_recipe_embedding(sample_recipe):
        print("\n✅ 샘플 레시피 저장 성공")
        
        # 검색 테스트
        results = approach.search_similar_recipes("아몬드 머핀", 3)
        print(f"\n🔍 검색 결과: {len(results)}개")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['title'][:50]}... ({result['similarity']*100:.1f}%)")
    else:
        print("\n❌ 샘플 레시피 저장 실패")
