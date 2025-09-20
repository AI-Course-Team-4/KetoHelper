# Restaurant 모듈 🏪

키토 친화적 식당 검색 및 추천을 담당하는 모듈입니다.

## 📁 폴더 구조

```
restaurant/
├── agents/          # 식당 검색 에이전트들
├── api/            # 식당 관련 API 엔드포인트
├── models/         # 식당 데이터 모델
├── prompts/        # 식당 검색용 프롬프트 템플릿
├── tools/          # 식당 검색 도구들
└── README.md       # 이 파일
```

## 🤖 에이전트 개인화 가이드

### RestaurantAgent 커스터마이징

`agents/restaurant_agent.py`의 `RestaurantAgent` 클래스를 개인화하여 자신만의 식당 검색 에이전트를 만들 수 있습니다.

#### 1. 기본 설정 변경

```python
class RestaurantAgent:
    # 개인화 설정 - 이 부분을 수정하세요
    AGENT_NAME = "나만의 식당 추천 전문가"
    PROMPT_FILES = {
        "search_improvement": "my_search_optimization",    # 검색 쿼리 개선
        "search_failure": "my_search_failure",            # 검색 실패 시 응답
        "recommendation": "my_restaurant_recommendation"   # 추천 생성
    }
    TOOL_FILES = {
        "place_search": "my_place_search_tool"           # 장소 검색 도구
    }
```

#### 2. 개인 프롬프트 파일 생성

각 기능별로 프롬프트 파일을 생성하세요:

**prompts/my_search_optimization.py** - 검색 쿼리 개선
```python
PLACE_SEARCH_IMPROVEMENT_PROMPT = """
사용자의 식당 검색 요청을 분석하여 더 효과적인 검색 키워드를 생성하세요.

사용자 메시지: "{message}"

여기에 자신만의 검색 최적화 로직을 작성...
"""

# 다른 접근법들
SEARCH_IMPROVEMENT_PROMPT = "..."
PROMPT = "..."
```

**prompts/my_search_failure.py** - 검색 실패 처리
```python
PLACE_SEARCH_FAILURE_PROMPT = """
식당 검색 결과가 없을 때 도움이 되는 대안을 제시하세요.

검색 요청: "{message}"

여기에 자신만의 실패 처리 로직을 작성...
"""
```

**prompts/my_restaurant_recommendation.py** - 추천 생성
```python
RESTAURANT_RECOMMENDATION_PROMPT = """
검색된 식당들을 바탕으로 키토 식단 관점에서 개인화된 추천을 생성하세요.

사용자 요청: "{message}"
식당 목록: {restaurants}
사용자 프로필: {profile}

여기에 자신만의 추천 로직을 작성...
"""
```

#### 3. 개인 도구 파일 생성 (선택사항)

**tools/my_place_search_tool.py**
```python
class MyPlaceSearchTool:
    """자신만의 장소 검색 도구"""
    
    async def search(self, query: str, lat: float, lng: float, radius: int):
        # 자신만의 검색 로직
        # 다른 검색 API 사용, 필터링 로직 추가 등
        return [
            {
                "id": "place_001",
                "name": "키토 프렌들리 식당",
                "address": "서울시 강남구...",
                "category": "스테이크하우스",
                "keto_score": 9
            }
        ]
```

#### 4. 에이전트 인스턴스 생성

```python
# 기본 에이전트
agent = RestaurantAgent()

# 개인화된 에이전트
my_agent = RestaurantAgent(
    prompt_files={
        "search_improvement": "my_search_optimization",
        "search_failure": "my_search_failure",
        "recommendation": "my_restaurant_recommendation"
    },
    tool_files={
        "place_search": "my_place_search_tool"
    },
    agent_name="내 전용 식당 가이드"
)
```

## 📝 프롬프트 작성 가이드

### 검색 쿼리 개선 프롬프트

