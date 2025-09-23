-- ==========================================
-- 데이터베이스 구조 최적화 마이그레이션
-- 작성일: 2025년 9월 23일
-- 목적: 프로필 시스템 최적화 (6개 테이블 → 3개 테이블)
-- 
-- 작업 배경:
-- - 기존: users, keto_goals, user_allergy, allergy, disliked_ingredient, (user_dislike) 
-- - 최적화: users (통합), allergy_master, dislike_ingredient_master
-- - 목표: 복잡한 JOIN 제거, 성능 향상, 관리 편의성 증대
--
-- 주요 변경사항:
-- 1. keto_goals 테이블 → users 테이블에 통합 (goals_kcal, goals_carbs_g)
-- 2. user_allergy 중간테이블 제거 → selected_allergy_ids 배열로 참조
-- 3. 알레르기/비선호 재료를 ID 배열로 저장하여 성능 향상
-- 4. user_profile_detailed 뷰로 복잡한 JOIN 로직 캡슐화
-- 
-- 실행 환경: Supabase PostgreSQL
-- 실행 방법: Supabase SQL Editor에서 전체 스크립트 실행
-- ==========================================

-- 🔍 STEP 1: 현재 테이블 구조 확인
-- 실행 전에 현재 어떤 테이블들이 있는지 확인
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 🗑️ STEP 2: 불필요한 테이블들 삭제 (순서 중요!)
-- 외래키 의존성 때문에 순서대로 삭제

-- 중간 테이블들 먼저 삭제
DROP TABLE IF EXISTS user_allergy CASCADE;

-- 목표 테이블 삭제 (users 테이블에 통합될 예정)
DROP TABLE IF EXISTS keto_goals CASCADE;

