## 📋 변경 사항
- [x] 새로운 기능 추가
- [x] 버그 수정
- [x] 문서 업데이트
- [ ] 리팩토링
- [ ] 테스트 추가

## 🔍 상세 설명
소셜 로그인 ID 충돌 문제를 해결하기 위해 `provider` 컬럼을 추가했습니다.

### 문제 상황
- 구글, 카카오, 네이버 소셜 로그인에서 동일한 사용자명이 있을 경우 ID 충돌 발생
- 카카오는 UUID 형태의 ID를 제공하지만, 구글과 네이버는 다른 형태의 ID 제공
- 현재 `id` 컬럼만으로는 어떤 소셜 로그인 플랫폼인지 구분 불가

### 해결 방법
1. **`provider` 컬럼 추가**: `users` 테이블에 소셜 로그인 플랫폼 구분 컬럼 추가
2. **백엔드 코드 수정**: 각 소셜 로그인에서 `provider` 값 설정
3. **제약 조건 추가**: `(provider, id)` 조합이 유니크하도록 설정

### 변경된 파일
- `backend/app/shared/api/auth.py`: 카카오, 네이버 로그인에 `provider` 설정 추가
- `docs/add_social_login_columns.sql`: `provider` 컬럼 추가 SQL

## 🧪 테스트
- [x] 기존 테스트 통과
- [ ] 새로운 테스트 추가
- [x] 수동 테스트 완료

### 테스트 시나리오
1. **구글 로그인**: `provider = "google"` 설정 확인
2. **카카오 로그인**: `provider = "kakao"` 설정 확인  
3. **네이버 로그인**: `provider = "naver"` 설정 확인
4. **ID 충돌 방지**: 같은 사용자명이어도 다른 플랫폼이면 다른 사용자로 인식

## 📸 스크린샷 (UI 변경 시)
- 데이터베이스 스키마 변경 (provider 컬럼 추가)
- 소셜 로그인 플로우 변경 없음 (백엔드 내부 처리)

## 📚 관련 이슈
- 소셜 로그인 ID 충돌 문제 해결
- 사용자 식별 정확성 향상
- 다중 소셜 로그인 플랫폼 지원 강화

## 🔧 기술적 세부사항

### 데이터베이스 변경
```sql
-- provider 컬럼 추가
ALTER TABLE users 
ADD COLUMN provider TEXT CHECK (provider IN ('google', 'kakao', 'naver'));

-- 유니크 제약 조건 추가
ALTER TABLE users 
ADD CONSTRAINT unique_provider_id UNIQUE (provider, id);
```

### 백엔드 변경
```python
# 카카오 로그인
profile = {
    "id": str(data.get("id")),
    "email": kakao_account.get("email", ""),
    "name": kakao_account.get("profile", {}).get("nickname", ""),
    "picture": kakao_account.get("profile", {}).get("profile_image_url", ""),
    "provider": "kakao",  # ← 추가
}

# 네이버 로그인
profile = {
    "id": resp.get("id"),
    "email": resp.get("email", ""),
    "name": resp.get("name") or resp.get("nickname") or "",
    "picture": resp.get("profile_image", ""),
    "provider": "naver",  # ← 추가
}
```

## ✅ 검증 완료
- [x] SQL 문법 검증
- [x] 백엔드 코드 수정 완료
- [x] 소셜 로그인 플로우 분석 완료
- [x] ID 충돌 방지 로직 검증 완료