**목적**: 사용자 요청을 효과적인 검색 키워드로 변환
**입력 변수**:
- `{message}`: 사용자 검색 요청

**출력 형식**: 쉼표로 구분된 키워드
```
"스테이크하우스", "구이 전문점", "키토 카페"
```

**프롬프트 예시**:
```python
SEARCH_IMPROVEMENT_PROMPT = """
사용자의 식당 검색 요청을 키토 친화적 관점에서 분석하여 효과적인 검색 키워드를 생성하세요.

사용자 메시지: "{message}"

키토 식단 적합성을 고려한 키워드 생성 기준:
1. 저탄수화물 메뉴가 많은 업종 우선
2. 육류, 해산물, 샐러드 전문점 포함
3. 밀가루, 설탕 사용이 적은 음식점
4. 맞춤 주문이 가능한 곳

최대 3개의 검색 키워드를 쉼표로 구분하여 제시하세요.
"""
```

### 검색 실패 응답 프롬프트

**목적**: 검색 결과가 없을 때 유용한 대안 제시
**입력 변수**:
- `{message}`: 원래 검색 요청

**출력 형식**: 친근한 안내 메시지

**프롬프트 예시**:
```python
SEARCH_FAILURE_PROMPT = """
'{message}' 검색 결과가 없을 때 사용자에게 도움이 되는 응답을 생성하세요.

응답에 포함할 내용:
1. 검색 결과가 없음을 친근하게 알림
2. 키토 친화적 대안 식당 유형 제안
3. 검색 범위 확대 제안 (반경 증가, 다른 지역)
4. 일반적인 키토 외식 팁
5. 격려와 재검색 유도

친근하고 도움이 되는 톤으로 200-300자 내외로 작성하세요.
"""
```

### 추천 생성 프롬프트

**목적**: 검색된 식당들을 개인화하여 추천
**입력 변수**:
- `{message}`: 원래 요청
- `{restaurants}`: 검색된 식당 목록
- `{profile}`: 사용자 프로필

**출력 형식**: 구조화된 추천 메시지

**프롬프트 예시**:
```python
RECOMMENDATION_PROMPT = """
검색된 식당들을 바탕으로 키토 식단 관점에서 개인화된 추천을 생성하세요.

사용자 요청: "{message}"
식당 목록:
{restaurants}

사용자 프로필: {profile}

추천 응답 형식:
🍽️ **키토 친화적 식당 추천**

**1. [식당명]** ⭐ 키토 점수: X/10
- 🥩 추천 메뉴: [구체적 메뉴명과 이유]
- 💡 주문 팁: [키토 최적화 주문법]
- 📍 위치: [간단한 위치 설명]
- ⚠️ 주의사항: [알레르기나 제약사항 고려]

**2. [식당명]** ⭐ 키토 점수: X/10
- 🥩 추천 메뉴: [구체적 메뉴명과 이유]
- 💡 주문 팁: [키토 최적화 주문법]
- 📍 위치: [간단한 위치 설명]

🎯 **개인 맞춤 조언**
[사용자 프로필(알레르기, 선호도)을 고려한 추가 조언]

실용적이고 친근한 톤으로 작성해주세요.
"""
```

## 🔧 API 사용법

### 식당 검색

```python
POST /api/restaurant/search
{
    "message": "강남역 근처 키토 식당 추천해줘",
    "location": {
        "lat": 37.4979,
        "lng": 127.0276
    },
    "radius_km": 2.0,
    "profile": {
        "allergies": ["새우"],
        "dislikes": ["매운음식"]
    }
}
```

### 응답 형식

