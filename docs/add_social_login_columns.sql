-- 소셜 로그인 컬럼 추가 SQL
-- users 테이블에 소셜 로그인 관련 컬럼들을 추가합니다.
-- 참고: email, profile_image_url, social_nickname 컬럼은 이미 존재합니다.
-- 참고: 현재 id 컬럼이 이미 각 플랫폼의 고유 ID를 저장하고 있습니다.

-- 1. 소셜 로그인 플랫폼 컬럼 추가 (provider_id는 불필요 - 현재 id가 이미 플랫폼별 고유 ID)
ALTER TABLE users 
ADD COLUMN provider TEXT CHECK (provider IN ('google', 'kakao', 'naver'));

-- 2. provider_id는 불필요 - 현재 id 컬럼이 이미 각 플랫폼의 고유 ID를 저장
-- 3. 이메일 컬럼은 이미 존재하므로 추가하지 않음
-- 4. profile_image_url, social_nickname 컬럼도 이미 존재

-- 5. 복합 유니크 제약 조건 추가 (provider + id 조합이 유니크해야 함)
ALTER TABLE users 
ADD CONSTRAINT unique_provider_id UNIQUE (provider, id);

-- 6. 이메일 유니크 제약 조건 추가 (이메일이 있는 경우에만)
-- 참고: email 컬럼이 이미 존재하므로 기존 제약 조건이 있는지 확인 필요
-- ALTER TABLE users 
-- ADD CONSTRAINT unique_email UNIQUE (email);

-- 7. 인덱스 추가 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_users_provider ON users(provider);
-- id는 이미 PRIMARY KEY이므로 별도 인덱스 불필요
-- email 인덱스는 이미 존재할 가능성이 높음

-- 8. 기존 데이터 마이그레이션을 위한 주석
-- 기존 사용자가 있다면 다음과 같이 업데이트할 수 있습니다:
-- UPDATE users SET provider = 'google' WHERE id = '기존_uuid';
-- UPDATE users SET provider = 'kakao' WHERE id = '기존_uuid';
-- UPDATE users SET provider = 'naver' WHERE id = '기존_uuid';
-- email, profile_image_url, social_nickname은 이미 존재하는 컬럼이므로 별도 업데이트 불필요

-- 9. 성공 메시지
SELECT '소셜 로그인 컬럼 추가 완료!' as result;
