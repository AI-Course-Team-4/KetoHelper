      이어트 웹사이트 - 식단 관리 기능 구현 가이드 (업데이트)

## 📋 구현된 기능 개요

### 1. 채팅 페이지에서 LLM 식단 추천
- 사용자가 자연어로 "오늘 식단 추천해줘" 요청
- 백엔드에서 ChatResponse 형태로 식단 데이터 응답 (results 배열 또는 response 텍스트)
- 추천받은 식단을 '캘린더에 저장' 버튼으로 Supabase에 저장 (로그인 필수)

### 2. 캘린더 페이지에서 식단 관리
- Supabase에서 식단 데이터 불러와 캘린더에 표시 (로그인 필수)
- 날짜별 식단 완성도를 색상과 도트로 시각화
- 날짜 클릭 시 해당 날짜의 식단 정보 모달로 표시 및 수정 가능

### 3. Supabase 데이터베이스 연동
- 실시간 식단 데이터 저장, 조회, 수정
- 로그인 필수 - 사용자 인증 없이는 기능 사용 불가

## 🔐 인증 시스템 변경사항

### ❌ 제거된 기능
- 임시 사용자 ID 생성/관리 (`getTempUserId`, `clearTempUserId`)
- 로그인 없이 식단 데이터 저장/조회

### ✅ 추가된 기능
- 모든 식단 관련 함수에서 `userId` 매개변수 필수
- 로그인 상태 확인 및 에러 처리
- 로그인 안내 UI (CalendarPage)
- 제한적 기능 안내 (ChatPage)

## 🗄️ Supabase 테이블 스키마

```sql
CREATE TABLE meals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,  -- 필수 (로그인한 사용자만)
  date DATE NOT NULL,
  breakfast TEXT,
  lunch TEXT,
  dinner TEXT,
  snack TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX idx_meals_user_date ON meals(user_id, date);
CREATE INDEX idx_meals_date ON meals(date);
```

## 🔧 주요 구현 파일 변경사항

### 1. MealService (`src/lib/mealService.ts`) - 업데이트
```typescript
export class MealService {
  // 모든 함수에서 userId 필수로 변경
  static async saveMeal(date: string, mealData: MealData, userId: string): Promise<boolean>
  static async getMealByDate(date: string, userId: string): Promise<MealData | null>
  static async getMealsByDateRange(startDate: string, endDate: string, userId: string): Promise<Record<string, MealData>>
  static async deleteMeal(date: string, userId: string): Promise<boolean>
}

// 백엔드 응답 파싱 추가
export class MealParserService {
  // 새로 추가: 백엔드 ChatResponse에서 식단 데이터 추출
  static parseMealFromBackendResponse(chatResponse: any): LLMParsedMeal | null
  // 기존: LLM 응답 텍스트에서 식단 JSON 추출
  static parseMealFromResponse(response: string): LLMParsedMeal | null
}
```

### 2. ChatPage 업데이트 (`src/pages/ChatPage.tsx`)
- `useAuthStore` 추가로 로그인 상태 확인
- 백엔드 응답 파싱: `parseMealFromBackendResponse` 사용
- 식단 저장 시 로그인 체크 및 에러 메시지
- 비로그인 사용자에게 제한 안내

### 3. CalendarPage 업데이트 (`src/pages/CalendarPage.tsx`)
- `useAuthStore` 추가로 로그인 상태 확인
- 비로그인 시 로그인 안내 화면 표시
- 모든 식단 관련 함수에 `user.id` 전달
- 로그인 상태 변경 시 데이터 자동 로드

## 🎯 백엔드 응답 구조

### ChatResponse 구조 (FastAPI)
```typescript
interface ChatResponse {
  response: string          // AI 응답 텍스트
  intent: string           // 의도 분류 (예: "meal_planning")
  results?: Array<any>     // 검색 결과 배열
  session_id?: string      // 세션 ID
}
```

