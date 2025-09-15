# .env 파일 설정 가이드

## 🔧 .env 파일 생성 방법

### 1. .env 파일 생성
프로젝트 루트 디렉토리에 `.env` 파일을 만드세요.

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### 2. .env 파일 편집
`.env` 파일을 열어서 실제 값으로 수정하세요.

```env
# Supabase 설정
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# OpenAI 설정 (방식3용 - 선택사항)
OPENAI_API_KEY=your-openai-api-key-here
```

## 🔑 Supabase 정보 찾기

### 1. Supabase Dashboard 접속
- https://supabase.com/dashboard 에 로그인

### 2. 프로젝트 선택
- 사용할 프로젝트를 클릭

### 3. Settings → API 메뉴
- 왼쪽 사이드바에서 "Settings" → "API" 클릭

### 4. API Keys 복사
- **Project URL** → `SUPABASE_URL`에 복사
- **anon public** → `SUPABASE_ANON_KEY`에 복사

## 🤖 OpenAI API 키 (선택사항)

방식 3 (LLM 전처리)를 사용하려면:

1. https://platform.openai.com/api-keys 에서 API 키 생성
2. `OPENAI_API_KEY`에 입력

## 📂 파일 구조

```
recipe_test/
├── .env                    # 실제 설정 값 (Git에 커밋하지 마세요!)
├── .env.example           # 템플릿 파일
├── .gitignore            # .env 파일 제외 설정
├── check_supabase_data.py # 데이터베이스 구조 확인
└── embedding_experiments/
    └── run_supabase_experiment.py
```

## ⚠️ 보안 주의사항

1. **절대로 .env 파일을 Git에 커밋하지 마세요!**
2. `.gitignore`에 `.env` 추가 확인
3. API 키를 다른 사람과 공유하지 마세요

## 🚀 실행 방법

.env 파일 설정 후:

```bash
# 데이터베이스 구조 확인
python check_supabase_data.py

# 실험 실행
cd embedding_experiments
python run_supabase_experiment.py --mode test
```

## 🔍 문제 해결

### .env 파일을 찾을 수 없다는 오류
- `.env` 파일이 프로젝트 루트에 있는지 확인
- 파일명이 정확한지 확인 (`.env.txt`가 아니라 `.env`)

### 환경변수를 읽을 수 없다는 오류
- `.env` 파일 내용에 공백이나 따옴표가 없는지 확인
- `SUPABASE_URL=값` 형태로 등호 앞뒤 공백 제거

### Supabase 연결 실패
- SUPABASE_URL 형태 확인 (`https://` 포함)
- SUPABASE_ANON_KEY가 올바른 키인지 확인