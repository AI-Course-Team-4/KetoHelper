# 메뉴 정보 인터넷 검색 증강 전략

## 🎯 개요
메뉴명만으로는 판단하기 어려운 경우 인터넷 검색을 통해 메뉴 정보를 보완하는 방법을 단계별로 제시합니다.

## 📋 구현 단계

### **Phase 1: 간단한 하이브리드 접근 (추천 시작점)**

#### **1.1 기본 구조**
```python
def enrich_menu_with_fallback(menu_name, restaurant_context=None):
    # 1단계: 기본 규칙으로 시도
    basic_info = apply_simple_rules(menu_name)
    
    # 2단계: 신뢰도가 낮으면 검색으로 보완
    if basic_info.confidence < 0.6 or len(basic_info.get("main_ingredients", [])) < 3:
        search_info = await search_menu_simple(menu_name, restaurant_context)
        basic_info = merge_enrichment_data(basic_info, search_info)
    
    return basic_info
```

#### **1.2 간단한 웹 검색 (playwright-fetch)**
```python
async def search_menu_simple(menu_name, restaurant_name=None):
    """네이버 블로그 검색으로 메뉴 정보 보완"""
    
    # 검색 쿼리 생성
    queries = [
        f"{menu_name} 레시피",
        f"{menu_name} 재료",
        f"{restaurant_name} {menu_name}" if restaurant_name else menu_name
    ]
    
    search_results = []
    
    for query in queries:
        try:
            search_url = f"https://search.naver.com/search.naver?query={query}"
            content = await playwright_fetch(search_url)
            
            # 간단한 키워드 추출
            ingredients = extract_ingredients_from_text(content)
            if ingredients:
                search_results.extend(ingredients)
                
        except Exception as e:
            logger.warning(f"검색 실패: {query} - {e}")
            continue
    
    return {
        "main_ingredients": list(set(search_results))[:5],  # 중복 제거, 최대 5개
        "source": "search",
        "confidence": min(len(search_results) / 5, 1.0)  # 재료 개수 기반 신뢰도
    }
```

#### **1.3 간단한 패턴 매칭**
```python
def extract_ingredients_from_text(text):
    """텍스트에서 재료 정보 추출"""
    
    # 재료 관련 패턴
    patterns = [
        r"주재료[:\s]*([^,\.]+)",
        r"재료[:\s]*([^,\.]+)",
        r"필요재료[:\s]*([^,\.]+)",
        r"준비물[:\s]*([^,\.]+)"
    ]
    
    # 일반적인 재료 키워드
    common_ingredients = [
        "돼지고기", "소고기", "닭고기", "생선", "새우", "오징어", "문어",
        "김치", "두부", "콩나물", "시금치", "당근", "양파", "마늘",
        "고추장", "된장", "간장", "참기름", "들기름", "식용유",
        "밥", "국수", "면", "떡", "만두", "김", "계란"
    ]
    
    ingredients = []
    
    # 패턴 매칭으로 추출
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # 쉼표나 공백으로 분리
            items = re.split(r'[,，\s]+', match.strip())
            ingredients.extend([item.strip() for item in items if item.strip()])
    
    # 일반 재료 키워드 검색
    for ingredient in common_ingredients:
        if ingredient in text:
            ingredients.append(ingredient)
    
    return list(set(ingredients))  # 중복 제거
```

#### **1.4 데이터 병합 로직**
```python
def merge_enrichment_data(basic_info, search_info):
    """기본 정보와 검색 정보 병합"""
    
    merged = basic_info.copy()
    
    # 재료 정보 병합 (중복 제거)
    basic_ingredients = set(basic_info.get("main_ingredients", []))
    search_ingredients = set(search_info.get("main_ingredients", []))
    merged["main_ingredients"] = list(basic_ingredients.union(search_ingredients))[:5]
    
    # 신뢰도 업데이트
    if search_info.get("confidence", 0) > basic_info.get("confidence", 0):
        merged["confidence"] = search_info["confidence"]
        merged["source"] = "hybrid"  # 기본 + 검색
    
    return merged
```

### **Phase 2: 고도화 (필요시 업그레이드)**

#### **2.1 다중 검색 엔진 활용**
```python
async def search_menu_advanced(menu_name, restaurant_context=None):
    """다중 검색 엔진으로 메뉴 정보 수집"""
    
    search_engines = [
        ("naver", f"https://search.naver.com/search.naver?query={menu_name}+레시피"),
        ("google", f"https://www.google.com/search?q={menu_name}+재료"),
        ("youtube", f"https://www.youtube.com/results?search_query={menu_name}+요리")
    ]
    
    all_results = []
    
    for engine, url in search_engines:
        try:
            content = await playwright_fetch(url)
            results = extract_ingredients_from_text(content)
            all_results.extend(results)
            
            # Rate limiting
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.warning(f"{engine} 검색 실패: {e}")
    
    return {
        "main_ingredients": list(set(all_results))[:5],
        "source": "multi_search",
        "confidence": min(len(all_results) / 10, 1.0)
    }
```

