// 키토 식단 더미 데이터
export const ketoMeals = {
  breakfast: [
    '아보카도 토스트',
    '계란 스크램블', 
    '베이컨 에그',
    '그릭 요거트',
    '아몬드 우유 라떼',
    '치즈 오믈렛',
    '버터 커피',
    '코코넛 팬케이크',
    '스모크드 새먼',
    '아보카도 스무디',
    '크림 치즈 팬케이크',
    '햄 앤 치즈 오믈렛',
    '아보카도 에그 베네딕트',
    '코코넛 밀크 라떼',
    '프로틴 스무디'
  ],
  lunch: [
    '그릴 치킨 샐러드',
    '불고기',
    '스테이크',
    '새우볶음밥',
    '생선구이',
    '연어 스테이크',
    '치킨 샐러드',
    '비프 스테이크',
    '참치 샐러드',
    '돼지고기 구이',
    '치킨 케사디야',
    '연어 아보카도 볼',
    '비프 버거 (빵 없이)',
    '치킨 스트립 샐러드',
    '연어 타르타르'
  ],
  dinner: [
    '연어 스테이크',
    '새우볶음밥',
    '생선구이',
    '치킨 스테이크',
    '비프 스테이크',
    '돼지고기 구이',
    '참치 스테이크',
    '랍스터 테일',
    '양고기 구이',
    '오리 구이',
    '치킨 파마지아나',
    '연어 테리야키',
    '비프 웰링턴',
    '치킨 알프레도',
    '연어 그라브락스'
  ],
  snack: [
    '아몬드',
    '호두',
    '치즈',
    '올리브',
    '아보카도',
    '코코넛 칩',
    '다크 초콜릿',
    '그릭 요거트',
    '베리류',
    '견과류 믹스',
    '치즈 큐브',
    '아보카도 푸딩',
    '코코넛 바',
    '프로틴 바',
    '치즈 크래커'
  ]
}

// 식단 타입 정의
export interface MealData {
  breakfast: string
  lunch: string
  dinner: string
  snack: string
  // 체크 상태 추가
  breakfastCompleted?: boolean
  lunchCompleted?: boolean
  dinnerCompleted?: boolean
  snackCompleted?: boolean
}

// 랜덤 식단 생성 함수
export const generateRandomMeal = (): MealData => {
  const getRandomItem = (array: string[]) => array[Math.floor(Math.random() * array.length)]
  
  return {
    breakfast: getRandomItem(ketoMeals.breakfast),
    lunch: getRandomItem(ketoMeals.lunch),
    dinner: getRandomItem(ketoMeals.dinner),
    snack: getRandomItem(ketoMeals.snack)
  }
}
