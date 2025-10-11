-- meal_log 테이블에 url 컬럼 추가
-- 식단표에서 생성된 레시피의 URL 정보를 저장하기 위한 컬럼

-- URL 컬럼 추가
ALTER TABLE public.meal_log 
ADD COLUMN IF NOT EXISTS url text;

-- URL 컬럼에 대한 코멘트 추가
COMMENT ON COLUMN public.meal_log.url IS '레시피 상세 페이지 URL (식단표에서 생성된 경우)';

-- 기존 데이터 확인 (URL이 있는 meal_log 수)
SELECT COUNT(*) as total_meal_logs, 
       COUNT(url) as meal_logs_with_url,
       COUNT(*) - COUNT(url) as meal_logs_without_url
FROM public.meal_log;

-- 샘플 데이터 확인 (URL이 있는 경우)
SELECT id, date, meal_type, note, url, created_at 
FROM public.meal_log 
WHERE url IS NOT NULL 
LIMIT 5;