```json
{
    "response": "🍽️ **키토 친화적 식당 추천**\n\n**1. 스테이크팩토리** ⭐ 키토 점수: 9/10...",
    "restaurants": [
        {
            "id": "place_001",
            "name": "스테이크팩토리",
            "address": "서울시 강남구 역삼동...",
            "category": "스테이크하우스",
            "keto_score": 9,
            "why": ["고품질 소고기", "저탄수 사이드"],
            "tips": ["감자 대신 버섯 요청", "소스 별도 제공 요청"]
        }
    ],
    "search_keywords": ["스테이크하우스", "구이전문점"],
    "tool_calls": [
        {
            "tool": "restaurant_search",
            "results_count": 5
        }
    ]
}
```

## 🛠️ 도구 개발 가이드

### 장소 검색 도구

도구 클래스는 다음 메서드를 구현해야 합니다:

```python
class MyPlaceSearchTool:
    async def search(self, query: str, lat: float, lng: float, radius: int) -> List[Dict]:
        """
        장소 검색
        
        Args:
            query: 검색 키워드
            lat: 위도
            lng: 경도  
            radius: 검색 반경 (미터)
            
        Returns:
            List[{
                "id": str,
                "name": str,
                "address": str,
                "category": str,
                "phone": str (선택),
                "rating": float (선택),
                "distance": int (선택, 미터)
            }]
        """
        pass
```

### 사용자 정의 검색 도구 예시

**네이버 지도 API 연동**
```python
# tools/naver_place_search.py
import requests

class NaverPlaceSearch:
    def __init__(self):
        self.client_id = "your_naver_client_id"
        self.client_secret = "your_naver_client_secret"
    
    async def search(self, query, lat, lng, radius):
        # 네이버 지도 API 호출
        url = "https://openapi.naver.com/v1/search/local.json"
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        params = {
            "query": query,
            "display": 10,
            "sort": "distance"
        }
        
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        return self._parse_naver_results(data)
    
    def _parse_naver_results(self, data):
        results = []
        for item in data.get("items", []):
            results.append({
                "id": item.get("link", "").split("/")[-1],
                "name": item.get("title", "").replace("<b>", "").replace("</b>", ""),
                "address": item.get("address", ""),
                "category": item.get("category", ""),
                "phone": item.get("telephone", ""),
                "rating": 0  # 네이버에서 제공하지 않음
            })
        return results
```

**카카오맵 API 연동**
```python
# tools/kakao_place_search.py
import requests

class KakaoPlaceSearch:
    def __init__(self):
        self.api_key = "your_kakao_api_key"
    
    async def search(self, query, lat, lng, radius):
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        
        params = {
            "query": query,
            "x": lng,
            "y": lat,
            "radius": radius,
            "size": 10
        }
        
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        return self._parse_kakao_results(data)
```

## 🎯 검색 최적화 전략

### 키토 친화도별 키워드 매핑

```python
KETO_FRIENDLY_KEYWORDS = {
    "고급": ["스테이크하우스", "고급 레스토랑", "파인다이닝"],
    "일반": ["구이전문점", "샤브샤브", "생선구이"],
    "간편": ["샐러드바", "키토카페", "닭가슴살 전문점"],
    "해산물": ["회집", "조개구이", "새우전문점"],
    "육류": ["갈비집", "삼겹살", "소고기 전문점"]
}

def optimize_search_keywords(message: str) -> List[str]:
    """메시지 분석으로 최적 키워드 선택"""
    keywords = []
    
    if "고급" in message or "특별한" in message:
        keywords.extend(KETO_FRIENDLY_KEYWORDS["고급"])
    elif "간단" in message or "빠른" in message:
        keywords.extend(KETO_FRIENDLY_KEYWORDS["간편"])
    
    # 음식 유형별 추가
    if any(word in message for word in ["고기", "스테이크", "갈비"]):
        keywords.extend(KETO_FRIENDLY_KEYWORDS["육류"])
    
    return keywords[:3]
```

### 지역별 특화 검색

```python
REGIONAL_SPECIALTIES = {
    "강남": ["고급 스테이크", "오마카세", "와인바"],
    "홍대": ["키토 브런치", "샐러드 카페", "헬시 푸드"],
    "이태원": ["외국 음식", "글루텐프리", "키토 디저트"],
    "명동": ["한우 전문점", "해산물", "전통 구이"]
}
```