### 식단 데이터 위치
1. **results 배열**: 7일 식단표나 구조화된 데이터
   ```typescript
   results: [
     {
       type: 'meal_plan',
       days: [
         {
           breakfast: { title: "아침 메뉴" },
           lunch: { title: "점심 메뉴" },
           dinner: { title: "저녁 메뉴" }
         }
       ]
     }
   ]
   ```

2. **response 텍스트**: JSON 형태로 포함된 식단
   ```typescript
   response: `오늘의 키토 식단을 추천해드릴게요:
   \`\`\`json
   {
     "breakfast": "아보카도 토스트",
     "lunch": "그릴 치킨 샐러드",
     "dinner": "연어 스테이크"
   }
   \`\`\``
   ```

## 🔄 업데이트된 데이터 흐름

```
사용자 질문 → 백엔드 ChatResponse → 식단 파싱 → 로그인 체크 → Supabase 저장 → 캘린더 표시
     ↑                                           ↓
   로그인 필수 ←←←←←←←←←←←←←←←←←←← 인증 상태 확인
```

## 🎨 UI/UX 업데이트

### 1. 로그인 안내 화면 (CalendarPage)
```typescript
if (!user) {
  return (
    <div className="text-center py-12">
      <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-6" />
      <h2 className="text-2xl font-bold mb-4">로그인이 필요합니다</h2>
      <p className="text-muted-foreground mb-6">
        식단 캘린더를 사용하려면 로그인해주세요.
      </p>
      <Button onClick={() => window.location.href = '/login'}>
        로그인하기
      </Button>
    </div>
  )
}
```

### 2. 제한 안내 메시지 (ChatPage)
- 로그인 전: "식단 저장 기능은 로그인 후 이용 가능합니다."
- 식단 저장 시도 시: "❌ 식단 저장을 위해 로그인이 필요합니다."

## 🚀 사용 방법 (업데이트)

### 1. 식단 추천받기
1. **로그인 상태 확인** ← 새로 추가
2. 채팅 페이지에서 "오늘 식단 추천해줘" 입력
3. 백엔드에서 ChatResponse 형태로 식단 추천
4. 추천받은 식단 카드에서 "캘린더에 저장" 버튼 클릭
5. 성공 메시지 확인

### 2. 캘린더에서 식단 관리
1. **로그인 필수** ← 새로 추가
2. 캘린더 페이지로 이동
3. 식단이 저장된 날짜는 색상으로 표시됨
4. 날짜 클릭 시 상세 정보 모달 열림
5. 모달에서 식단 수정 가능

### 3. 비로그인 사용자
- **채팅**: 식단 추천 받기 가능, 저장은 불가
- **캘린더**: 로그인 안내 화면 표시

## 🔧 개발자 가이드 (업데이트)

### 1. 인증 상태 확인
```typescript
import { useAuthStore } from '@/store/authStore'

const { user } = useAuthStore()
if (!user?.id) {
  // 로그인 필요 처리
  return
}
```

### 2. 식단 데이터 처리
```typescript
// 백엔드 응답 파싱
const parsedMeal = MealParserService.parseMealFromBackendResponse(response)

// 식단 저장 (userId 필수)
await MealService.saveMeal(date, mealData, user.id)
```

### 3. 에러 처리
```typescript
try {
  await MealService.saveMeal(date, mealData, user.id)
} catch (error) {
  if (error.message.includes('로그인')) {
    // 로그인 에러 처리
  }
}
```

## 📊 주요 변경사항 요약

| 항목 | 이전 | 현재 |
|------|------|------|
| 사용자 인증 | 임시 ID 지원 | 로그인 필수 |
| 식단 저장 | `saveMeal(date, data)` | `saveMeal(date, data, userId)` |
| 식단 조회 | `getMealByDate(date)` | `getMealByDate(date, userId)` |
| 응답 파싱 | `parseMealFromResponse` | `parseMealFromBackendResponse` |
| UI 접근성 | 모든 기능 접근 가능 | 로그인 필수 안내 |

이제 모든 식단 관리 기능이 로그인 기반으로 동작하며, 백엔드 응답 구조에 맞춰 최적화되었습니다! 🥑
