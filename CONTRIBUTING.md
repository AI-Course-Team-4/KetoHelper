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
# syncmain -> release -> release-finish 순서대로 진행하여 dev 브랜치의 내용을 main으로 이전

# 해당 순서대로 진행하여 dev 내용을 main으로 동기화.
# git syncmain   # 사전 정리
# git release    # dev→main 릴리즈 PR 생성/열기
# GitHub에서 릴리즈 PR 머지
# git release-finish   # main→dev 동기화


# prdev (템플릿 강제 주입 → 생성 후 웹 열기)
git config --global alias.prdev '!f(){
  set -e
  BR=$(git rev-parse --abbrev-ref HEAD)
  [ "$BR" = dev -o "$BR" = main ] && { echo "현재 브랜치가 $BR 입니다. feature 브랜치에서 실행하세요."; exit 1; }

  git fetch origin
  if ! git merge origin/dev; then
    echo "⚠️ 충돌 발생: 해결 후 ① add ② commit ③ push"; exit 1
  fi
  git push -u origin "$BR"

  # 템플릿 파일이 현재 브랜치에 없으면 dev에서 가져와 보장
  [ -f .github/pull_request_template.md ] || \
    git show origin/dev:.github/pull_request_template.md > .github/pull_request_template.md

  # 이미 열린 PR 있으면 그걸 웹으로
  NUM=$(gh pr list --base dev --head "$BR" --state open --json number --jq ".[0].number" 2>/dev/null || true)
  if [ -n "$NUM" ]; then gh pr view "$NUM" --web; exit 0; fi

  # ★ 여기서 CLI가 본문을 파일로 '주입'해서 생성
  gh pr create -B dev -H "$BR" -F .github/pull_request_template.md --title "$BR"
  gh pr view --web
}; f'

# main → dev 동기화 PR (템플릿 강제 주입 + 자동머지 시도 + 웹 열기)
git config --global alias.syncmain '!f(){
  set -euo pipefail
  git fetch origin

  # main_only(L), dev_only(R) 계산: origin/main...origin/dev 의 서로 다른 커밋 수
  # L = main 전용 커밋, R = dev 전용 커밋
  read -r L R <<EOF
$(git rev-list --left-right --count origin/main...origin/dev)
EOF

  if [ "$L" -eq 0 ]; then
    echo "✅ main→dev 동기화 필요 없음 (main_only=0)"
    exit 0
  fi
  echo "ℹ️ main_only=$L, dev_only=$R → main→dev 동기화 PR 진행"

  # PR 본문 템플릿 준비(임시파일, 안전 삭제)
  TMP="$(mktemp)"
  cleanup() { rm -f "$TMP" || true; }
  trap cleanup EXIT

  if git show origin/dev:.github/pull_request_template.md > "$TMP" 2>/dev/null; then
    :
  elif git show origin/main:.github/pull_request_template.md > "$TMP" 2>/dev/null; then
    :
  else
    {
      echo "Sync main → dev"
      echo
      echo "- This PR syncs commits that exist only on **main** back into **dev**."
      echo "- Triggered by \`git syncmain\` alias."
      echo
      echo "**main only commits:**"
      git log --oneline origin/dev..origin/main || true
    } > "$TMP"
  fi

  # 이미 열린 PR이 있으면 그걸 사용, 없으면 생성
  NUM="$(gh pr list --base dev --head main --state open --json number --jq ".[0].number" 2>/dev/null || true)"
  if [ -n "${NUM:-}" ]; then
    echo "ℹ️ 기존 PR #$NUM 이 열려 있어요."
  else
    gh pr create -B dev -H main -F "$TMP" --title "Sync main → dev" >/dev/null
    # 생성 직후 재조회(네트워크 지연 대비)
    NUM="$(gh pr list --base dev --head main --state open --json number --jq ".[0].number" 2>/dev/null || true)"
    if [ -z "${NUM:-}" ]; then
      echo "⚠️ PR 번호를 찾지 못했어요. PR이 생성됐는지 웹에서 확인해주세요."
      gh pr list --base dev --head main --state open || true
      gh repo view --web || true
      exit 0
    fi
  fi

  # Auto-merge 시도 (레포에서 Allow auto-merge + 보호규칙 충족 필요)
  # 병합 방식은 --merge. 레포 정책상 merge 불가면 --squash/--rebase 로 바꾸거나 생략
  gh pr merge "$NUM" --auto --merge || true

  # PR 페이지 열기
  gh pr view "$NUM" --web || true
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

