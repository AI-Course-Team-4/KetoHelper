-- 🚨 CRITICAL BUG FIX: user_profile_detailed 뷰 배열 순서 문제 해결
-- 
-- 작성일: 2024-12-XX
-- 작성자: soohwan
-- 목적: Badge 삭제 시 잘못된 항목이 삭제되는 문제 해결
-- 
-- 문제: 뷰에서 ORDER BY name으로 정렬하여 selected_*_ids 배열과 *_names 배열의 순서가 맞지 않음
-- 해결: ORDER BY array_position()을 사용하여 원본 배열의 순서 유지
--
-- ⚠️  주의: 이 SQL을 Supabase SQL Editor에서 실행해야 합니다.
--
DROP VIEW IF EXISTS user_profile_detailed;

CREATE VIEW user_profile_detailed AS
SELECT 
    u.id,
    u.name,
    u.email,
    u.nickname,
    u.profile_image_url,
    u.profile_image_source,
    u.first_login,
    u.goals_kcal,
    u.goals_carbs_g,
    u.selected_allergy_ids,
    u.selected_dislike_ids,
    
    -- 선택된 알레르기 정보 (ID 배열 순서 유지)
    COALESCE(
        (SELECT array_agg(am.name ORDER BY array_position(u.selected_allergy_ids, am.id)) 
         FROM allergy_master am 
         WHERE am.id = ANY(u.selected_allergy_ids)), 
        '{}'::text[]
    ) AS allergy_names,
     
    -- 선택된 비선호 재료 정보 (ID 배열 순서 유지)
    COALESCE(
        (SELECT array_agg(dm.name ORDER BY array_position(u.selected_dislike_ids, dm.id)) 
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
