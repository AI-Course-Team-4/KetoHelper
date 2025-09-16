# Supabase 설정 가이드

## 1. Supabase 프로젝트 생성

1. [supabase.com](https://supabase.com)에 회원가입/로그인
2. "New Project" 클릭
3. Organization 선택 (개인 계정 사용)
4. 프로젝트 정보 입력:
   - **Name**: `keto-Helper` (또는 원하는 이름)
   - **Database Password**: 강력한 비밀번호 설정 (⚠️ **반드시 기록해두세요!**)
   - **Region**: Asia Northeast (Seoul) - `ap-northeast-2`
5. "Create new project" 클릭

## 2. 연결 정보 수집

### Database 연결 정보
`Settings → Database`에서 확인:

```
Host: db.xxxxxxxxxxxxx.supabase.co
Database name: postgres
Port: 5432
User: postgres
Password: [설정한 비밀번호]
```

### API 키 정보
`Settings → API`에서 확인:

```
Project URL: https://xxxxxxxxxxxxx.supabase.co
anon (public): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role (secret): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 3. .env 파일 생성

`backend/.env` 파일 생성:

```bash
# 데이터베이스 설정 (실제 값으로 교체)
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# AI/LLM 설정 (OpenAI API 키 필요)
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-3.5-turbo

# 카카오 API 설정 (카카오 디벨로퍼스에서 발급)
KAKAO_REST_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 애플리케이션 설정
DEBUG=true
ENVIRONMENT=development

# RAG 설정
MAX_SEARCH_RESULTS=5
SIMILARITY_THRESHOLD=0.7

# 캐시 설정
ENABLE_CACHE=true
CACHE_TTL_SECONDS=3600
```

## 4. 데이터베이스 스키마 설정

1. Supabase 대시보드에서 `SQL Editor` 클릭
2. "New query" 생성
3. `docs/database_setup.sql` 파일 내용을 복사하여 붙여넣기
4. "Run" 버튼 클릭하여 실행

## 5. pgvector 확장 설치 확인

SQL Editor에서 다음 쿼리 실행:

```sql
-- pgvector 확장 설치 확인
CREATE EXTENSION IF NOT EXISTS vector;

-- 설치 확인
SELECT * FROM pg_extension WHERE extname = 'vector';
```

## 6. 연결 테스트

백엔드 서버 실행하여 연결 확인:

```bash
cd backend
uvicorn app.main:app --reload
```

브라우저에서 `http://localhost:8000/health` 접속하여 확인

## 🔐 보안 주의사항

- **service_role 키**: 절대 프론트엔드나 공개 저장소에 노출하지 말 것
- **데이터베이스 비밀번호**: 안전한 곳에 별도 보관
- **.env 파일**: `.gitignore`에 추가하여 버전 관리에서 제외

## 📞 문제 해결

### 연결 실패 시 체크리스트:
- [ ] 데이터베이스 비밀번호 정확성
- [ ] Supabase 프로젝트가 활성 상태인지 확인
- [ ] 방화벽/네트워크 설정 확인
- [ ] DATABASE_URL 형식 정확성

### 일반적인 오류:
1. **"password authentication failed"**: 비밀번호 확인
2. **"connection timeout"**: 네트워크 연결 확인
3. **"database does not exist"**: DATABASE_URL의 데이터베이스명 확인 (postgres)
