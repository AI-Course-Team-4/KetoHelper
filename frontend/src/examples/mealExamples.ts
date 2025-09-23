/**
 * LLM 식단 추천 응답 예시
 * 
 * ChatPage에서 "오늘 식단 추천해줘" 같은 자연어 요청을 하면,
 * LLM이 이런 형태의 JSON으로 응답할 수 있습니다.
 */

// 예시 1: 기본 식단 추천
export const EXAMPLE_MEAL_RESPONSE_1 = `
안녕하세요! 오늘의 키토 식단을 추천해드릴게요:

\`\`\`json
{
  "breakfast": "아보카도 토스트 (키토 빵 사용)와 스크램블 에그",
  "lunch": "그릴 치킨 샐러드 (올리브오일 드레싱)",
  "dinner": "연어 스테이크와 구운 브로콜리",
  "snack": "아몬드 한 줌과 치즈 큐브"
}
\`\`\`

이 식단은 탄수화물 20g 이하로 완벽한 키토 식단입니다!
`

// 예시 2: 한국어 키가 포함된 응답
export const EXAMPLE_MEAL_RESPONSE_2 = `
키토 다이어트를 위한 하루 식단을 준비했어요:

\`\`\`json
{
  "아침": "버터 커피와 베이컨 에그",
  "점심": "불고기 (설탕 없이)와 상추쌈",
  "저녁": "삼겹살 구이와 김치찌개 (무설탕)",
  "간식": "견과류 믹스"
}
\`\`\`

한국 음식으로도 충분히 키토를 실천할 수 있어요!
`

// 예시 3: 일주일 식단표
export const EXAMPLE_WEEKLY_MEAL_RESPONSE = `
7일 키토 식단표를 만들어드렸어요!

**월요일**
\`\`\`json
{
  "breakfast": "그릭 요거트와 베리류",
  "lunch": "치킨 케사디야 (키토 토르티야)",
  "dinner": "양고기 구이와 아스파라거스"
}
\`\`\`

**화요일**
\`\`\`json
{
  "breakfast": "아보카도 스무디",
  "lunch": "참치 샐러드",
  "dinner": "스테이크와 버터 구운 시금치"
}
\`\`\`

각 날짜별로 저장하시면 됩니다!
`

// 예시 4: 부분적 식단 (일부 끼니만)
export const EXAMPLE_PARTIAL_MEAL_RESPONSE = `
점심과 저녁 메뉴만 추천해드릴게요:

\`\`\`json
{
  "lunch": "연어 아보카도 볼",
  "dinner": "치킨 알프레도 (시라타키 면 사용)"
}
\`\`\`

아침은 이미 드셨다고 하니 점심과 저녁만 준비했어요!
`

/**
 * 식단 파싱 테스트 함수
 */
export const testMealParsing = () => {
  const { MealParserService } = require('../lib/mealService')
  
  console.log('=== 식단 파싱 테스트 ===')
  
  const examples = [
    EXAMPLE_MEAL_RESPONSE_1,
    EXAMPLE_MEAL_RESPONSE_2,
    EXAMPLE_PARTIAL_MEAL_RESPONSE
  ]
  
  examples.forEach((example, index) => {
    console.log(`\n--- 예시 ${index + 1} ---`)
    const result = MealParserService.parseMealFromResponse(example)
    console.log('파싱 결과:', result)
  })
}

/**
 * 실제 사용 예시
 */
export const USAGE_EXAMPLES = {
  // 사용자가 입력할 수 있는 자연어 질문들
  userQueries: [
    "오늘 식단 추천해줘",
    "아침 키토 레시피 알려줘", 
    "7일 키토 식단표 만들어줘",
    "점심으로 뭐 먹을까?",
    "키토 간식 추천해줘",
    "외식할 때 키토 메뉴 추천",
    "집에서 만들 수 있는 키토 요리"
  ],
  
  // LLM이 응답할 때 포함해야 할 JSON 형태
  expectedJsonStructure: {
    breakfast: "아침 식단 (선택적)",
    lunch: "점심 식단 (선택적)", 
    dinner: "저녁 식단 (선택적)",
    snack: "간식 (선택적)"
  },
  
  // 대체 가능한 한국어 키
  koreanKeys: {
    "아침": "breakfast",
    "점심": "lunch", 
    "저녁": "dinner",
    "간식": "snack"
  }
}
