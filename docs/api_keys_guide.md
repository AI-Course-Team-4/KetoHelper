# API 키 발급 가이드

## 🗄️ 1. Supabase 설정

### 프로젝트 생성
1. https://supabase.com 접속
2. "New Project" → Organization 선택
3. 프로젝트 설정:
   - **Name**: `keto-Helper`
   - **Database Password**: 강력한 비밀번호 (⚠️ 반드시 기록!)
   - **Region**: Asia Northeast (Seoul)

### 연결 정보 수집
#### API 정보 (`Settings → API`)
```
Project URL: https://xxxxxxxxx.supabase.co
anon (public): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Database 정보 (`Settings → Database`)
```
Host: db.xxxxxxxxx.supabase.co
Database: postgres
Port: 5432
User: postgres
Password: [설정한 비밀번호]
```

## 🤖 2. OpenAI API 키

### 발급 방법
1. https://platform.openai.com 접속
2. 계정 생성/로그인
3. **API Keys** 메뉴 클릭
4. **"Create new secret key"** 클릭
5. 키 이름 입력 (예: keto-coach)
6. **API 키 복사** (⚠️ 한 번만 표시됩니다!)

### 요금 정보
- **무료 크레딧**: 새 계정 $5 제공
- **사용량 기반 과금**: GPT-3.5-turbo 약 $0.002/1K tokens
- **예상 비용**: 개발/테스트 시 월 $10-20 정도

## 🗺️ 3. 카카오 API 키

### 애플리케이션 생성
1. https://developers.kakao.com 접속
2. **내 애플리케이션** → **애플리케이션 추가하기**
3. 앱 정보 입력:
   - **앱 이름**: `키토코치`
   - **사업자명**: 개인 이름
   - **카테고리**: 기타

### API 키 확인
#### REST API 키 (`앱 키` 탭)
```
REST API 키: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
JavaScript 키: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 플랫폼 설정
#### Web 플랫폼 등록 (`플랫폼` 탭)
1. **Web 플랫폼 등록** 클릭
2. **사이트 도메인**: `http://localhost:3000`, `http://localhost:3001`

#### 사용 권한 설정 (`동의항목` 탭)
- **카카오 로그인**: 선택사항 (추후 로그인 기능 시)
- **카카오맵**: 필수

## 📋 4. 최종 체크리스트

### backend/.env 파일에 필요한 값들:
- [ ] `DATABASE_URL`: Supabase 데이터베이스 연결 URL
- [ ] `SUPABASE_URL`: Supabase 프로젝트 URL
- [ ] `SUPABASE_ANON_KEY`: Supabase anon 키
- [ ] `SUPABASE_SERVICE_ROLE_KEY`: Supabase service_role 키
- [ ] `OPENAI_API_KEY`: OpenAI API 키
- [ ] `KAKAO_REST_KEY`: 카카오 REST API 키

### frontend/.env 파일에 필요한 값들:
- [ ] `VITE_SUPABASE_URL`: Supabase 프로젝트 URL
- [ ] `VITE_SUPABASE_ANON_KEY`: Supabase anon 키
- [ ] `VITE_KAKAO_JS_KEY`: 카카오 JavaScript 키

## 🔒 보안 주의사항

### ✅ 안전한 키 (프론트엔드 노출 가능)
- Supabase `anon` 키
- 카카오 `JavaScript` 키

### ⚠️ 위험한 키 (절대 노출 금지)
- Supabase `service_role` 키
- OpenAI API 키
- 카카오 `REST API` 키
- 데이터베이스 비밀번호

### 보안 체크리스트
- [ ] `.env` 파일이 `.gitignore`에 포함되어 있음
- [ ] service_role 키는 백엔드에서만 사용
- [ ] API 키를 코드에 하드코딩하지 않음
- [ ] 주기적으로 키 회전 (3-6개월마다)

## 🆘 문제 해결

### OpenAI API 오류
```
Error: "You exceeded your current quota"
```
- **해결**: 결제 정보 등록 후 사용량 제한 설정

### 카카오 API 오류
```
Error: "Invalid app key"
```
- **해결**: REST API 키와 JavaScript 키 구분 확인

### Supabase 연결 오류
```
Error: "password authentication failed"
```
- **해결**: 데이터베이스 비밀번호 재확인
