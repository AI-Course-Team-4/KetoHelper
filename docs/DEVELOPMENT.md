# 개발 가이드

## 🛠️ 개발 환경 설정

### 필요 조건

- **Node.js**: 18.0.0 이상
- **Python**: 3.11 이상
- **MongoDB**: 7.0 이상 (또는 MongoDB Atlas)


### 설치 및 실행

1. **저장소 클론**
```bash
git clone https://github.com/your-username/mainProject-Team4.git
cd mainProject-Team4
```

2. **자동 설정 스크립트 실행**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

3. **환경 변수 설정**
```bash
cp env.example .env
# .env 파일을 편집하여 필요한 값들을 설정
```

4. **개발 서버 실행**

#### 개별 실행
```bash
# 백엔드
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload

# 프론트엔드 (새 터미널)
cd frontend
npm run dev
```



## 🏗️ 프로젝트 구조

```
mainProject-Team4/
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── components/      # 재사용 가능한 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── hooks/          # 커스텀 훅
│   │   ├── services/       # API 서비스
│   │   ├── store/          # 상태 관리 (Zustand)
│   │   ├── types/          # TypeScript 타입
│   │   ├── utils/          # 유틸리티 함수
│   │   └── theme/          # 테마 설정
│   ├── public/
│   └── package.json
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 라우터
│   │   ├── core/           # 핵심 설정
│   │   ├── models/         # 데이터 모델
│   │   ├── services/       # 비즈니스 로직
│   │   └── main.py         # 앱 엔트리포인트
│   └── requirements.txt
├── docs/                   # 문서
└── scripts/                # 유틸리티 스크립트
```

## 🎨 프론트엔드 개발

### 기술 스택

- **React 18** + **TypeScript**
- **Vite**: 빠른 개발 환경
- **Material-UI**: UI 컴포넌트 라이브러리
- **Zustand**: 상태 관리
- **React Query**: 서버 상태 관리
- **React Router**: 라우팅

### 컴포넌트 생성 가이드

1. **재사용 가능한 컴포넌트**
```typescript
// src/components/Button/Button.tsx
import { Button as MuiButton, ButtonProps } from '@mui/material'

interface CustomButtonProps extends Omit<ButtonProps, 'color'> {
  variant?: 'primary' | 'secondary' | 'danger'
}

export const Button = ({ variant = 'primary', ...props }: CustomButtonProps) => {
  const colorMap = {
    primary: 'primary',
    secondary: 'secondary',
    danger: 'error'
  }

  return <MuiButton color={colorMap[variant]} {...props} />
}
```

2. **페이지 컴포넌트**
```typescript
// src/pages/ExamplePage.tsx
import { Box, Typography } from '@mui/material'

const ExamplePage = () => {
  return (
    <Box>
      <Typography variant="h3">페이지 제목</Typography>
      {/* 페이지 내용 */}
    </Box>
  )
}

export default ExamplePage
```

### 상태 관리

**Zustand Store 예시:**
```typescript
// src/store/exampleStore.ts
import { create } from 'zustand'

interface ExampleState {
  count: number
  increment: () => void
  decrement: () => void
}

export const useExampleStore = create<ExampleState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
}))
```

### API 호출

**서비스 예시:**
```typescript
// src/services/exampleService.ts
import { apiHelper } from './api'

export const exampleService = {
  getData: async (id: string): Promise<ExampleData> => {
    return apiHelper.get<ExampleData>(`/example/${id}`)
  },
  
  createData: async (data: CreateExampleData): Promise<ExampleData> => {
    return apiHelper.post<ExampleData>('/example', data)
  }
}
```

## ⚙️ 백엔드 개발

### 기술 스택

- **FastAPI**: 고성능 Python 웹 프레임워크
- **Motor**: MongoDB 비동기 드라이버
- **Pydantic**: 데이터 검증 및 직렬화
- **LangChain**: AI/RAG 시스템
- **OAuth 2.0**: Google 소셜 로그인

### API 엔드포인트 생성

