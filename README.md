# 키토 코치 - 대화형 키토 식단 추천 웹앱

AI 기반 한국형 키토 식단 레시피 추천 및 주변 키토 친화 식당 찾기 서비스

## 🎯 주요 기능

### Must Have
- ✅ **대화형 AI 채팅**: "아침에 먹을 키토 한식 뭐 있어?", "역삼역 근처 키토 식당 알려줘"
- ✅ **레시피 추천**: 한국형 메뉴 키토화(keto-ize) 변환 + 대체재 제안  
- ✅ **식당 검색**: 카카오 로컬 API + 키토 스코어 정렬 + 지도/리스트
- ✅ **개인화**: 알레르기/비선호/목표 칼로리/탄수 제한 반영
- ✅ **RAG 시스템**: 한식 레시피 임베딩 검색 (pgvector)

### Should Have  
- ⏳ **7일 식단표 생성**: AI 기반 자동 계획
- ⏳ **캘린더 플래너**: 일정 저장/완료 기록 + ICS 내보내기
- ⏳ **쇼핑리스트**: 주간 레시피 재료 집계

## 🏗️ 기술 스택

### Frontend
- **Framework**: Vite + React 18 + TypeScript
- **상태관리**: Zustand + TanStack Query
- **UI**: Tailwind CSS + Radix UI + shadcn/ui
- **지도**: Kakao Map JS SDK

### Backend  
- **Framework**: FastAPI (Python)
- **AI/Agent**: LangGraph + LangChain + OpenAI
- **Database**: Supabase (PostgreSQL + pgvector)
- **External API**: Kakao Local/Maps

### AI/ML
- **LLM**: OpenAI GPT-3.5/4
- **Embeddings**: text-embedding-3-small  
- **Vector DB**: pgvector (PostgreSQL extension)
- **Agent**: LangGraph 노드 기반 오케스트레이션

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd mainProject-Team4-AICourse

# 백엔드 설정
cd backend
pip install -r requirements.txt
cp env.example .env
# .env 파일에 API 키들 설정

# 프론트엔드 설정  
cd ../frontend
npm install
```

### 2. 데이터베이스 설정

1. [Supabase](https://supabase.com)에서 새 프로젝트 생성
2. SQL Editor에서 `docs/database_setup.sql` 실행
3. `.env`에 데이터베이스 연결 정보 입력

### 3. API 키 설정

```bash
# backend/.env
OPENAI_API_KEY=sk-...
KAKAO_REST_KEY=...
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=...
```

### 4. 실행

```bash
# 백엔드 실행 (터미널 1)
cd backend  
uvicorn app.main:app --host :: --port 8000

# 프론트엔드 실행 (터미널 2)
cd frontend
npm run dev
```

🌐 **접속**: http://localhost:3000

## 📁 프로젝트 구조

```
mainProject-Team4-AICourse/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── agents/         # LangGraph 에이전트
│   │   ├── api/            # API 엔드포인트  
│   │   ├── core/           # 설정/DB 연결
│   │   ├── models/         # SQLAlchemy 모델
│   │   └── tools/          # RAG/검색/스코어 도구
│   └── requirements.txt
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # UI 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── hooks/          # React 훅
│   │   ├── lib/            # 유틸리티
│   │   └── store/          # Zustand 상태
│   └── package.json
├── docs/                   # 문서/스키마
└── README.md
```

## 🔧 주요 컴포넌트

### LangGraph 에이전트 플로우
```
router → recipe_rag | place_search | meal_plan | memory → answer
```

### 키토 스코어 계산 (0-100)
- ✅ **+20**: 단백질 중심 (삼겹/등심/회/치킨)
- ✅ **+10**: 채소 반찬 (나물/샐러드/쌈)  
- ❌ **-25**: 탄수 주식 (밥/면/떡/빵)
- ❌ **-10**: 당류 양념 (고추장/설탕)
- ✅ **+10**: 밥 제외 주문 가능

### API 엔드포인트
- `POST /api/v1/chat`: 대화형 추천
- `GET /api/v1/places`: 키토 친화 식당 검색
- `POST /api/v1/plans/generate`: 7일 식단표 생성
- `GET /api/v1/plans/range`: 캘린더 조회

## 🎨 UI/UX 특징

- **반응형 디자인**: 모바일 퍼스트 
- **다크모드 지원**: 시스템 설정 연동
- **실시간 채팅**: 스트리밍 응답
- **키토 스코어 시각화**: 색상 코딩 배지
- **지도 통합**: 카카오맵 + 마커 클러스터링

## 🔮 향후 계획

- [ ] **전국 확장**: 서울 → 수도권 → 전국
- [ ] **소셜 기능**: 식단 공유/커뮤니티  
- [ ] **웨어러블 연동**: 애플 헬스/삼성 헬스
- [ ] **배달 연동**: 키토 메뉴 주문 연결
- [ ] **영양사 상담**: 전문가 원격 상담

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다.

## 👥 팀 정보

**Team 4 - AI Course Project**
- 키토 식단 전문가 역할 분담
- 1개월 스프린트 개발
- 취업 포트폴리오 목적

---

⭐ **Star this repo if you find it helpful!**
