# 챗봇 대화 저장 **MVP 가이드** (비로그인 지원)

> **3줄 요약**  
> 1) **스레드(thread) 단위**로 유저/게스트 공통 저장  
> 2) 페이지 로드시 **최근 스레드의 20개 메시지**만 불러오기  
> 3) **게스트 ID(localStorage)** 로 로그인 전에도 연속 대화 유지

---

## 0) DB 점검(10분 컷)

게스트도 스레드를 가질 수 있게 아주 **최소 변경**만 합니다.

### 스키마 변경안
```sql
-- 0-1) chat 테이블: 게스트 컬럼 추가
ALTER TABLE public.chat
  ADD COLUMN IF NOT EXISTS guest_id uuid NULL;

-- 0-2) chat_thread: 게스트/회원 중 한 쪽만 귀속되도록
ALTER TABLE public.chat_thread
  ADD COLUMN IF NOT EXISTS guest_id uuid NULL;

-- 0-3) user_id NULL 허용 (게스트 스레드 지원)
ALTER TABLE public.chat_thread
  ALTER COLUMN user_id DROP NOT NULL;

-- 0-4) 체크 제약: user_id XOR guest_id
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chat_thread_user_or_guest'
  ) THEN
    ALTER TABLE public.chat_thread
    ADD CONSTRAINT chat_thread_user_or_guest
    CHECK (
      (user_id IS NOT NULL AND guest_id IS NULL)
      OR (user_id IS NULL AND guest_id IS NOT NULL)
    );
  END IF;
END$$;

-- 0-5) 인덱스(조회 성능)
CREATE INDEX IF NOT EXISTS idx_chat_thread_order_by_user
  ON public.chat_thread(user_id, last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_thread_order_by_guest
  ON public.chat_thread(guest_id, last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_by_thread_time
  ON public.chat(thread_id, created_at ASC);
```

---

## 1) 프론트엔드(가장 쉬운 것부터)

### 1-1. 게스트 ID 영구보관
- 위치: `frontend/src/store/authStore.ts`
- 로직: 최초 접속 시 `UUID v4` 생성 → `localStorage('keto_guest_id')` 저장 → 이후 재사용

```ts
// authStore.ts (pseudo)
import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

type AuthState = {
  userId?: string | null;
  guestId: string;
  ensureGuestId: () => string;
};

export const useAuthStore = create<AuthState>((set, get) => ({
  userId: null,
  guestId: localStorage.getItem('keto_guest_id') || '',
  ensureGuestId: () => {
    let gid = get().guestId;
    if (!gid) {
      gid = uuidv4();
      localStorage.setItem('keto_guest_id', gid);
      set({ guestId: gid });
    }
    return gid;
  },
}));
```

### 1-2. 채팅 전송 & 불러오기
- 진입 시: **내(회원 or 게스트) 최신 스레드** 정보 로드 → 그 스레드의 **최근 20개** 메시지를 불러와 표시
- 전송 시: `user_id` **또는** `guest_id` + `thread_id`를 함께 전송

```ts
// ChatPage.tsx (pseudo)
const { userId, ensureGuestId } = useAuthStore();
const idPayload = userId ? { user_id: userId } : { guest_id: ensureGuestId() };

// 1) 스레드 목록 가져오기
const threads = await api.get('/chat/threads', { params: idPayload });
const activeThread = threads[0] ?? await api.post('/chat/thread', idPayload); // 없으면 생성(선택)

// 2) 히스토리 20개
const history = await api.get(`/chat/history/${activeThread.id}`, { params: { limit: 20 } });
setMessages(history);

// 3) 메시지 전송
async function sendMessage(text: string) {
  const res = await api.post('/chat', {
    ...idPayload,
    thread_id: activeThread.id,
    message: text,
  });
  // res에는 assistant 메시지도 함께(동기 처리) 반환시키면 UI 구현이 쉬워짐
  setMessages(prev => [...prev, { role: 'user', message: text }, ...res.assistantBatch]);
}
```

---

## 2) 백엔드 API(3개면 끝)

위치는 예시로 `backend/app/domains/chat/api/chat.py`

### 2-1) POST `/chat` — 메시지 저장(+필요 시 스레드 생성)
**Request**
```json
{
  "message": "키토 점심 추천해줘",
  "thread_id": "optional-uuid",
  "user_id": "로그인시 포함",
  "guest_id": "게스트시 포함"
}
```

