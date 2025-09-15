#!/usr/bin/env python3
"""
Enhanced Blob 생성 테스트 (임베딩 없이)
"""
import os
import json
from dotenv import load_dotenv
from supabase import create_client

# .env 파일 로드
load_dotenv('../.env')

def normalize_text(text: str) -> str:
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

def create_simple_enhanced_blob(recipe: dict) -> str:
    """간단하고 효과적인 Enhanced Blob 생성"""
    
    # 원본 데이터 수집
    title = normalize_text(recipe.get('title', ''))
    description = normalize_text(recipe.get('summary', ''))
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
    if '쿠키' in title_lower or 'cookie' in title_lower:
        keywords.extend(['쿠키', '베이킹', '간식'])
    if '빵' in title_lower or 'bread' in title_lower:
        keywords.extend(['빵', '베이킹'])
    if '스콘' in title_lower or 'scone' in title_lower:
        keywords.extend(['스콘', '베이킹', '간식'])
    
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
    if '크림' in ingredients_lower:
        keywords.append('크림')
    if '버터' in ingredients_lower:
        keywords.append('버터')
    if '밀가루' in ingredients_lower:
        keywords.append('밀가루')
    if '설탕' in ingredients_lower:
        keywords.append('설탕')
    
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
    marketing_words = ['키토제닉]', '[키토제닉', 'No 설탕', 'No 코코아', 'No 밀가루', '저탄수', '다이어트', '키토', 'Keto']
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

def test_blob_generation():
    print("=== Enhanced Blob 생성 테스트 (10개 샘플) ===")
    
    # Supabase에서 샘플 데이터 가져오기
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    
    try:
        result = client.table('recipes_keto_raw').select('*').limit(10).execute()
        
        if not result.data:
            print("❌ 데이터가 없습니다.")
            return
        
        for i, recipe in enumerate(result.data, 1):
            print(f"\n{i}. 원본 제목: {recipe.get('title', '')[:60]}...")
            
            # Enhanced Blob 생성
            enhanced_blob = create_simple_enhanced_blob(recipe)
            
            print(f"   Enhanced Blob:")
            print(f"   {enhanced_blob}")
            print(f"   ---")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_blob_generation()
