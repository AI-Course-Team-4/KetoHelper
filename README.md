# 🥑 KetoHelper - 키토식단 추천 웹사이트

키토제닉 다이어트를 시작하거나 유지하는 사용자들에게 AI 기반 개인화된 식단 추천, 식당 정보, 그리고 맞춤 서비스를 제공하는 웹 플랫폼입니다.

## 🚀 주요 기능

- 🤖 **AI 기반 개인화 식단 추천**: RAG와 AI Agent를 활용한 맞춤형 레시피 추천
- 🍽️ **키토 친화적 식당 추천**: 위치 기반 식당 정보와 메뉴 분석
- 📅 **구독 전용 캘린더**: 매일 아침, 점심, 저녁 식단을 체계적으로 관리 (프리미엄)
- 👤 **개인화 설정**: 알레르기, 선호도, 다이어트 계획 관리
- 💎 **구독 서비스**: 무제한 추천과 고급 기능 제공
- 📊 **진행률 추적**: D-day, 목표 체중, 연속 실천 일수 관리
- 📱 **반응형 디자인**: 모든 디바이스에서 최적화된 사용자 경험
- 🔐 **Google OAuth**: 간편하고 안전한 소셜 로그인

## 🛠️ 기술 스택

### Frontend
- **React 18+** with TypeScript
- **Vite** - 빠른 개발 환경
- **Material-UI** - 현대적이고 접근성이 좋은 UI 컴포넌트
- **React Router v6** - 클라이언트 사이드 라우팅
- **Zustand** - 경량 상태 관리
- **React Query** - 서버 상태 관리

### Backend
- **FastAPI** - 고성능 Python 웹 프레임워크
- **MongoDB Atlas** - 클라우드 데이터베이스 with Motor (비동기 MongoDB 드라이버)
- **Pydantic** - 데이터 검증 및 직렬화
- **OAuth 2.0** - Google 소셜 로그인
- **Uvicorn** - ASGI 서버

### AI & 데이터
- **LangChain** - RAG 시스템 구현
- **LangGraph** - AI 워크플로우 관리
- **OpenAI GPT** - 언어 모델
- **Pinecone** - 벡터 데이터베이스

## 📁 프로젝트 구조

```
mainProject-Team4/
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── components/      # 재사용 가능한 UI 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── hooks/          # 커스텀 React 훅
│   │   ├── services/       # API 서비스
│   │   ├── store/          # 상태 관리
│   │   ├── utils/          # 유틸리티 함수
│   │   └── types/          # TypeScript 타입 정의
│   ├── public/
│   └── package.json
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 라우터
│   │   ├── core/           # 설정 및 보안
│   │   ├── models/         # 데이터 모델
│   │   ├── services/       # 비즈니스 로직
│   │   ├── ai/             # AI 관련 모듈
│   │   └── main.py         # FastAPI 앱 엔트리포인트
│   ├── requirements.txt
│   └── Dockerfile
├── docs/                   # 프로젝트 문서
├── scripts/                # 배포 및 유틸리티 스크립트
└── docker-compose.yml      # 개발 환경 설정
```

## 🚀 빠른 시작

### 필요 조건
- Node.js 18+
- Python 3.11+
- MongoDB (로컬 또는 MongoDB Atlas)
- Git

### 설치 및 실행

1. **저장소 클론**
```bash
git clone https://github.com/your-username/mainProject-Team4.git
cd mainProject-Team4
```

2. **환경 변수 설정**
```bash
# 루트 디렉토리에 .env 파일 생성
cp .env.example .env
# 필요한 환경 변수들을 .env 파일에 설정
```

3. **MongoDB Atlas 설정**
   - [MongoDB Atlas](https://www.mongodb.com/atlas) 계정 생성
   - 클러스터 생성 및 연결 문자열 복사
   - `backend/.env` 파일 생성 (env.example 참고)
   - MONGODB_URL에 Atlas 연결 문자열 입력

4. **프론트엔드 설정**
```bash
cd frontend
npm install
npm run dev
```

5. **백엔드 설정**
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### 전체 환경 자동 설정
```bash
# 자동 설정 스크립트 실행 (MongoDB 포함)
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## 🌐 API 문서

백엔드 서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📱 주요 화면

1. **로그인 화면** (`/login`) - Google OAuth 소셜 로그인
2. **메인 화면** (`/`) - 서비스 소개 및 개인화 대시보드
3. **프로필 설정** (`/profile`) - 사진, 기본 정보, 다이어트 계획 설정
4. **선호도 설정** (`/preferences`) - 알레르기, 비선호 음식, 요리 스타일 관리
5. **캘린더** (`/calendar`) - 매끼 식단 관리 및 체크 (구독 전용)
6. **추천 식단** (`/meals`) - AI 기반 키토 레시피 추천
7. **추천 식당** (`/restaurants`) - 위치 기반 키토 친화적 식당 정보
8. **구독** (`/subscription`) - 프리미엄 구독 관리
9. **설정** (`/settings`) - 계정 및 알림 설정

### 사용자 상태별 기능 접근

| 사용자 상태 | 캘린더 사용 | 선호도 반영 | 추천 개수 |
|------------|-----------|-----------|---------|
| 비로그인    | ❌        | ❌        | 3개 제한 |
| 로그인      | ❌        | ✅        | 3개 제한 |
| 구독        | ✅        | ✅        | 무제한   |

## 🔧 개발 가이드

### 코드 스타일
- **Frontend**: ESLint + Prettier
- **Backend**: Black + isort
- **Commit**: Conventional Commits

### 브랜치 전략
- `main`: 프로덕션 브랜치
- `develop`: 개발 브랜치
- `feature/*`: 기능 개발 브랜치
- `hotfix/*`: 긴급 수정 브랜치

### 테스트
```bash
# 프론트엔드 테스트
cd frontend && npm test

# 백엔드 테스트
cd backend && pytest
```

## 🚀 배포

### 프론트엔드 (Vercel)
```bash
cd frontend
npm run build
vercel --prod
```

### 백엔드 (Railway/AWS EC2)
```bash
cd backend
docker build -t ketohelper-backend .
# 배포 명령어는 플랫폼별로 상이
```

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 팀

- **프론트엔드**: React, TypeScript, UI/UX
- **백엔드**: FastAPI, MongoDB, API 설계
- **AI/ML**: RAG 시스템, LangChain, 추천 알고리즘
- **DevOps**: 배포, 모니터링, 인프라 관리

## 📞 연락처

프로젝트 관련 문의사항이 있으시면 이슈를 생성해주세요.

---

**Made with ❤️ for the Keto Community**
