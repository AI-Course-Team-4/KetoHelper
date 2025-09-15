#!/usr/bin/env python3
"""
고도화된 Enhanced Blob 생성 (실제 데이터로 테스트)
"""
import os
import json
import re
from dotenv import load_dotenv
from supabase import create_client

# .env 파일 로드
load_dotenv('../.env')

def advanced_normalize_text(text: str) -> str:
    """고도화된 텍스트 정규화"""
    if not text:
        return ""

    # 기본 정규화
    text = text.strip()
    text = ' '.join(text.split())  # 여러 공백을 하나로

    # 특수문자 정리
    replacements = {
        '·': ' ', '∙': ' ', '※': '', '★': '', '♥': '', '♡': '',
        '[': '', ']': '', '(': '', ')': '', '{': '', '}': '',
        '!': '', '?': '', '~': '', '`': '', '"': '', "'": '',
        '|': ' ', '-': ' ', '_': ' ', '=': ' ', '+': ' ',
        '&': ' ', '@': ' ', '#': ' ', '$': ' ', '%': ' ',
        '^': ' ', '*': ' ', '\\': ' ', '/': ' '
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.strip()

def extract_ingredients_from_json(ingredients_data):
    """JSON 형태의 재료 데이터에서 재료명만 추출"""
    ingredients = []
    
    if isinstance(ingredients_data, str):
        try:
            ingredients_data = json.loads(ingredients_data)
        except:
            return []
    
    if isinstance(ingredients_data, list):
        for item in ingredients_data:
            if isinstance(item, dict):
                # {"name": "계란 15개", "amount": ""} 형태
                name = item.get('name', '')
                if name:
                    # 재료명만 추출 (양 제거)
                    clean_name = re.sub(r'\d+[가-힣]*\s*', '', name).strip()
                    if clean_name:
                        ingredients.append(clean_name)
            elif isinstance(item, str):
                # 문자열 형태
                clean_item = re.sub(r'\d+[가-힣]*\s*', '', item).strip()
                if clean_item:
                    ingredients.append(clean_item)
    
    return ingredients

def extract_keywords_advanced(title: str, ingredients: list, tags: list) -> list:
    """고도화된 키워드 추출"""
    keywords = []
    
    # 제목에서 키워드 추출
    title_lower = title.lower()
    
    # 요리 종류 키워드
    cuisine_keywords = {
        '김밥': ['김밥', '한식', '간식', '롤'],
        'gimbap': ['김밥', '한식', '간식', '롤'],
        '머핀': ['머핀', '베이킹', '디저트', '빵'],
        'muffin': ['머핀', '베이킹', '디저트', '빵'],
        '케이크': ['케이크', '베이킹', '디저트', '케이크'],
        'cake': ['케이크', '베이킹', '디저트', '케이크'],
        '쿠키': ['쿠키', '베이킹', '간식', '과자'],
        'cookie': ['쿠키', '베이킹', '간식', '과자'],
        '빵': ['빵', '베이킹', '빵'],
        'bread': ['빵', '베이킹', '빵'],
        '스콘': ['스콘', '베이킹', '간식'],
        'scone': ['스콘', '베이킹', '간식'],
        '마들렌': ['마들렌', '베이킹', '간식'],
        'madeleine': ['마들렌', '베이킹', '간식'],
        '치즈케이크': ['치즈케이크', '케이크', '디저트', '치즈'],
        'cheesecake': ['치즈케이크', '케이크', '디저트', '치즈'],
        '바스크': ['바스크', '치즈케이크', '케이크', '디저트'],
        'basque': ['바스크', '치즈케이크', '케이크', '디저트']
    }
    
    for keyword, related_words in cuisine_keywords.items():
        if keyword in title_lower:
            keywords.extend(related_words)
    
    # 다이어트/건강 키워드
    health_keywords = {
        '키토': ['키토', '저탄수', '고지방'],
        'keto': ['키토', '저탄수', '고지방'],
        '다이어트': ['다이어트', '저칼로리'],
        'diet': ['다이어트', '저칼로리'],
        '저탄수': ['저탄수', '키토'],
        '저칼로리': ['저칼로리', '다이어트'],
        '고단백': ['고단백', '단백질'],
        '고섬유': ['고섬유', '섬유질']
    }
    
    for keyword, related_words in health_keywords.items():
        if keyword in title_lower:
            keywords.extend(related_words)
    
    # 재료에서 키워드 추출
    ingredient_keywords = {
        '아몬드': ['아몬드', '견과류'],
        '계란': ['계란', '단백질'],
        '치즈': ['치즈', '유제품'],
        '크림': ['크림', '유제품'],
        '버터': ['버터', '유제품'],
        '초콜릿': ['초콜릿', '초콜렛', '초코'],
        '레몬': ['레몬', '과일'],
        '베리': ['베리', '과일'],
        '바나나': ['바나나', '과일'],
        '사과': ['사과', '과일'],
        '당근': ['당근', '채소'],
        '양배추': ['양배추', '채소'],
        '브로콜리': ['브로콜리', '채소'],
        '토마토': ['토마토', '채소'],
        '고구마': ['고구마', '채소'],
        '감자': ['감자', '채소'],
        '밀가루': ['밀가루', '곡물'],
        '설탕': ['설탕', '당분'],
        '꿀': ['꿀', '당분'],
        '시럽': ['시럽', '당분']
    }
    
    for ingredient in ingredients:
        ingredient_lower = ingredient.lower()
        for keyword, related_words in ingredient_keywords.items():
            if keyword in ingredient_lower:
                keywords.extend(related_words)
    
    # 태그에서 키워드 추출
    if tags:
        for tag in tags:
            tag_lower = str(tag).lower()
            if tag_lower in ['키토', '다이어트', '저탄수', '고단백', '저칼로리']:
                keywords.append(tag_lower)
    
    # 중복 제거 및 정렬
    keywords = list(set(keywords))
    keywords.sort()
    
    return keywords

def create_advanced_enhanced_blob(recipe: dict) -> str:
    """고도화된 Enhanced Blob 생성"""
    
    # 원본 데이터 수집
    title = advanced_normalize_text(recipe.get('title', ''))
    description = advanced_normalize_text(recipe.get('summary', ''))
    tags = recipe.get('tags', [])
    ingredients_data = recipe.get('ingredients', [])
    
    # 태그 정규화
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except:
            tags = []
    
    # 재료 정보 추출 및 정규화
    ingredients = extract_ingredients_from_json(ingredients_data)
    
    # 고도화된 키워드 추출
    keywords = extract_keywords_advanced(title, ingredients, tags)
    
    # Enhanced Blob 생성
    blob_parts = []
    
    # 1. 핵심 키워드들 (상위 10개만)
    if keywords:
        blob_parts.append(" ".join(keywords[:10]))
    
    # 2. 정규화된 제목 (마케팅 단어 제거)
    clean_title = title
    # 마케팅 단어 제거
    marketing_words = [
        '키토제닉]', '[키토제닉', 'No 설탕', 'No 코코아', 'No 밀가루', 
        '저탄수', '다이어트', '키토', 'Keto', 'KETO',
        '만들기', '레시피', '방법', '조리법', '요리법',
        '홈베이킹', '홈쿡', '집에서', '간편', '초간단',
        '맛있는', '고소한', '달콤한', '촉촉한', '부드러운'
    ]
    
    for word in marketing_words:
        clean_title = clean_title.replace(word, '').strip()
    
    # 연속된 공백 제거
    clean_title = ' '.join(clean_title.split())
    
    if clean_title:
        blob_parts.append(f"제목: {clean_title}")
    
    # 3. 설명 (간결하게)
    if description and len(description) > 10:
        # 설명이 너무 길면 앞부분만
        short_description = description[:100] + "..." if len(description) > 100 else description
        blob_parts.append(f"설명: {short_description}")
    
    # 4. 주요 재료 (상위 5개만)
    if ingredients:
        main_ingredients = ingredients[:5]
        blob_parts.append(f"주요 재료: {', '.join(main_ingredients)}")
    
    # 5. 태그 (상위 3개만)
    if tags:
        main_tags = [str(tag) for tag in tags[:3]]
        blob_parts.append(f"태그: {', '.join(main_tags)}")
    
    return "\n".join(blob_parts)

def test_advanced_blob_generation():
    print("=== 고도화된 Enhanced Blob 생성 테스트 (실제 데이터) ===")
    
    # Supabase에서 실제 데이터 가져오기
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    
    try:
        result = client.table('recipes_keto_raw').select('*').limit(10).execute()
        
        if not result.data:
            print("❌ 데이터가 없습니다.")
            return
        
        for i, recipe in enumerate(result.data, 1):
            print(f"\n{i}. 원본 제목: {recipe.get('title', '')[:60]}...")
            
            # 고도화된 Enhanced Blob 생성
            enhanced_blob = create_advanced_enhanced_blob(recipe)
            
            print(f"   Enhanced Blob:")
            print(f"   {enhanced_blob}")
            print(f"   ---")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_advanced_blob_generation()
