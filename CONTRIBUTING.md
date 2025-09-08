# KetoHelper 기여 가이드

KetoHelper 프로젝트에 기여해주셔서 감사합니다! 🥑

## 🚀 시작하기

### 개발 환경 설정

1. **저장소 Fork 및 Clone**
```bash
git clone https://github.com/your-username/mainProject-Team4.git
cd mainProject-Team4
```

2. **개발 환경 설정**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

3. **환경 변수 설정**
```bash
cp env.example .env
# .env 파일을 편집하여 필요한 환경 변수를 설정하세요
```

### 개발 서버 실행

#### 방법 1: 개별 실행
```bash
# 백엔드
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload

# 프론트엔드 (새 터미널)
cd frontend
npm run dev
```

#### 방법 2: Docker 사용
```bash
docker-compose up -d
```

## 🔧 개발 가이드라인

### 브랜치 전략

- `main`: 프로덕션 브랜치
- `develop`: 개발 브랜치
- `feature/{기능명}`: 새로운 기능 개발
- `bugfix/{버그명}`: 버그 수정
- `hotfix/{수정명}`: 긴급 수정

### 커밋 컨벤션

[Conventional Commits](https://www.conventionalcommits.org/) 규칙을 따릅니다.

```
type(scope): description

feat(auth): add Google OAuth login
fix(api): resolve recipe search pagination
docs(readme): update installation guide
style(ui): improve mobile responsive design
refactor(backend): optimize database queries
test(api): add recipe endpoint tests
chore(deps): update dependencies
```

**타입:**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 과정 또는 보조 도구 변경

### 코드 스타일

#### Frontend (React/TypeScript)
- **ESLint + Prettier** 사용
- **함수형 컴포넌트** 우선 사용
- **TypeScript strict 모드** 준수
- **재사용 가능한 컴포넌트** 작성

```bash
# 린팅 실행
npm run lint

# 포맷팅 실행
npm run lint:fix
```

#### Backend (Python/FastAPI)
- **Black + isort** 사용
- **Type hints** 필수
- **Pydantic 모델** 사용
- **비동기 함수** 우선 사용

```bash
# 포맷팅 실행
black .
isort .

# 린팅 실행
flake8 .
```

## 📝 Pull Request 가이드

### PR 템플릿

```markdown
## 📋 변경 사항
- [ ] 새로운 기능 추가
- [ ] 버그 수정
- [ ] 문서 업데이트
- [ ] 리팩토링
- [ ] 테스트 추가

## 🔍 상세 설명
이 PR에서 변경된 내용을 자세히 설명해주세요.

## 🧪 테스트
- [ ] 기존 테스트 통과
- [ ] 새로운 테스트 추가
- [ ] 수동 테스트 완료

## 📸 스크린샷 (UI 변경 시)
변경된 UI의 스크린샷을 첨부해주세요.

## 📚 관련 이슈
Closes #issue_number
```

### PR 체크리스트

- [ ] 브랜치명이 규칙을 따르는가?
- [ ] 커밋 메시지가 컨벤션을 따르는가?
- [ ] 코드 스타일 가이드를 준수하는가?
- [ ] 테스트가 통과하는가?
- [ ] 문서가 업데이트되었는가?
- [ ] 충돌이 해결되었는가?

## 🐛 버그 리포트

버그를 발견했다면 다음 정보를 포함하여 이슈를 생성해주세요:

```markdown
## 🐛 버그 설명
버그에 대한 명확하고 간결한 설명

## 🔄 재현 단계
1. '...'로 이동
2. '...'를 클릭
3. '...'까지 스크롤
4. 오류 확인

## 🎯 예상 동작
예상했던 동작에 대한 설명

## 📸 스크린샷
가능하다면 스크린샷을 첨부해주세요

## 🖥️ 환경 정보
- OS: [예: macOS, Windows, Ubuntu]
- 브라우저: [예: Chrome, Safari, Firefox]
- 버전: [예: 22]

## 📝 추가 컨텍스트
버그에 대한 기타 컨텍스트나 정보
```

## 💡 기능 요청

새로운 기능을 제안하고 싶다면:

```markdown
## 🚀 기능 요청
기능에 대한 명확하고 간결한 설명

## 🎯 해결하고자 하는 문제
이 기능이 해결할 문제나 개선할 점

## 💭 제안하는 해결책
원하는 기능의 동작 방식

## 🔄 대안책
고려해본 다른 해결책이나 기능

## 📝 추가 컨텍스트
기능 요청에 대한 기타 컨텍스트나 스크린샷
```

## 🧪 테스트

### Frontend 테스트
```bash
cd frontend
npm test
```

### Backend 테스트
```bash
cd backend
source venv/bin/activate
pytest
```

### E2E 테스트
```bash
# TODO: E2E 테스트 설정 후 업데이트 예정
```

## 📚 문서

- **API 문서**: http://localhost:8000/docs
- **Storybook**: `npm run storybook` (예정)
- **타입 문서**: `npm run type-check`

## 🤝 커뮤니티

- **이슈 토론**: GitHub Issues 활용
- **코드 리뷰**: 상호 존중하는 건설적인 피드백
- **질문**: Discussions 탭 활용

## ⚖️ 라이선스

이 프로젝트에 기여함으로써 MIT 라이선스 하에 기여 내용을 제공하는 것에 동의합니다.

---

**질문이 있으시면 언제든지 이슈를 생성하거나 토론을 시작해주세요!**

Happy coding! 🥑✨
