# KetoHelper API 문서

## 개요

KetoHelper API는 키토제닉 다이어트를 위한 RESTful API입니다.

## 기본 정보

- **Base URL**: `http://localhost:8000/api/v1`
- **API 문서**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 인증

### Bearer Token 인증

```http
Authorization: Bearer <jwt_token>
```

## 엔드포인트

### 인증 (Authentication)

#### POST /auth/google
Google OAuth 로그인

**Request:**
```json
{
  "token": "google_oauth_token"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "name": "사용자명"
  }
}
```

#### GET /auth/me
현재 사용자 정보 조회

**Headers:**
- `Authorization: Bearer <jwt_token>`

**Response:**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "name": "사용자명",
  "profile_image": "image_url"
}
```

### 레시피 (Recipes)

#### GET /recipes
레시피 목록 조회

**Query Parameters:**
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지 크기 (기본값: 20)
- `meal_type`: 식사 시간 (breakfast, lunch, dinner, snack)
- `difficulty`: 난이도 (easy, medium, hard)
- `cooking_time`: 최대 조리 시간(분)

**Response:**
```json
{
  "items": [
    {
      "id": "recipe_id",
      "title": "레시피명",
      "description": "설명",
      "image_url": "이미지 URL",
      "cooking_time": 30,
      "difficulty": "easy",
      "nutrition": {
        "calories": 400,
        "carbs": 5,
        "protein": 25,
        "fat": 30
      },
      "rating": 4.5,
      "is_keto_friendly": true
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### GET /recipes/{recipe_id}
레시피 상세 조회

#### POST /recipes/recommendations
AI 기반 레시피 추천

**Request:**
```json
{
  "preferences": {
    "allergies": ["견과류"],
    "dislikes": ["버섯"]
  },
  "filters": {
    "meal_type": "dinner",
    "cooking_time": 30
  },
  "context": "오늘 저녁 메뉴 추천"
}
```

### 식당 (Restaurants)

#### GET /restaurants
식당 목록 조회

**Query Parameters:**
- `page`: 페이지 번호
- `page_size`: 페이지 크기
- `lat`: 위도
- `lng`: 경도
- `radius`: 검색 반경(km)
- `category`: 음식 카테고리
- `min_keto_score`: 최소 키토 점수

#### GET /restaurants/nearby
근처 식당 조회

**Query Parameters:**
- `lat`: 위도 (필수)
- `lng`: 경도 (필수)
- `radius`: 검색 반경(km, 기본값: 5)
- `limit`: 최대 결과 수 (기본값: 20)

### 사용자 (Users)

#### GET /users/me
현재 사용자 상세 정보

#### PATCH /users/preferences
사용자 선호도 업데이트

**Request:**
```json
{
  "allergies": ["견과류", "갑각류"],
  "dislikes": ["버섯"],
  "experience_level": "intermediate",
  "target_calories": 1800
}
```

## 에러 처리

모든 에러는 다음 형식으로 반환됩니다:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "details": {}
  }
}
```

### 상태 코드

- `200`: 성공
- `201`: 생성됨
- `400`: 잘못된 요청
- `401`: 인증 필요
- `403`: 권한 없음
- `404`: 리소스 없음
- `422`: 검증 오류
- `500`: 서버 오류