### 시간대별 추천

```python
TIME_BASED_RECOMMENDATIONS = {
    "breakfast": ["브런치 카페", "계란 요리", "키토 베이커리"],
    "lunch": ["샐러드바", "단백질 도시락", "헬시 레스토랑"],
    "dinner": ["스테이크하우스", "구이 전문점", "고급 레스토랑"],
    "late_night": ["치킨", "야식", "24시간 식당"]
}
```

## 🔍 고급 기능

### 개인화된 키토 점수 시스템

```python
# prompts/personalized_scoring.py
PERSONALIZED_SCORING_PROMPT = """
다음 식당을 사용자의 키토 목표에 맞춰 평가하세요.

식당 정보: {restaurant_info}
사용자 프로필: {user_profile}
키토 목표: {keto_goals}

평가 기준:
1. 탄수화물 제한 수준 (매우 엄격: 5g 이하, 일반적: 20g 이하)
2. 개인 알레르기 및 제약사항
3. 식사 목적 (체중감량, 유지, 근육증가)
4. 예산 고려사항

1-10점 점수와 개인화된 이유를 제공하세요.
"""
```

### 동적 반경 조정

```python
def adjust_search_radius(base_radius: float, density: str, user_urgency: str) -> float:
    """지역 밀도와 사용자 급함 정도에 따라 검색 반경 조정"""
    
    density_multiplier = {
        "high": 0.5,    # 강남, 홍대 등
        "medium": 1.0,  # 일반 지역
        "low": 2.0      # 외곽 지역
    }
    
    urgency_multiplier = {
        "urgent": 0.7,    # "지금 당장", "빨리"
        "normal": 1.0,    # 일반
        "flexible": 1.5   # "괜찮은 곳이면", "시간 여유"
    }
    
    return base_radius * density_multiplier.get(density, 1.0) * urgency_multiplier.get(user_urgency, 1.0)
```

## 📚 개발자 팁

### 1. API 키 관리
- 각 검색 API의 무료 한도 확인
- 환경변수로 API 키 관리
- 백업 검색 서비스 준비

### 2. 검색 품질 향상
- 사용자 피드백 수집
- 인기 검색어 분석
- 지역별 맞춤 키워드 업데이트

### 3. 성능 최적화
- 검색 결과 캐싱
- 중복 제거 알고리즘 개선
- 비동기 검색으로 응답 속도 향상

## 🤝 협업 가이드

### 지역별 전문화

```python
# 팀원 A - 강남/서초 전문
gangnam_agent = RestaurantAgent(
    prompt_files={
        "search_improvement": "gangnam_search_optimization",
        "recommendation": "gangnam_restaurant_recommendation"
    },
    agent_name="강남 맛집 전문가"
)

# 팀원 B - 홍대/마포 전문
hongdae_agent = RestaurantAgent(
    prompt_files={
        "search_improvement": "hongdae_search_optimization", 
        "recommendation": "hongdae_restaurant_recommendation"
    },
    agent_name="홍대 맛집 전문가"
)
```

### 검색 API 분담

- **팀원 A**: 카카오맵 API 도구 개발
- **팀원 B**: 네이버 지도 API 도구 개발  
- **팀원 C**: 구글 플레이스 API 도구 개발
- **팀원 D**: 통합 검색 도구 개발

### 프롬프트 품질 관리

1. **A/B 테스트**: 다른 프롬프트로 같은 검색 비교
2. **사용자 만족도**: 추천 결과에 대한 피드백 수집
3. **정확도 측정**: 실제 방문 후기와 추천 일치도 확인

---

💡 **새로운 검색 API나 더 나은 추천 로직 아이디어가 있다면 팀과 공유해주세요!**
