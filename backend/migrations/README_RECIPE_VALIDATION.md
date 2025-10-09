# 레시피 검증 시스템 마이그레이션 가이드

## 📋 개요

골든셋 기반 레시피 검증 시스템을 위한 데이터베이스 스키마 마이그레이션입니다.

## 🗂️ 생성되는 테이블

1. **golden_recipes** - 검증된 골든셋 레시피 (30개 목표)
2. **transform_rules** - 변형 규칙 (swap, scale, 금지재료)
3. **generated_recipes** - AI 생성 레시피 및 심사 결과
4. **ingredient_normalization** - 재료 정규화 매핑

## 🚀 마이그레이션 실행

### Windows (PowerShell)

```powershell
# Supabase SQL Editor에서 실행
# 1. Supabase 대시보드 접속
# 2. SQL Editor 메뉴 선택
# 3. recipe_validation_schema.sql 파일 내용 복사하여 실행
```

### 로컬 PostgreSQL (개발용)

```powershell
# psql로 실행
psql -U postgres -d ketohelper -f backend/migrations/recipe_validation_schema.sql

# 또는 Python 스크립트로 실행
python backend/scripts/run_migration.py
```

## ✅ 마이그레이션 검증

```sql
-- 테이블 생성 확인
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('golden_recipes', 'transform_rules', 'generated_recipes', 'ingredient_normalization');

-- 샘플 데이터 확인
SELECT COUNT(*) FROM golden_recipes WHERE is_active = true;
SELECT COUNT(*) FROM ingredient_normalization;

-- 함수 확인
SELECT routine_name FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name IN ('normalize_ingredient', 'search_golden_recipes');
```

## 📊 예상 결과

```
✅ Tables: 4개 생성됨
✅ Indexes: 10개 생성됨
✅ Functions: 2개 생성됨
✅ Sample Data: 골든셋 1개, 규칙 1개, 재료 10개
```

## 🔄 롤백 (필요시)

```sql
-- 테이블 삭제 (역순)
DROP TABLE IF EXISTS generated_recipes CASCADE;
DROP TABLE IF EXISTS transform_rules CASCADE;
DROP TABLE IF EXISTS golden_recipes CASCADE;
DROP TABLE IF EXISTS ingredient_normalization CASCADE;

-- 함수 삭제
DROP FUNCTION IF EXISTS normalize_ingredient(TEXT);
DROP FUNCTION IF EXISTS search_golden_recipes(TEXT[]);
```

## 📝 다음 단계

1. ✅ 스키마 마이그레이션 완료
2. ⏳ 골든셋 데이터 30개 준비
3. ⏳ RecipeValidator 서비스 구현
4. ⏳ MealPlannerAgent 통합

## 🐛 트러블슈팅

### 오류: "relation already exists"
```sql
-- 기존 테이블 확인 후 DROP
DROP TABLE IF EXISTS golden_recipes CASCADE;
```

### 오류: "permission denied"
```sql
-- Supabase service_role 키 사용 확인
-- 또는 슈퍼유저 권한으로 실행
```

