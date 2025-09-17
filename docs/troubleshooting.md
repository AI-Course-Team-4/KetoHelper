# 문제 해결 가이드

## 🚨 백엔드 서버 실행 오류

### 1. "No module named 'supabase'" 오류

**해결 방법**:
```bash
cd backend
pip install supabase
```

### 2. "No module named 'pgvector'" 오류

**해결 방법**:
```bash
pip install pgvector
```

### 3. "No module named 'langgraph'" 오류

**해결 방법**:
```bash
pip install langchain langgraph
```

### 4. 한번에 모든 의존성 설치

**Windows**:
```bash
cd backend
install_dependencies.bat
```

**또는 수동으로**:
```bash
cd backend
pip install -r requirements.txt
```

## 🔧 환경 설정 오류

### 1. DATABASE_URL 설정 안됨

**해결 방법**:
1. `backend/.env` 파일 생성
2. Supabase 정보 입력:
```
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
```

### 2. API 키 없음

**임시 해결** (테스트용):
- `backend/test_server.py` 실행 (API 키 없이도 실행 가능)

**완전 해결**:
- Supabase, OpenAI, 카카오 API 키 발급 후 `.env` 설정

## 🖥️ 프론트엔드 오류

### 1. "Cannot find module 'tailwindcss-animate'"

**해결 방법**:
```bash
cd frontend
npm install tailwindcss-animate @radix-ui/react-scroll-area @radix-ui/react-toast
```

### 2. 환경 변수 오류

**해결 방법**:
`frontend/.env` 파일 생성:
```
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
VITE_KAKAO_JS_KEY=xxxxxxxx
```

## 🗄️ 데이터베이스 연결 오류

### 1. "password authentication failed"

**원인**: Supabase 비밀번호 오류

**해결 방법**:
1. Supabase 대시보드 → Settings → Database
2. 비밀번호 재확인 또는 재설정
3. `.env` 파일의 DATABASE_URL 업데이트

### 2. "database does not exist"

**원인**: 잘못된 데이터베이스명

**해결 방법**:
- DATABASE_URL에서 데이터베이스명을 `postgres`로 수정

### 3. pgvector 확장 없음

**해결 방법**:
Supabase SQL Editor에서 실행:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 🚀 빠른 테스트 실행

### 1. 최소 기능 테스트
```bash
cd backend
python test_server.py
```
→ http://localhost:8000 접속

### 2. 프론트엔드만 테스트
```bash
cd frontend
npm run dev
```
→ http://localhost:3000 접속

### 3. API 키 없이 실행
1. `test_server.py` 실행 (백엔드)
2. `npm run dev` 실행 (프론트엔드)
3. UI만 확인 가능

## 📋 체크리스트

### 백엔드 실행 전 체크
- [ ] Python 설치됨
- [ ] 모든 pip 패키지 설치됨
- [ ] `.env` 파일 존재 (또는 test_server.py 사용)
- [ ] Supabase 프로젝트 생성됨 (선택)

### 프론트엔드 실행 전 체크
- [ ] Node.js 설치됨
- [ ] `npm install` 완료
- [ ] `.env` 파일 존재 (선택)

### 완전 기능 실행 전 체크
- [ ] Supabase 프로젝트 + API 키
- [ ] OpenAI API 키 (AI 기능용)
- [ ] 카카오 API 키 (지도 기능용)
- [ ] 데이터베이스 스키마 설치됨

## 🆘 여전히 문제가 있나요?

1. **터미널 재시작**: 새 명령 프롬프트/PowerShell 열기
2. **Python 환경 확인**: `python --version`, `pip --version`
3. **패키지 재설치**: `pip uninstall supabase && pip install supabase`
4. **임시 테스트**: `python test_server.py`로 기본 동작 확인