#### **2.2 검색 API 활용 (Google Custom Search)**
```python
import requests

async def search_with_google_api(menu_name, api_key, search_engine_id):
    """Google Custom Search API 활용"""
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": f"{menu_name} 레시피 재료",
        "num": 5
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # 검색 결과에서 텍스트 추출
        search_text = ""
        for item in data.get("items", []):
            search_text += item.get("snippet", "") + " "
        
        ingredients = extract_ingredients_from_text(search_text)
        
        return {
            "main_ingredients": ingredients,
            "source": "google_api",
            "confidence": 0.8  # API 결과는 높은 신뢰도
        }
        
    except Exception as e:
        logger.error(f"Google API 검색 실패: {e}")
        return {"main_ingredients": [], "source": "api_failed", "confidence": 0.0}
```

#### **2.3 AI 기반 정보 추출**
```python
async def extract_with_llm(menu_name, search_context):
    """LLM을 활용한 정교한 정보 추출"""
    
    prompt = f"""
    다음 메뉴에 대한 정보를 추출해주세요:
    메뉴명: {menu_name}
    검색 결과: {search_context}
    
    다음 형식으로 답변해주세요:
    - 주재료: (최대 5개)
    - 조리법: (grill, stew, stir-fry 등)
    - 매운 정도: (0-3)
    - 온도: (hot, cold, room)
    - 알레르기: (계란, 우유, 대두, 갑각류 등)
    """
    
    # OpenAI API 또는 로컬 LLM 호출
    response = await call_llm_api(prompt)
    
    return parse_llm_response(response)
```

### **Phase 3: 최적화 및 모니터링**

#### **3.1 캐싱 시스템**
```python
class MenuSearchCache:
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def get_cached_result(self, menu_name):
        """캐시된 검색 결과 조회"""
        query = """
        SELECT search_result, created_at 
        FROM menu_search_cache 
        WHERE menu_name = %s AND created_at > NOW() - INTERVAL '7 days'
        """
        result = await self.db.fetch_one(query, (menu_name,))
        return result
    
    async def cache_result(self, menu_name, search_result):
        """검색 결과 캐시 저장"""
        query = """
        INSERT INTO menu_search_cache (menu_name, search_result, created_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (menu_name) DO UPDATE SET
        search_result = EXCLUDED.search_result,
        created_at = EXCLUDED.created_at
        """
        await self.db.execute(query, (menu_name, json.dumps(search_result)))
```

#### **3.2 품질 모니터링**
```python
def monitor_search_quality():
    """검색 결과 품질 모니터링"""
    
    metrics = {
        "search_success_rate": 0,
        "avg_ingredients_found": 0,
        "confidence_distribution": {},
        "source_effectiveness": {}
    }
    
    # 일일 리포트 생성
    generate_daily_report(metrics)
    
    # 품질이 낮은 메뉴 식별
    low_quality_menus = identify_low_quality_menus()
    
    return metrics, low_quality_menus
```

## 🚀 구현 우선순위

### **1단계 (즉시 구현)**
- ✅ 간단한 네이버 검색 (playwright-fetch)
- ✅ 기본 패턴 매칭
- ✅ 하이브리드 풍부화 로직

### **2단계 (1-2주 후)**
- ✅ 다중 검색 엔진
- ✅ 캐싱 시스템
- ✅ 품질 모니터링

### **3단계 (필요시)**
- ✅ Google API 연동
- ✅ LLM 기반 추출
- ✅ 고급 품질 검증

## 📊 성능 지표

### **목표 지표**
- **검색 성공률**: ≥ 80%
- **평균 재료 추출**: ≥ 3개
- **응답 시간**: ≤ 5초
- **캐시 히트율**: ≥ 60%

### **모니터링 대시보드**
- 검색 성공/실패율
- 재료 추출 개수 분포
- 소스별 효과성
- 응답 시간 트렌드

## 🔧 설정 파일 예시

### **search_config.yaml**
```yaml
search_engines:
  naver:
    enabled: true
    rate_limit: 1.0  # requests per second
    timeout: 10
  google:
    enabled: false
    api_key: ""
    search_engine_id: ""
    rate_limit: 0.5

extraction:
  max_ingredients: 5
  confidence_threshold: 0.6
  cache_ttl_days: 7

patterns:
  ingredient_patterns:
    - "주재료[:\s]*([^,\.]+)"
    - "재료[:\s]*([^,\.]+)"
  common_ingredients:
    - "돼지고기"
    - "소고기"
    - "김치"
    # ... 더 많은 재료
```

---
**작성일**: 2025-01-27  
**버전**: v1.0  
**상태**: 구현 준비 완료