```python
# backend/app/api/v1/endpoints/example.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ExampleResponse(BaseModel):
    id: str
    name: str
    description: str

@router.get("/", response_model=List[ExampleResponse])
async def get_examples():
    """예시 데이터 목록 조회"""
    # TODO: 데이터베이스에서 데이터 조회
    return []

@router.post("/", response_model=ExampleResponse)
async def create_example(data: dict):
    """예시 데이터 생성"""
    # TODO: 데이터베이스에 데이터 저장
    return ExampleResponse(
        id="example_id",
        name=data.get("name"),
        description=data.get("description")
    )
```

### 데이터베이스 모델

```python
# backend/app/models/example.py
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ExampleModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

## 🤖 AI 기능 개발

### RAG 시스템 구조

```python
# backend/app/services/ai/rag_service.py
from langchain.vectorstores import Pinecone
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI

class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = Pinecone.from_existing_index(
            index_name="ketohelper",
            embedding=self.embeddings
        )
        self.llm = OpenAI()
    
    async def get_recommendations(self, query: str, user_preferences: dict):
        """사용자 쿼리와 선호도를 바탕으로 추천 생성"""
        # 1. 벡터 검색으로 관련 문서 찾기
        docs = self.vectorstore.similarity_search(query, k=5)
        
        # 2. LLM으로 개인화된 답변 생성
        context = "\n".join([doc.page_content for doc in docs])
        prompt = f"""
        사용자 선호도: {user_preferences}
        관련 정보: {context}
        질문: {query}
        
        키토 다이어트에 적합한 맞춤형 추천을 제공해주세요.
        """
        
        response = await self.llm.agenerate([prompt])
        return response.generations[0][0].text
```

## 🧪 테스트

### 프론트엔드 테스트

```bash
cd frontend

# 단위 테스트
npm test

# 테스트 커버리지
npm run test:coverage

# E2E 테스트 (예정)
npm run test:e2e
```

### 백엔드 테스트

```bash
cd backend
source venv/bin/activate

# 단위 테스트
pytest

# 테스트 커버리지
pytest --cov=app

# 특정 테스트 파일
pytest tests/test_recipes.py
```

## 🚀 배포

### 프론트엔드 배포 (Vercel)

```bash
cd frontend
npm run build
vercel --prod
```

### 백엔드 배포 (Railway/AWS)

```bash
cd backend
# 플랫폼별 배포 명령어 실행
```

## 📊 모니터링 및 로깅

### 프론트엔드

- **에러 추적**: Sentry (예정)
- **분석**: Google Analytics (예정)
- **성능**: Web Vitals

### 백엔드

- **로깅**: Loguru
- **모니터링**: 헬스체크 엔드포인트 (`/health`)
- **API 문서**: FastAPI 자동 생성 (`/docs`)

## 🔧 개발 도구

### VS Code 확장

- **Frontend**: ES7+ React/Redux/React-Native, TypeScript Importer
- **Backend**: Python, Pylance, autoDocstring
- **공통**: GitLens, Prettier

### 유용한 명령어

```bash
# 의존성 업데이트
npm update                    # Frontend
pip install -r requirements.txt --upgrade  # Backend

# 코드 포맷팅
npm run lint:fix             # Frontend
black . && isort .           # Backend

# 타입 체크
npm run type-check           # Frontend
mypy .                       # Backend (예정)
```

## 🐛 디버깅

### 일반적인 문제들

1. **MongoDB 연결 오류**
   - MongoDB 서버가 실행 중인지 확인
   - 연결 문자열이 올바른지 확인

2. **CORS 오류**
   - backend/app/core/config.py에서 CORS_ORIGINS 확인
   - 프론트엔드 URL이 포함되어 있는지 확인

3. **환경 변수 오류**
   - .env 파일이 올바른 위치에 있는지 확인
   - 필수 환경 변수가 설정되어 있는지 확인

## 📝 추가 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [React 공식 문서](https://react.dev/)
- [Material-UI 문서](https://mui.com/)
- [LangChain 문서](https://python.langchain.com/)