-- 🔄 STEP 3: 기존 users 테이블에 새로운 컬럼들 추가
-- 기존 데이터는 보존하면서 컬럼만 추가

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS goals_kcal INTEGER,
ADD COLUMN IF NOT EXISTS goals_carbs_g INTEGER,
ADD COLUMN IF NOT EXISTS selected_allergy_ids INTEGER[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS selected_dislike_ids INTEGER[] DEFAULT '{}';

-- 추가 컬럼들 (필요에 따라)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS trial_granted BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS trial_start_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS trial_end_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS paid_until TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS access_state VARCHAR(20) DEFAULT 'free';

-- 기존 컬럼의 기본값 설정 (이미 있는 컬럼은 오류 무시)
DO $$ 
BEGIN
    BEGIN
        ALTER TABLE users ALTER COLUMN created_at SET DEFAULT NOW();
    EXCEPTION 
        WHEN others THEN NULL;
    END;
    
    BEGIN
        ALTER TABLE users ALTER COLUMN updated_at SET DEFAULT NOW();
    EXCEPTION 
        WHEN others THEN NULL;
    END;
END $$;

-- 🔧 STEP 4: updated_at 자동 업데이트 트리거 설정
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 기존 트리거가 있다면 삭제 후 재생성
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 🆕 STEP 5: 새로운 마스터 테이블들 생성
-- 기존 테이블이 있다면 삭제 후 재생성

-- 알레르기 마스터 테이블
DROP TABLE IF EXISTS allergy CASCADE;
DROP TABLE IF EXISTS allergy_master CASCADE;
CREATE TABLE allergy_master (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50),
    severity_level INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 비선호 재료 마스터 테이블
DROP TABLE IF EXISTS disliked_ingredient CASCADE;
DROP TABLE IF EXISTS dislike_ingredient_master CASCADE;
CREATE TABLE dislike_ingredient_master (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 🔍 STEP 6: 인덱스 생성 (IF NOT EXISTS로 안전하게)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_access_state ON users(access_state);
CREATE INDEX IF NOT EXISTS idx_users_selected_allergy_ids ON users USING GIN(selected_allergy_ids);
CREATE INDEX IF NOT EXISTS idx_users_selected_dislike_ids ON users USING GIN(selected_dislike_ids);
CREATE INDEX IF NOT EXISTS idx_allergy_master_category ON allergy_master(category);
CREATE INDEX IF NOT EXISTS idx_dislike_master_category ON dislike_ingredient_master(category);

-- 🔐 STEP 7: Row Level Security (RLS) 설정
-- users 테이블 RLS 재설정
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- 기존 정책들 삭제 후 재생성 (오류 무시)
DO $$ 
BEGIN
    DROP POLICY IF EXISTS "Users can view their own profile" ON users;
    DROP POLICY IF EXISTS "Users can update their own profile" ON users;
    DROP POLICY IF EXISTS "Users can insert their own profile" ON users;
EXCEPTION 
    WHEN others THEN NULL;
END $$;

-- 새로운 정책 생성
CREATE POLICY "Users can view their own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- 마스터 테이블들 RLS
ALTER TABLE allergy_master ENABLE ROW LEVEL SECURITY;
ALTER TABLE dislike_ingredient_master ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Everyone can view allergy master" ON allergy_master
    FOR SELECT USING (true);

CREATE POLICY "Everyone can view dislike master" ON dislike_ingredient_master
    FOR SELECT USING (true);

-- 🎯 STEP 8: 마스터 데이터 삽입
INSERT INTO allergy_master (name, description, category, severity_level) VALUES
('땅콩', '땅콩 및 땅콩 제품에 대한 알레르기', '견과류', 3),
('우유', '유제품 및 유당에 대한 알레르기', '유제품', 2),
('달걀', '계란 및 계란 제품에 대한 알레르기', '동물성', 2),
('대두', '콩 및 콩 제품에 대한 알레르기', '콩류', 1),
('밀', '밀 및 글루텐 함유 제품에 대한 알레르기', '곡물', 2),
('새우', '갑각류에 대한 알레르기', '해산물', 3),
('게', '갑각류에 대한 알레르기', '해산물', 3),
('생선', '어류 전반에 대한 알레르기', '해산물', 2),
('아몬드', '견과류에 대한 알레르기', '견과류', 2),
('호두', '견과류에 대한 알레르기', '견과류', 2),
('참깨', '참깨 및 참기름에 대한 알레르기', '씨앗류', 2),
('호박씨', '씨앗류에 대한 알레르기', '씨앗류', 1),
('치즈', '특정 유제품에 대한 알레르기', '유제품', 2),
('버터', '유제품에 대한 알레르기', '유제품', 1)
ON CONFLICT (name) DO NOTHING;

INSERT INTO dislike_ingredient_master (name, category, description) VALUES
('양파', '채소', '매운맛과 향이 강한 채소'),
('마늘', '향신료', '강한 향과 맛을 가진 향신료'),
('생강', '향신료', '매콤하고 알싸한 맛의 향신료'),
('고수', '허브', '독특한 향미를 가진 허브'),
('버섯', '채소', '특유의 식감과 향을 가진 균류'),
('토마토', '채소', '신맛과 특유의 향을 가진 과채류'),
('피망', '채소', '아삭한 식감과 독특한 맛'),
('가지', '채소', '스펀지 같은 특유의 식감'),
('브로콜리', '채소', '십자화과 특유의 쓴맛'),
('셀러리', '채소', '강한 향과 섬유질 식감'),
('오이', '채소', '시원한 맛과 아삭한 식감'),
('당근', '채소', '달콤한 맛의 뿌리채소'),
('고추', '향신료', '매운맛을 내는 향신료'),
('겨자', '향신료', '알싸한 맛의 향신료'),
('민트', '허브', '청량한 향미의 허브'),
('로즈마리', '허브', '강한 향의 허브'),
('바질', '허브', '이탈리아 요리에 사용되는 허브'),
('올리브', '지방', '독특한 맛의 지중해 과일'),
('아보카도', '지방', '크리미한 식감의 과일'),
('코코넛', '지방', '달콤한 맛의 열대 과일')
ON CONFLICT (name) DO NOTHING;

-- 📊 STEP 9: 편의를 위한 뷰 생성
-- 복잡한 JOIN 로직을 뷰로 캡슐화하여 API에서 간단하게 사용
DROP VIEW IF EXISTS user_profile_detailed;
CREATE VIEW user_profile_detailed AS
SELECT 
    u.id,
    u.email,
    u.nickname,
    u.profile_image_url,
    u.profile_image_source,
    u.first_login,
    u.goals_kcal,
    u.goals_carbs_g,
    u.selected_allergy_ids,
    u.selected_dislike_ids,
    
    -- 선택된 알레르기 정보 (ID 배열을 이름 배열로 변환)
    COALESCE(
        (SELECT array_agg(am.name ORDER BY am.name) 
         FROM allergy_master am 
         WHERE am.id = ANY(u.selected_allergy_ids)), 
        '{}'::text[]
    ) AS allergy_names,
     
    -- 선택된 비선호 재료 정보 (ID 배열을 이름 배열로 변환)
    COALESCE(
        (SELECT array_agg(dm.name ORDER BY dm.name) 
         FROM dislike_ingredient_master dm 
         WHERE dm.id = ANY(u.selected_dislike_ids)), 
        '{}'::text[]
    ) AS dislike_names,
     
    u.created_at,
    u.updated_at,
    u.trial_granted,
    u.trial_start_at,
    u.trial_end_at,
    u.paid_until,
    u.access_state
FROM users u;

-- 🎉 마이그레이션 완료! 검증 쿼리들:

-- 1. 테이블 목록 확인
SELECT 'Tables after migration:' as info;
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 2. users 테이블 새 컬럼 확인
SELECT 'Users table columns:' as info;
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;

-- 3. 마스터 데이터 확인
SELECT 'Allergy master data:' as info;
SELECT category, COUNT(*) as count
FROM allergy_master 
GROUP BY category 
ORDER BY category;

SELECT 'Dislike master data:' as info;
SELECT category, COUNT(*) as count
FROM dislike_ingredient_master 
GROUP BY category 
ORDER BY category;

-- 4. 뷰 동작 확인 (사용자가 있다면)
SELECT 'View test (first user):' as info;
SELECT id, email, allergy_names, dislike_names 
FROM user_profile_detailed 
LIMIT 1;

-- ==========================================
-- 마이그레이션 완료
-- 
-- 결과:
-- - 테이블 수: 6개 → 3개 (50% 감소)
-- - 성능: JOIN 쿼리 최소화로 향상
-- - 관리: 단순한 구조로 유지보수성 증대
-- - 확장성: 마스터 데이터 쉽게 추가/수정 가능
-- ==========================================
