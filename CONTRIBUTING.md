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

```bash
# 백엔드
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload

# 프론트엔드 (새 터미널)
cd frontend
npm run dev
```

## 🔧 개발 가이드라인

### 브랜치 전략 & 네이밍 규칙

* **기본 브랜치**
  * `dev` : 통합 개발 브랜치 (기능 합류, 테스트)
  * `main` : 배포/릴리즈 브랜치 (안정)

* **작업 브랜치(기능/수정 등)**
  * **패턴(권장)**: `type/<owner>-<topic>` — 슬래시는 1회만 사용
  * **허용 type**: `feature`, `fix`, `chore`, `docs`, `refactor`, `test`, `hotfix`, `release`
  * **예시**: `feature/sh-main-page`, `fix/yk-login-500`, `chore/ci-cd-cache-tune`
  * **금지**: 중첩 슬래시(예: `feature/sh/setting`)

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

---

# Git PR 운영 규칙 (실행 가이드)

> 목적: `dev`/`main`은 PR로만 변경. 개인 브랜치에서 자유 작업.
> 편의성: git 명령어가 어려운 팀원들을 위해 alias로 명령어 하나로 협업 가능하도록 작업.

## 팀 공통 운영 흐름

### 0) Windows에서 gh 설치

- PowerShell(관리자) 열고 실행

winget install --id GitHub.cli -e

- 설치 후 새 터미널에서 확인/로그인
gh --version
gh auth login

### 1) 각자 작업 → dev로 PR

```bash
git switch -c feature/<owner>-<topic>
git add -A && git commit -m "feat: ..."
git prdev
```
### 패턴(권장): type/<owner>-<topic> — 단 한 번만 슬래시 사용

### 허용 type: feature, fix, chore, docs, refactor, test, hotfix, release

### 예시
- feature/sh-main-page

- fix/yk-login-500

- chore/ci-cd-cache-tune

- 금지: 중첩 슬래시(예: feature/sh/setting). Git의 참조 구조상 **feature/sh**가 존재하면 **feature/sh/setting**을 만들 수 없습니다.

### 2) 릴리즈: dev → main 승격

```bash
#dev 브랜치에서 실행
git release
```

## 한 번만 설정하는 alias (gh CLI 필요)

```bash
# prdev : feature → dev PR 생성
# release : dev → main 릴리즈 PR 생성(템플릿 강제 주입)


# feature/* → (origin/dev merge, 템플릿 적용) → dev 대상 PR 생성
git config --global alias.prdev '!f(){
  set -e
  BR=$(git rev-parse --abbrev-ref HEAD)
  [ "$BR" = dev -o "$BR" = main ] && { echo "현재 브랜치가 $BR 입니다. feature 브랜치에서 실행하세요."; exit 1; }
  git fetch origin
  if ! git merge origin/dev; then
    echo "⚠️ 충돌 발생: 해결 후 ① git add -A ② git commit ③ git push -u origin $BR"; exit 1
  fi
  git push -u origin "$BR"
  gh pr create -B dev -H "$BR" -F .github/pull_request_template.md --web
}; f'

# dev → main 릴리즈 PR (템플릿 강제 주입)
git config --global alias.release '!f(){
  set -e
  git fetch origin
  # main에만 있는 커밋이 있으면 먼저 main→dev 병합 필요
  if ! git merge-base --is-ancestor origin/main origin/dev; then
    echo "❌ main에만 있는 커밋이 있어요. 먼저 main→dev 병합 PR을 머지하세요."
    exit 1
  fi
  # 이미 열린 dev→main PR이 있으면 그걸 연다
  NUM=$(gh pr list --base main --head dev --state open --json number --jq ".[0].number" 2>/dev/null || true)
  if [ -n "$NUM" ]; then
    echo "ℹ️ 기존 PR #$NUM 이 열려 있어요. 웹으로 엽니다."
    gh pr view "$NUM" --web
    exit 0
  fi
  # 템플릿 강제 주입(-F)으로 새 PR 생성
  gh pr create -B main -H dev \
    -F .github/pull_request_template.md \
    --title "Release: dev → main" \
    --web
}; f'
```


### gh(깃허브 CLI) 설치/체크 (Windows)

```powershell
winget install --id GitHub.cli -e
```

```bash
gh auth login
gh auth status
```

## 자주 발생하는 이슈 & 해결

- GH013: dev/main 직접 push 거절 → 정상, 반드시 PR 사용 (`git prdev`, `git release`).
- 브랜치 이름 충돌 → 슬래시는 한 번만 (`feature/sh-setting`).
- 충돌 발생 → 수정 후 `git add -A` → `git commit` → `git push` → 필요 시 `gh pr create -B dev -H <현재브랜치> -w`.
- 기본 브랜치 확인: GitHub Settings → Branches → Default branch = `dev`.
