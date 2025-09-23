# 🚀 배포 가이드

## 배포 환경 검증 완료 ✅

이 프로젝트는 다음 배포 환경에서 정상 동작합니다:

### 필수 환경 변수

```bash
# 🔐 JWT 인증 (필수 - 배포시 강력한 시크릿으로 변경)
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXP_MINUTES=30
REFRESH_TOKEN_EXP_DAYS=30

# 🗄️ Supabase 데이터베이스 (필수)
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 🤖 AI API (필수)
GOOGLE_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_TOKENS=8192

# 🗺️ 카카오 API (필수)
KAKAO_REST_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 🍪 쿠키 설정 (프로덕션 환경)
COOKIE_SECURE=true
COOKIE_SAMESITE=none
COOKIE_DOMAIN=.yourdomain.com

# 🌐 CORS 설정 (프로덕션 환경)
FRONTEND_DOMAIN=https://yourdomain.com
VERCEL_PROJECT_NAME=your-project-name

# 🛠️ 애플리케이션 설정
DEBUG=false
ENVIRONMENT=production
```

## 배포 플랫폼별 가이드

### 1. Vercel (프론트엔드) + Railway/Render (백엔드)

**프론트엔드 (Vercel)**:
```bash
# vercel.json 이미 설정됨
npm run build
vercel --prod
```

**백엔드 (Railway/Render)**:
```bash
# 환경 변수 모두 설정 후
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 2. Docker 배포

**Dockerfile 생성 예시**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔧 배포 전 체크리스트

### 백엔드
- ✅ `PyJWT` 의존성 추가됨
- ✅ JWT 시크릿 강력한 값으로 설정
- ✅ CORS 설정 확인
- ✅ 쿠키 보안 설정 (HTTPS 환경)
- ✅ 데이터베이스 마이그레이션 실행

### 프론트엔드  
- ✅ API 엔드포인트 URL 설정
- ✅ 환경별 설정 분리
- ✅ HTTPS 적용

### 데이터베이스
- ✅ Supabase 프로덕션 환경 설정
- ✅ 마이그레이션 SQL 실행: `docs/database/2025.9.23-soohwan-database-optimization-migration.sql`
- ✅ Row Level Security (RLS) 활성화 확인

## 🚨 보안 고려사항

1. **JWT 시크릿**: 강력한 랜덤 값 사용
2. **쿠키 설정**: HTTPS 환경에서 `secure=true`
3. **CORS**: 필요한 도메인만 허용
4. **API 키**: 환경 변수로만 관리, 코드에 하드코딩 금지

## 🧪 배포 후 테스트

```bash
# 헬스 체크
curl https://your-backend.com/health

# API 문서 확인
curl https://your-backend.com/docs

# 프로필 API 테스트 (인증 후)
curl -X GET https://your-backend.com/api/v1/profile/master/allergies
```

## 🔍 모니터링

배포 후 확인할 포인트:
- 서버 응답 시간
- 데이터베이스 연결 상태  
- JWT 토큰 생성/검증
- 프로필 API 정상 동작
- 파일 업로드/다운로드

## 🎯 성능 최적화

배포 환경에서 권장 설정:
- 프로덕션용 데이터베이스 connection pool 설정
- Redis 캐시 활용 (선택사항)
- CDN 활용 (정적 파일)
- 로그 레벨 조정 (`INFO` 이상)