# release 후 main→dev 동기화(PR 생성/열기 + 자동머지 시도) - main에만 존재하는 커밋을 dev로 되돌려, 다음 릴리즈 때 막히지 않게 하는 마무리 동기화하는 역할
git config --global alias.release-finish '!f(){
  set -euo pipefail
  git fetch origin

  # main_only(L), dev_only(R)
  read -r L R <<EOF
$(git rev-list --left-right --count origin/main...origin/dev)
EOF

  if [ "$L" -eq 0 ]; then
    echo "✅ 릴리즈 후 동기화 필요 없음 (main_only=0)"
    exit 0
  fi
  echo "ℹ️ 릴리즈 반영 커밋을 dev로 되돌립니다 (main_only=$L, dev_only=$R)"

  # PR 본문 템플릿 준비
  TMP="$(mktemp)"; trap "rm -f \"$TMP\"" EXIT
  if git show origin/dev:.github/pull_request_template.md > "$TMP" 2>/dev/null || \
     git show origin/main:.github/pull_request_template.md > "$TMP" 2>/dev/null; then
    :
  else
    {
      echo "Sync main → dev (post-release)"
      echo
      echo "- Bring post-release commits from **main** back into **dev**."
      echo
      echo "**main-only commits:**"
      git log --oneline origin/dev..origin/main || true
    } > "$TMP"
  fi

  # 기존 PR 재사용 또는 새 PR 생성
  NUM="$(gh pr list --base dev --head main --state open --json number --jq ".[0].number" 2>/dev/null || true)"
  if [ -n "${NUM:-}" ]; then
    echo "ℹ️ 기존 동기화 PR #$NUM 사용"
  else
    gh pr create -B dev -H main -F "$TMP" -t "Sync main → dev (post-release)" >/dev/null
    NUM="$(gh pr list --base dev --head main --state open --json number --jq ".[0].number" 2>/dev/null || true)"
    [ -z "${NUM:-}" ] && { echo "⚠️ PR 번호 재조회 실패 — 웹에서 확인해주세요."; gh pr list --base dev --head main --state open || true; gh repo view --web || true; exit 0; }
  fi

  # 자동 머지 시도(Allow auto-merge + 필수체크/승인 필요)
  gh pr merge "$NUM" --auto --merge || true

  # PR 페이지 열기
  gh pr view "$NUM" --web || true
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


# git 협업 - 한 눈에 보는 치트시트
- 팀원은 feature/___ 브랜치 생성 후 작업 끝나면 git prdev 작성, 승인 완료 후 merge 클릭

- pm은 git syncmain 하여 main과 dev 싱크 맞추고 git release 실행, 
  승인 완료 후 merge 클릭, 마지막으로 다시 git syncmain

- 기능 작업 제출: feature/ → git prdev → (승인2) 웹에서 Merge

- 릴리즈 직전: git syncmain (필요 없으면 “✅ 없음” 출력)

- 릴리즈 PR: git release → (승인2) 웹에서 Merge

- 릴리즈 후(권장): git syncmain 한 번 더

-----------------------------------------
# git 협업 - 위처럼 진행하면 아래와 같은 이점 존재

--충돌은 feature 단계에서 조기 발견

--보호 규칙(리뷰 2명, 직접 push 금지) 준수

--템플릿은 항상 본문에 주입되어 빈 폼 스트레스 제거

--릴리즈 때 분기 가드로 안전하게 진행