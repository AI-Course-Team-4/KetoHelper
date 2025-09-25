-- 키토 코치 채팅 연속성 및 비로그인 사용자 지원을 위한 데이터베이스 마이그레이션
-- 실행 순서: Supabase SQL Editor에서 이 파일을 순서대로 실행

-- 1) chat_thread 테이블 생성 (대화 스레드 관리)
CREATE TABLE IF NOT EXISTS public.chat_thread (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL DEFAULT '새 채팅',
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  guest_id UUID, -- 게스트 사용자 ID (localStorage에서 생성)
  last_message_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2) chat 테이블 수정 (기존 messages 테이블을 chat으로 변경)
-- 먼저 기존 messages 테이블이 있는지 확인하고 chat 테이블로 변경
DO $$
BEGIN
  -- messages 테이블이 존재하면 chat으로 이름 변경
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'messages' AND table_schema = 'public') THEN
    ALTER TABLE public.messages RENAME TO chat;
  END IF;
END$$;

-- 3) chat 테이블에 필요한 컬럼들 추가/수정
ALTER TABLE public.chat
  ADD COLUMN IF NOT EXISTS thread_id UUID REFERENCES public.chat_thread(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS guest_id UUID,
  ALTER COLUMN role DROP NOT NULL,
  ALTER COLUMN content DROP NOT NULL;

-- 4) chat 테이블의 content 컬럼을 message로 변경 (요구사항에 맞춤)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'chat' AND column_name = 'content' AND table_schema = 'public') THEN
    ALTER TABLE public.chat RENAME COLUMN content TO message;
  END IF;
END$$;

-- 5) user_id NULL 허용 (게스트 스레드 지원)
ALTER TABLE public.chat_thread
  ALTER COLUMN user_id DROP NOT NULL;

-- 6) 체크 제약: user_id XOR guest_id (둘 중 하나만 있어야 함)
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

-- 7) chat 테이블에도 동일한 제약 추가
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'chat_user_or_guest'
  ) THEN
    ALTER TABLE public.chat
    ADD CONSTRAINT chat_user_or_guest
    CHECK (
      (user_id IS NOT NULL AND guest_id IS NULL)
      OR (user_id IS NULL AND guest_id IS NOT NULL)
    );
  END IF;
END$$;

-- 8) 성능 향상을 위한 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_chat_thread_user_id ON public.chat_thread(user_id, last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_thread_guest_id ON public.chat_thread(guest_id, last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_thread_id ON public.chat(thread_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_chat_user_id ON public.chat(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_guest_id ON public.chat(guest_id, created_at DESC);

-- 9) 기존 데이터 마이그레이션 (messages -> chat)
-- 기존 messages 테이블의 데이터가 있다면 chat_thread와 연결
DO $$
DECLARE
  default_thread_id UUID;
BEGIN
  -- 기본 스레드 생성 (기존 데이터용)
  INSERT INTO public.chat_thread (id, title, user_id, guest_id)
  VALUES (gen_random_uuid(), '기존 대화', NULL, NULL)
  RETURNING id INTO default_thread_id;
  
  -- 기존 messages 데이터를 chat으로 이동 (있다면)
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chat' AND table_schema = 'public') THEN
    UPDATE public.chat 
    SET thread_id = default_thread_id 
    WHERE thread_id IS NULL;
  END IF;
END$$;

-- 10) 게스트 데이터 30일 후 자동 삭제를 위한 함수 생성
CREATE OR REPLACE FUNCTION cleanup_guest_chat_data()
RETURNS void AS $$
BEGIN
  -- 30일 이상 된 게스트 채팅 메시지 삭제
  DELETE FROM public.chat 
  WHERE guest_id IS NOT NULL 
    AND created_at < NOW() - INTERVAL '30 days';
  
  -- 30일 이상 된 게스트 채팅 스레드 삭제
  DELETE FROM public.chat_thread 
  WHERE guest_id IS NOT NULL 
    AND last_message_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- 11) 정리 함수 실행 (선택사항 - 테스트용)
-- SELECT cleanup_guest_chat_data();

-- 12) 마이그레이션 완료 확인
SELECT 
  'chat_thread' as table_name,
  COUNT(*) as row_count
FROM public.chat_thread
UNION ALL
SELECT 
  'chat' as table_name,
  COUNT(*) as row_count
FROM public.chat;