**Handler 개요**
1) `thread_id` 없으면 신규 스레드 생성(회원이면 user_id, 게스트면 guest_id 귀속)
2) `chat`에 유저 메시지 INSERT (`role='user'`)
3) 에이전트 호출 → **AI 응답** 생성
4) AI 응답도 `chat`에 INSERT (`role='assistant'`)
5) `chat_thread.last_message_at` 갱신
6) 응답으로 **AI 메시지 배열**(1개 이상 가능, 스트리밍 미도입) 반환

```py
# pseudo (FastAPI)
@router.post("/chat")
def post_chat(body: ChatIn):
    thread = ensure_thread(body.user_id, body.guest_id, body.thread_id)
    insert_chat(thread.id, 'user', body.message, body.user_id, body.guest_id)
    ai_msgs = run_agent(body.message, thread_context(thread.id))  # 요약/컨텍스트는 이후 확장
    for m in ai_msgs:
        insert_chat(thread.id, 'assistant', m, body.user_id, body.guest_id)
    touch_thread(thread.id)
    return {"assistantBatch": [{"role": "assistant", "message": m} for m in ai_msgs]}
```

### 2-2) GET `/chat/threads` — 내 스레드 목록(최근 순)
**Query**: `user_id` 또는 `guest_id` 중 1개  
**Response**: `[{ id, title, last_message_at }]` 최신 20개

```sql
SELECT id, title, last_message_at
FROM public.chat_thread
WHERE (user_id = :user_id) IS NOT DISTINCT FROM TRUE
   OR (guest_id = :guest_id) IS NOT DISTINCT FROM TRUE
ORDER BY last_message_at DESC
LIMIT 20;
```

### 2-3) GET `/chat/history/{thread_id}` — 스레드 메시지 페이지네이션
**Query**: `limit=20`, `before=<created_at or id>`(선택)  
**Response**: 시간 오름차순 정렬된 최신 20개

```sql
SELECT id, role, message, created_at
FROM public.chat
WHERE thread_id = :thread_id
  AND (:before IS NULL OR created_at < :before)
ORDER BY created_at ASC
LIMIT :limit;  -- 20
```

> **팁**: 1차 배포는 **스트리밍 없이 동기 응답**으로. 안정화 후 필요 시 SSE/WebSocket 스트리밍 추가.

---

## 3) 데이터 모델(최소 공통 형태)

`chat`  
- `id`, `thread_id`, `role ('user'|'assistant')`, `message`, `created_at`
- `user_id NULL`, `guest_id NULL` (둘 중 하나 채움)

`chat_thread`  
- `id`, `title`, `last_message_at`, `user_id NULL`, `guest_id NULL`(XOR 제약)

> 나중에 `intent`, `session_id`, `meta JSONB` 등은 **추가 컬럼**으로 확장하면 됩니다.

---

## 4) 게스트 정책(초간단)

- **게스트도 DB에 동일 규칙**으로 저장(식별자는 `guest_id`)
- **보관 30일** 정책: 나중에 배치로 삭제

```sql
-- Supabase pg_cron 또는 외부 스케줄러로 매일 1회 실행
DELETE FROM public.chat c
USING public.chat_thread t
WHERE c.thread_id = t.id
  AND t.last_message_at < now() - interval '30 days';

DELETE FROM public.chat_thread
WHERE last_message_at < now() - interval '30 days';
```

---

## 5) FE—BE 연결 포인트 요약

- FE `sendMessage()` → POST `/chat` (body: `message + thread_id + (user_id|guest_id)`)
- 초기 진입 → GET `/chat/threads` → 최상단 스레드 선택 → GET `/chat/history/{id}?limit=20`

---

## 6) 테스트 체크리스트(MVP 합격 기준)

- **게스트 모드**: 비로그인 상태 채팅 가능, `keto_guest_id`가 브라우저 재시작 후에도 유지
- **메시지 저장**: 유저/AI 모두 DB에 저장, `created_at` 정상
- **연속성**: 새로고침 후 직전 스레드의 최근 20개가 그대로 보임(오름차순 정렬)
- **경계 상황**: 네트워크 오류, 다중 탭, 로그인 전환(guest → user) 시 정상 동작

---

## 7) 오늘 바로 분업 제안

- **FE 1명**: `authStore.ts` 게스트 ID 유틸 + ChatPage 초기 로드/전송 연결
- **BE 1명**: DB 마이그레이션 + 3개 엔드포인트(`/chat`, `/chat/threads`, `/chat/history/:id`)
- **QA 1명**: 위 체크리스트로 수동 테스트(한글/이모지 입력, 긴 문장, 빠른 연속 전송 등)
```

