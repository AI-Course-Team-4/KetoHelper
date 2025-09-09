# KetoHelper 백엔드 데이터베이스 스키마 및 API 설계

## 📋 목차
1. [데이터베이스 스키마](#데이터베이스-스키마)
2. [인덱스 설정](#인덱스-설정)
3. [API 엔드포인트](#api-엔드포인트)
4. [데이터 관계도](#데이터-관계도)

---

## 🗄️ 데이터베이스 스키마

### 1. Users Collection
```javascript
{
  _id: ObjectId,
  email: String, // unique, indexed
  password: String, // hashed with bcrypt
  name: String,
  profileImage: String,
  googleId: String, // for Google OAuth, sparse index
  
  // 개인 정보
  preferences: {
    allergies: [String], // ['견과류', '유제품', '글루텐']
    dislikes: [String], // ['브로콜리', '버섯']
    dietaryRestrictions: [String], // ['비건', '락토프리']
    experienceLevel: String, // enum: ['beginner', 'intermediate', 'advanced']
    goals: {
      targetWeight: Number, // kg
      targetCalories: Number, // per day
      macroRatio: {
        carbs: Number, // percentage (5-10% for keto)
        protein: Number, // percentage (20-25% for keto)
        fat: Number // percentage (70-75% for keto)
      }
    }
  },
  
  // 앱 설정
  settings: {
    notifications: {
      mealReminders: Boolean,
      recommendations: Boolean,
      weeklyReport: Boolean
    },
    units: String, // enum: ['metric', 'imperial']
    language: String, // 'ko', 'en'
    timezone: String // 'Asia/Seoul'
  },
  
  // 구독 정보
  subscription: {
    isActive: Boolean,
    plan: String, // enum: ['free', 'premium']
    startDate: Date,
    endDate: Date,
    autoRenewal: Boolean,
    paymentMethodId: String,
    stripeCustomerId: String
  },
  
  // 다이어트 계획
  dietPlan: {
    currentWeight: Number, // kg
    targetWeight: Number, // kg
    intensity: String, // enum: ['low', 'medium', 'high']
    startDate: Date,
    estimatedEndDate: Date,
    dailyCalories: Number,
    macroTargets: {
      carbs: Number, // grams
      protein: Number, // grams
      fat: Number // grams
    }
  },
  
  // 통계 정보
  stats: {
    streakDays: Number,
    totalDaysOnPlan: Number,
    completionRate: Number, // 0-100
    totalRecipesCompleted: Number,
    favoriteRecipesCount: Number
  },
  
  // 메타데이터
  isActive: Boolean,
  isEmailVerified: Boolean,
  lastLoginAt: Date,
  createdAt: Date,
  updatedAt: Date
}
```

### 2. Recipes Collection
```javascript
{
  _id: ObjectId,
  title: String, // indexed for search
  description: String, // indexed for search
  imageUrl: String,
  videoUrl: String, // optional cooking video
  authorId: ObjectId, // reference to Users (admin/chef)
  
  // 조리 정보
  cookingTime: Number, // minutes
  prepTime: Number, // preparation time in minutes
  difficulty: String, // enum: ['쉬움', '중간', '어려움']
  servings: Number,
  
  // 재료 정보
  ingredients: [{
    name: String, // '아보카도'
    amount: Number, // 2
    unit: String, // '개', 'g', 'ml', '큰술'
    carbs: Number, // carbs per ingredient
    calories: Number, // calories per ingredient
    protein: Number,
    fat: Number,
    isOptional: Boolean,
    alternatives: [String] // 대체 재료
  }],
  
  // 조리법
  instructions: [{
    step: Number,
    description: String,
    imageUrl: String, // optional step image
    timer: Number // optional timer in minutes
  }],
  
  // 영양 정보 (per serving)
  nutrition: {
    calories: Number,
    carbs: Number, // total carbs
    netCarbs: Number, // carbs - fiber
    protein: Number,
    fat: Number,
    fiber: Number,
    sugar: Number,
    sodium: Number, // mg
    cholesterol: Number, // mg
    saturatedFat: Number,
    unsaturatedFat: Number
  },
  
  // 분류 및 태그
  category: String, // '메인요리', '사이드', '간식', '음료', '디저트'
  mealTypes: [String], // ['아침', '점심', '저녁', '간식']
  tags: [String], // ['키토', '저탄수화물', '간단', '30분', '원팟'] - indexed
  cuisine: String, // '한식', '양식', '일식', '중식', '이탈리안'
  season: [String], // ['봄', '여름', '가을', '겨울']
  
  // 키토 관련
  isKetoFriendly: Boolean,
  ketoScore: Number, // 0-100 (higher is more keto-friendly)
  carbsPerServing: Number,
  ketogenicRatio: Number, // fat/(protein+carbs) ratio
  
  // 평점 및 리뷰
  rating: Number, // average rating 0-5
  reviewCount: Number,
  totalRating: Number, // sum of all ratings (for average calculation)
  
  // 난이도별 세부 정보
  skillsRequired: [String], // ['칼질', '볶기', '굽기']
  equipment: [String], // ['오븐', '블렌더', '팬']
  
  // 상태 및 메타데이터
  status: String, // enum: ['draft', 'published', 'archived']
  isPublic: Boolean,
  isFeatured: Boolean, // 추천 레시피 여부
  viewCount: Number,
  likeCount: Number,
  shareCount: Number,
  saveCount: Number, // 즐겨찾기 횟수
  
  // SEO
  slug: String, // unique, indexed for URL
  metaDescription: String,
  keywords: [String],
  
  // 버전 관리
  version: Number,
  lastReviewedAt: Date,
  
  createdAt: Date,
  updatedAt: Date
}
```

### 3. MealPlans Collection
```javascript
{
  _id: ObjectId,
  userId: ObjectId, // reference to Users, indexed
  date: Date, // indexed, YYYY-MM-DD format
  weekNumber: Number, // week of year for weekly queries
  
  // 식사별 계획
  meals: {
    breakfast: {
      recipeId: ObjectId, // reference to Recipes
      recipe: Object, // denormalized recipe data for quick access
      scheduledTime: String, // '07:00'
      isCompleted: Boolean,
      completedAt: Date,
      actualServings: Number, // 실제 섭취한 인분
      notes: String,
      personalRating: Number // 1-5
    },
    lunch: {
      recipeId: ObjectId,
      recipe: Object,
      scheduledTime: String, // '12:00'
      isCompleted: Boolean,
      completedAt: Date,
      actualServings: Number,
      notes: String,
      personalRating: Number
    },
    dinner: {
      recipeId: ObjectId,
      recipe: Object,
      scheduledTime: String, // '19:00'
      isCompleted: Boolean,
      completedAt: Date,
      actualServings: Number,
      notes: String,
      personalRating: Number
    },
    snacks: [{
      recipeId: ObjectId,
      recipe: Object,
      scheduledTime: String,
      isCompleted: Boolean,
      completedAt: Date,
      actualServings: Number,
      notes: String,
      personalRating: Number
    }]
  },
  
  // 일일 영양 총합 (계획된 값)
  plannedNutrition: {
    calories: Number,
    carbs: Number,
    netCarbs: Number,
    protein: Number,
    fat: Number,
    fiber: Number
  },
  
  // 실제 섭취 영양 (완료된 식사 기준)
  actualNutrition: {
    calories: Number,
    carbs: Number,
    netCarbs: Number,
    protein: Number,
    fat: Number,
    fiber: Number
  },
  
  // 목표 대비 달성률
  nutritionGoalAchievement: {
    calories: Number, // percentage 0-100
    carbs: Number,
    protein: Number,
    fat: Number
  },
  
  // 진행률
  completionRate: Number, // 0-100 (완료된 식사 비율)
  isCompleted: Boolean, // 모든 식사 완료 여부
  totalMeals: Number, // 계획된 총 식사 수
  completedMeals: Number, // 완료된 식사 수
  
  // 일일 메모
  dailyNotes: String,
  mood: String, // 'great', 'good', 'okay', 'poor'
  energyLevel: Number, // 1-5
  
  createdAt: Date,
  updatedAt: Date
}
```

### 4. UserFavorites Collection
```javascript
{
  _id: ObjectId,
  userId: ObjectId, // reference to Users, indexed
  recipeId: ObjectId, // reference to Recipes, indexed
  
  // 즐겨찾기 메타데이터
  addedAt: Date,
  category: String, // '아침', '점심', '저녁', '간식', '일반'
  personalNotes: String, // 개인 메모
  personalRating: Number, // 개인 평점 1-5
  timesCooked: Number, // 요리한 횟수
  lastCookedAt: Date,
  
  // 개인 수정사항
  personalModifications: [String], // 개인적으로 수정한 내용
  customTags: [String], // 개인 태그
  
  // 복합 인덱스 (userId, recipeId) - unique
}
```

### 5. Restaurants Collection
```javascript
{
  _id: ObjectId,
  name: String, // indexed for search
  description: String,
  businessRegistrationNumber: String, // 사업자등록번호
  
  // 위치 정보
  address: {
    full: String, // 전체 주소
    city: String, // 도시
    district: String, // 구/군
    neighborhood: String, // 동/면
    postalCode: String
  },
  location: {
    type: "Point", // GeoJSON for geospatial queries
    coordinates: [Number, Number] // [longitude, latitude]
  },
  
  // 연락처 정보
  phone: String,
  website: String,
  email: String,
  socialMedia: {
    instagram: String,
    facebook: String,
    blog: String
  },
  
  // 분류 정보
  category: String, // '한식', '양식', '일식', '중식', '카페'
  subCategory: [String], // ['BBQ', '구이', '찜'], ['파스타', '피자'], ['카페', '디저트']
  priceRange: Number, // 1-4 ($ to $$$$)
  
  // 운영 정보
  operatingHours: [{
    day: String, // 'monday', 'tuesday', ..., 'sunday'
    open: String, // '09:00'
    close: String, // '22:00'
    isHoliday: Boolean,
    breakTime: {
      start: String, // '15:00'
      end: String // '17:00'
    }
  }],
  
  // 메뉴 정보
  menu: [{
    id: String, // 메뉴 고유 ID
    name: String,
    description: String,
    price: Number,
    category: String, // '메인', '사이드', '음료', '디저트'
    
    // 영양 정보
    nutrition: {
      calories: Number,
      carbs: Number,
      protein: Number,
      fat: Number,
      fiber: Number,
      sodium: Number
    },
    
    // 키토 관련
    isKetoFriendly: Boolean,
    ketoModifications: [String], // ['빵 제거', '소스 빼기']
    carbCount: String, // 'Low', 'Medium', 'High'
    
    // 알레르기 정보
    allergens: [String], // ['견과류', '유제품', '글루텐']
    spicyLevel: Number, // 0-5
    
    // 상태
    isAvailable: Boolean,
    isPopular: Boolean,
    isRecommended: Boolean, // 키토 추천 메뉴
    
    // 이미지
    imageUrl: String,
    
    createdAt: Date,
    updatedAt: Date
  }],
  
  // 키토 친화도
  ketoScore: Number, // 0-100 키토 친화도 점수
  ketoFriendlyMenuCount: Number, // 키토 친화 메뉴 개수
  totalMenuCount: Number,
  ketoMenuPercentage: Number, // 키토 메뉴 비율
  
  // 평점 및 리뷰
  rating: Number, // 전체 평점 0-5
  reviewCount: Number,
  totalRating: Number, // 평점 합계
  
  // 세부 평점
  ratings: {
    food: Number, // 음식 맛
    service: Number, // 서비스
    atmosphere: Number, // 분위기
    ketoFriendliness: Number // 키토 친화도
  },
  
  // 이미지 및 미디어
  images: [String], // 식당 이미지 URL들
  logoUrl: String,
  menuImageUrl: String, // 메뉴판 이미지
  
  // 편의시설
  amenities: [String], // ['주차가능', '배달', '포장', '카드결제', 'WiFi']
  
  // 상태
  isActive: Boolean, // 운영 중
  isVerified: Boolean, // 검증된 정보
  isPremium: Boolean, // 프리미엄 파트너
  
  // 통계
  viewCount: Number,
  favoriteCount: Number,
  orderCount: Number, // 주문 횟수 (배달 연동 시)
  
  // 파트너십
  partnershipLevel: String, // 'none', 'basic', 'premium'
  commissionRate: Number, // 수수료율
  
  createdAt: Date,
  updatedAt: Date
}
```

### 6. Reviews Collection
```javascript
{
  _id: ObjectId,
  userId: ObjectId, // reference to Users
  targetId: ObjectId, // recipe or restaurant ID
  targetType: String, // enum: ['recipe', 'restaurant']
  
  // 리뷰 내용
  rating: Number, // 전체 평점 1-5
  title: String, // 리뷰 제목
  comment: String, // 리뷰 내용
  
  // 세부 평점 (레시피용)
  recipeRatings: {
    taste: Number, // 맛
    difficulty: Number, // 난이도 정확성
    instruction: Number, // 설명 명확성
    ketoFriendliness: Number // 키토 친화도
  },
  
  // 세부 평점 (식당용)
  restaurantRatings: {
    food: Number, // 음식
    service: Number, // 서비스
    atmosphere: Number, // 분위기
    ketoOptions: Number // 키토 옵션
  },
  
  // 키토 관련 평가
  ketoExperience: {
    hadKetoOptions: Boolean, // 키토 옵션이 있었는지
    staffKnowledge: Number, // 직원 키토 지식 1-5
    modifications: [String], // 요청한 수정사항
    satisfaction: Number // 키토 식단 만족도 1-5
  },
  
  // 방문/요리 정보
  visitDate: Date, // 식당 방문일 또는 요리한 날
  orderDetails: [String], // 주문한 메뉴들
  totalCost: Number, // 총 비용 (식당의 경우)
  
  // 도움됨 투표
  helpfulCount: Number,
  notHelpfulCount: Number,
  helpfulVotes: [ObjectId], // 도움됨 투표한 사용자 ID들
  
  // 미디어
  images: [String], // 리뷰 이미지들
  
  // 답글 (식당 사장 등)
  replies: [{
    authorId: ObjectId,
    authorType: String, // 'owner', 'admin'
    content: String,
    createdAt: Date
  }],
  
  // 상태
  isVerified: Boolean, // 검증된 리뷰
  isHidden: Boolean,
  moderationStatus: String, // enum: ['pending', 'approved', 'rejected']
  reportCount: Number, // 신고 횟수
  
  // 리뷰어 정보 (익명화)
  reviewerInfo: {
    dietExperience: String, // 'beginner', 'experienced'
    dietDuration: Number, // 키토 다이어트 기간 (개월)
    ketoLevel: String // 'strict', 'moderate', 'lazy'
  },
  
  createdAt: Date,
  updatedAt: Date
}
```

### 7. SearchHistory Collection
```javascript
{
  _id: ObjectId,
  userId: ObjectId, // reference to Users, indexed
  sessionId: String, // 세션 ID
  
  // 검색 정보
  query: String, // indexed for analytics
  searchType: String, // enum: ['recipe', 'restaurant', 'general']
  
  // 사용된 필터들
  filters: {
    mealType: String,
    difficulty: String,
    cookingTime: Number,
    location: {
      lat: Number,
      lng: Number,
      radius: Number
    },
    priceRange: [Number],
    rating: Number,
    ketoScore: Number,
    category: String
  },
  
  // 검색 결과 정보
  resultCount: Number, // 검색 결과 개수
  clickedResults: [{
    itemId: ObjectId, // 클릭한 아이템 ID
    itemType: String, // 'recipe' or 'restaurant'
    position: Number, // 검색 결과에서의 위치
    clickedAt: Date
  }],
  
  // 검색 성공률 추적
  hasResults: Boolean,
  userSatisfaction: Number, // 1-5 (사용자가 평가한 검색 만족도)
  
  // 검색 개선을 위한 데이터
  searchIntent: String, // AI가 분석한 검색 의도
  suggestedQueries: [String], // 제안된 검색어들
  correctedQuery: String, // 맞춤법 교정된 검색어
  
  // 메타데이터
  searchedAt: Date,
  ipAddress: String,
  userAgent: String,
  platform: String, // 'web', 'mobile', 'app'
  
  // 개인화를 위한 데이터
  timeOfDay: String, // 'morning', 'afternoon', 'evening'
  dayOfWeek: String,
  location: {
    city: String,
    district: String
  }
}
```

### 8. AIRecommendations Collection
```javascript
{
  _id: ObjectId,
  userId: ObjectId, // reference to Users, indexed
  
  // 추천 요청 컨텍스트
  requestContext: {
    timeOfDay: String, // 'morning', 'afternoon', 'evening'
    dayOfWeek: String, // 'monday', 'tuesday', ...
    weather: {
      condition: String, // 'sunny', 'rainy', 'cold'
      temperature: Number // celsius
    },
    userMood: String, // 'energetic', 'tired', 'stressed', 'happy'
    location: {
      type: "Point",
      coordinates: [Number, Number]
    },
    
    // 최근 식사 이력
    recentMeals: [{
      recipeId: ObjectId,
      date: Date,
      mealType: String
    }],
    
    // 사용자 상태
    userPreferences: Object, // 현재 사용자 선호도
    dietProgress: {
      daysOnDiet: Number,
      completionRate: Number,
      currentWeight: Number
    },
    
    // 요청 유형
    requestType: String, // 'meal_planning', 'quick_recipe', 'restaurant_nearby'
    specificNeeds: [String] // ['quick', 'easy', 'budget', 'healthy']
  },
  
  // AI 모델 정보
  modelInfo: {
    version: String, // 'gpt-4', 'custom-v1.2'
    algorithm: String, // 'collaborative_filtering', 'content_based', 'hybrid'
    trainingData: String, // 훈련 데이터 버전
    confidence: Number, // 0-100 모델 신뢰도
    processingTime: Number // 처리 시간 (ms)
  },
  
  // 추천 결과
  recommendations: [{
    itemId: ObjectId, // recipe or restaurant ID
    itemType: String, // enum: ['recipe', 'restaurant']
    score: Number, // 추천 점수 0-100
    confidence: Number, // 이 추천에 대한 신뢰도
    reasoning: String, // 추천 이유
    category: String, // 'breakfast', 'quick', 'nearby', 'similar_taste'
    
    // 개인화 팩터
    personalizationFactors: {
      userPreferenceMatch: Number, // 0-100
      pastBehaviorMatch: Number, // 0-100
      contextualRelevance: Number, // 0-100
      popularityScore: Number, // 0-100
      noveltyScore: Number // 0-100 (새로운 시도 정도)
    }
  }],
  
  // 사용자 피드백
  userFeedback: {
    wasHelpful: Boolean,
    selectedItems: [ObjectId], // 실제 선택한 아이템들
    rating: Number, // 1-5 추천 만족도
    feedback: String, // 텍스트 피드백
    feedbackAt: Date
  },
  
  // A/B 테스트 정보
  abTestInfo: {
    variant: String, // 'control', 'variant_a', 'variant_b'
    testName: String,
    testId: String
  },
  
  // 성능 메트릭
  metrics: {
    clickThroughRate: Number, // 클릭률
    conversionRate: Number, // 실제 선택률
    engagementTime: Number, // 참여 시간 (초)
    bounceRate: Number // 이탈률
  },
  
  createdAt: Date,
  expiresAt: Date // TTL for cleanup (30 days)
}
```

### 9. Subscriptions Collection
```javascript
{
  _id: ObjectId,
  userId: ObjectId, // reference to Users, unique
  
  // 구독 기본 정보
  plan: String, // enum: ['free', 'premium']
  status: String, // enum: ['active', 'cancelled', 'expired', 'past_due', 'trial']
  billingCycle: String, // enum: ['monthly', 'yearly']
  
  // 결제 정보
  paymentProvider: String, // 'stripe', 'kakao', 'naver', 'iamport'
  stripeCustomerId: String,
  stripeSubscriptionId: String,
  paymentMethodId: String,
  
  // 금액 정보
  amount: Number, // 결제 금액 (원)
  currency: String, // 'KRW', 'USD'
  originalAmount: Number, // 할인 전 금액
  discountAmount: Number, // 할인 금액
  discountCode: String, // 할인 코드
  
  // 날짜 정보
  startDate: Date,
  currentPeriodStart: Date,
  currentPeriodEnd: Date,
  trialStart: Date, // 무료 체험 시작일
  trialEnd: Date, // 무료 체험 종료일
  cancelAt: Date, // 예약 취소일 (기간 종료 시 취소)
  canceledAt: Date, // 실제 취소일 (즉시 취소)
  
  // 프리미엄 기능 사용량 추적
  usage: {
    aiRecommendations: {
      used: Number, // 이번 주기에 사용한 횟수
      limit: Number // 주기별 제한
    },
    customMealPlans: {
      used: Number,
      limit: Number
    },
    restaurantReservations: {
      used: Number,
      limit: Number
    },
    premiumRecipes: {
      accessed: [ObjectId], // 접근한 프리미엄 레시피 ID들
      limit: Number
    }
  },
  
  // 구독 변경 이력
  planHistory: [{
    plan: String,
    startDate: Date,
    endDate: Date,
    reason: String // 'upgrade', 'downgrade', 'renewal'
  }],
  
  // 결제 이력
  paymentHistory: [{
    amount: Number,
    currency: String,
    paymentDate: Date,
    paymentMethod: String,
    transactionId: String,
    status: String, // 'success', 'failed', 'refunded'
    invoiceUrl: String
  }],
  
  // 자동 갱신 설정
  autoRenewal: Boolean,
  renewalNotificationSent: Boolean,
  
  // 취소 관련
  cancellationReason: String,
  cancellationFeedback: String,
  
  createdAt: Date,
  updatedAt: Date
}
```

### 10. ProgressTracking Collection
```javascript
{
  _id: ObjectId,
  userId: ObjectId, // reference to Users, indexed
  date: Date, // daily records, indexed
  
  // 체중 및 신체 정보
  bodyMetrics: {
    weight: Number, // kg
    bodyFatPercentage: Number,
    muscleMass: Number, // kg
    waistCircumference: Number, // cm
    bodyMassIndex: Number // BMI
  },
  
  // 식단 준수율
  nutrition: {
    // 계획된 영양소
    plannedCalories: Number,
    plannedCarbs: Number,
    plannedProtein: Number,
    plannedFat: Number,
    
    // 실제 섭취 영양소
    actualCalories: Number,
    actualCarbs: Number,
    actualProtein: Number,
    actualFat: Number,
    
    // 목표 달성률 (0-100)
    calorieAchievement: Number,
    carbAchievement: Number,
    proteinAchievement: Number,
    fatAchievement: Number,
    
    // 식사 완료 정보
    mealCompletionRate: Number, // 0-100
    mealsCompleted: Number,
    totalMealsPlanned: Number
  },
  
  // 활동 및 운동
  activity: {
    steps: Number,
    exerciseMinutes: Number,
    exerciseType: [String], // ['cardio', 'strength', 'yoga']
    caloriesBurned: Number,
    activeMinutes: Number
  },
  
  // 수분 섭취
  hydration: {
    waterIntake: Number, // ml
    targetWater: Number, // ml
    achievementRate: Number // 0-100
  },
  
  // 케토시스 관련 (키토 다이어트)
  ketosis: {
    ketoneLevels: Number, // mmol/L (혈중 케톤 수치)
    measurementTime: Date,
    measurementMethod: String, // 'blood', 'urine', 'breath'
    inKetosis: Boolean,
    ketosisStreak: Number // 연속 케토시스 일수
  },
  
  // 기분 및 웰빙
  wellness: {
    moodRating: Number, // 1-5 (1: very bad, 5: excellent)
    energyLevel: Number, // 1-5
    hungerLevel: Number, // 1-5 (1: not hungry, 5: very hungry)
    sleepQuality: Number, // 1-5
    sleepHours: Number, // 수면 시간
    stressLevel: Number, // 1-5
    
    // 증상 추적 (키토 플루 등)
    symptoms: [String], // ['headache', 'fatigue', 'nausea', 'irritability']
    cravings: [String] // ['sweet', 'salty', 'carbs']
  },
  
  // 목표 달성 현황
  goalProgress: {
    weightLossProgress: Number, // kg (목표 대비)
    weightLossPercentage: Number, // 0-100
    streakDays: Number, // 연속 성공 일수
    weeklyAverage: {
      calories: Number,
      carbs: Number,
      completionRate: Number
    }
  },
  
  // 일일 메모 및 반성
  dailyReflection: {
    notes: String, // 일반 메모
    wins: [String], // 오늘의 성공
    challenges: [String], // 오늘의 어려움
    improvements: [String], // 개선할 점
    gratitude: String, // 감사한 일
    tomorrowGoals: [String] // 내일의 목표
  },
  
  // 약물/보충제 (선택사항)
  supplements: [{
    name: String,
    dosage: String,
    timing: String, // 'morning', 'evening'
    taken: Boolean
  }],
  
  // 데이터 출처
  dataSource: {
    weightSource: String, // 'manual', 'smart_scale', 'app'
    activitySource: String, // 'manual', 'fitbit', 'apple_health'
    nutritionSource: String // 'manual', 'app_tracking'
  },
  
  createdAt: Date
}
```

---

## 🔑 인덱스 설정

### MongoDB 인덱스
```javascript
// Users Collection
db.users.createIndex({ email: 1 }, { unique: true })
db.users.createIndex({ googleId: 1 }, { sparse: true })
db.users.createIndex({ "subscription.isActive": 1 })
db.users.createIndex({ lastLoginAt: -1 })

// Recipes Collection
db.recipes.createIndex({ 
  title: "text", 
  description: "text", 
  tags: "text",
  "ingredients.name": "text"
})
db.recipes.createIndex({ isKetoFriendly: 1, rating: -1 })
db.recipes.createIndex({ tags: 1 })
db.recipes.createIndex({ difficulty: 1, cookingTime: 1 })
db.recipes.createIndex({ category: 1, mealTypes: 1 })
db.recipes.createIndex({ status: 1, isPublic: 1 })
db.recipes.createIndex({ ketoScore: -1 })
db.recipes.createIndex({ slug: 1 }, { unique: true })
db.recipes.createIndex({ createdAt: -1 })

// MealPlans Collection
db.mealPlans.createIndex({ userId: 1, date: 1 }, { unique: true })
db.mealPlans.createIndex({ userId: 1, weekNumber: 1 })
db.mealPlans.createIndex({ date: 1 })
db.mealPlans.createIndex({ userId: 1, createdAt: -1 })

// UserFavorites Collection
db.userFavorites.createIndex({ userId: 1, recipeId: 1 }, { unique: true })
db.userFavorites.createIndex({ userId: 1, addedAt: -1 })
db.userFavorites.createIndex({ userId: 1, category: 1 })

// Restaurants Collection
db.restaurants.createIndex({ location: "2dsphere" })
db.restaurants.createIndex({ 
  name: "text", 
  description: "text",
  category: "text"
})
db.restaurants.createIndex({ category: 1, ketoScore: -1 })
db.restaurants.createIndex({ "address.city": 1, "address.district": 1 })
db.restaurants.createIndex({ isActive: 1, isVerified: 1 })
db.restaurants.createIndex({ rating: -1 })

// Reviews Collection
db.reviews.createIndex({ targetId: 1, targetType: 1 })
db.reviews.createIndex({ userId: 1, createdAt: -1 })
db.reviews.createIndex({ targetId: 1, rating: -1 })
db.reviews.createIndex({ moderationStatus: 1 })

// SearchHistory Collection
db.searchHistory.createIndex({ userId: 1, searchedAt: -1 })
db.searchHistory.createIndex({ query: "text" })
db.searchHistory.createIndex({ searchType: 1, searchedAt: -1 })
db.searchHistory.createIndex({ sessionId: 1 })

// AIRecommendations Collection
db.aiRecommendations.createIndex({ userId: 1, createdAt: -1 })
db.aiRecommendations.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 })
db.aiRecommendations.createIndex({ "modelInfo.version": 1 })

// Subscriptions Collection
db.subscriptions.createIndex({ userId: 1 }, { unique: true })
db.subscriptions.createIndex({ status: 1, currentPeriodEnd: 1 })
db.subscriptions.createIndex({ stripeCustomerId: 1 })

// ProgressTracking Collection
db.progressTracking.createIndex({ userId: 1, date: 1 }, { unique: true })
db.progressTracking.createIndex({ userId: 1, date: -1 })
db.progressTracking.createIndex({ date: 1 })
```

---

## 🌐 API 엔드포인트

### 인증 관련
```
POST   /api/auth/register          # 회원가입
POST   /api/auth/login             # 로그인
POST   /api/auth/logout            # 로그아웃
POST   /api/auth/refresh           # 토큰 갱신
POST   /api/auth/google            # Google OAuth
POST   /api/auth/forgot-password   # 비밀번호 찾기
POST   /api/auth/reset-password    # 비밀번호 재설정
GET    /api/auth/verify-email      # 이메일 인증
```

### 사용자 관리
```
GET    /api/users/me               # 내 정보 조회
PUT    /api/users/me               # 내 정보 수정
PUT    /api/users/me/preferences   # 선호도 설정
PUT    /api/users/me/settings      # 앱 설정
DELETE /api/users/me               # 회원 탈퇴
POST   /api/users/me/upload-avatar # 프로필 이미지 업로드
```

### 레시피 관련
```
GET    /api/recipes                # 레시피 목록 조회 (필터링, 페이징)
GET    /api/recipes/search         # 레시피 검색 (RAG + 하이브리드)
GET    /api/recipes/featured       # 추천 레시피
GET    /api/recipes/popular        # 인기 레시피
GET    /api/recipes/:id            # 레시피 상세 조회
POST   /api/recipes                # 레시피 생성 (관리자)
PUT    /api/recipes/:id            # 레시피 수정
DELETE /api/recipes/:id            # 레시피 삭제
POST   /api/recipes/:id/like       # 레시피 좋아요
DELETE /api/recipes/:id/like       # 레시피 좋아요 취소
```

### 즐겨찾기
```
GET    /api/favorites              # 즐겨찾기 목록
POST   /api/favorites              # 즐겨찾기 추가
DELETE /api/favorites/:recipeId    # 즐겨찾기 제거
PUT    /api/favorites/:recipeId    # 즐겨찾기 메모 수정
```

### 식단 계획
```
GET    /api/meal-plans             # 식단 계획 조회 (날짜별)
POST   /api/meal-plans             # 식단 계획 생성
PUT    /api/meal-plans/:date       # 식단 계획 수정
DELETE /api/meal-plans/:date       # 식단 계획 삭제
POST   /api/meal-plans/random      # 랜덤 식단 생성
POST   /api/meal-plans/complete    # 식사 완료 처리
GET    /api/meal-plans/week        # 주간 식단 조회
```

### 식당 관련
```
GET    /api/restaurants            # 식당 목록 (위치 기반)
GET    /api/restaurants/search     # 식당 검색
GET    /api/restaurants/nearby     # 주변 식당
GET    /api/restaurants/:id        # 식당 상세 정보
GET    /api/restaurants/:id/menu   # 식당 메뉴
POST   /api/restaurants/:id/review # 리뷰 작성
```

### 리뷰 시스템
```
GET    /api/reviews                # 리뷰 목록 (타겟별)
POST   /api/reviews                # 리뷰 작성
PUT    /api/reviews/:id            # 리뷰 수정
DELETE /api/reviews/:id            # 리뷰 삭제
POST   /api/reviews/:id/helpful    # 도움됨 투표
```

### AI 추천
```
POST   /api/recommendations/recipes    # 레시피 개인 맞춤 추천
POST   /api/recommendations/restaurants # 식당 추천
POST   /api/recommendations/meal-plan  # 식단 계획 추천
POST   /api/recommendations/feedback   # 추천 피드백
```

### 구독 및 결제
```
GET    /api/subscriptions          # 구독 정보 조회
POST   /api/subscriptions          # 구독 시작
PUT    /api/subscriptions          # 구독 변경
DELETE /api/subscriptions          # 구독 취소
POST   /api/payments/webhooks      # 결제 웹훅 처리
```

### 진행률 추적
```
GET    /api/progress               # 진행률 조회
POST   /api/progress               # 일일 기록 추가
PUT    /api/progress/:date         # 일일 기록 수정
GET    /api/progress/stats         # 통계 조회
GET    /api/progress/charts        # 차트 데이터
```

### 검색 및 분석
```
GET    /api/search/suggestions     # 검색어 자동완성
POST   /api/search/history         # 검색 기록 저장
GET    /api/analytics/dashboard    # 관리자 대시보드
GET    /api/analytics/users        # 사용자 분석
GET    /api/analytics/recipes      # 레시피 분석
```

---

## 📊 데이터 관계도

```
Users
├── MealPlans (1:N)
├── UserFavorites (1:N)
├── Reviews (1:N)
├── SearchHistory (1:N)
├── AIRecommendations (1:N)
├── Subscriptions (1:1)
└── ProgressTracking (1:N)

Recipes
├── UserFavorites (1:N)
├── Reviews (1:N)
├── MealPlans.meals (1:N)
└── AIRecommendations (1:N)

Restaurants
├── Reviews (1:N)
└── AIRecommendations (1:N)

MealPlans
├── Users (N:1)
└── Recipes (N:M through meals)

Reviews
├── Users (N:1)
├── Recipes (N:1)
└── Restaurants (N:1)
```

## 🔧 기술 스택 권장사항

### 백엔드
- **Framework**: Node.js + Express.js / Python + FastAPI
- **Database**: MongoDB (Primary) + Redis (Cache)
- **Authentication**: JWT + OAuth 2.0
- **File Storage**: AWS S3 / Google Cloud Storage
- **Search**: Elasticsearch + OpenAI Embeddings
- **Payments**: Stripe / 아임포트
- **Monitoring**: Winston + Sentry

### AI/ML
- **LLM**: OpenAI GPT-4 / Claude
- **Vector DB**: Pinecone / Weaviate
- **Recommendations**: TensorFlow / PyTorch
- **Search**: Hybrid Search (Keyword + Semantic)

이 스키마와 API 설계를 바탕으로 KetoHelper의 백엔드를 완벽하게 구현할 수 있습니다! 🚀
