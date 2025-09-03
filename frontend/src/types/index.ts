// 사용자 관련 타입
export interface User {
  id: string
  email: string
  name: string
  profileImage?: string
  createdAt: string
  updatedAt: string
  preferences: UserPreferences
  settings: UserSettings
  subscription: SubscriptionInfo
  dietPlan?: DietPlan
}

export interface UserPreferences {
  allergies: string[]
  dislikes: string[]
  dietaryRestrictions: string[]
  experienceLevel: 'beginner' | 'intermediate' | 'advanced'
  goals: UserGoals
}

export interface UserGoals {
  targetWeight?: number
  targetCalories: number
  macroRatio: MacroRatio
}

export interface MacroRatio {
  carbs: number
  protein: number
  fat: number
}

export interface UserSettings {
  notifications: NotificationSettings
  units: 'metric' | 'imperial'
}

export interface NotificationSettings {
  mealReminders: boolean
  recommendations: boolean
  weeklyReport: boolean
}

// 레시피 관련 타입
export interface Recipe {
  id: string
  title: string
  description: string
  imageUrl: string
  cookingTime: number // minutes
  difficulty: '쉬움' | '중간' | '어려움'
  servings: number
  ingredients: Ingredient[]
  instructions: string[]
  nutrition: NutritionInfo
  tags: string[]
  rating: number
  reviewCount: number
  isKetoFriendly: boolean
  createdAt: string
}

export interface Ingredient {
  name: string
  amount: number
  unit: string
  carbs: number // per serving
}

export interface NutritionInfo {
  calories: number
  carbs: number
  protein: number
  fat: number
  fiber: number
}

// 식당 관련 타입
export interface Restaurant {
  id: string
  name: string
  address: string
  location: {
    type: 'Point'
    coordinates: [number, number] // [longitude, latitude]
  }
  phone: string
  category: string
  priceRange: 1 | 2 | 3 | 4
  rating: number
  reviewCount: number
  operatingHours: OperatingHour[]
  menu: MenuItem[]
  ketoScore: number // 0-100
  images: string[]
  createdAt: string
  distance?: number // km (computed field)
}

export interface OperatingHour {
  day: string
  open: string
  close: string
}

export interface MenuItem {
  name: string
  description: string
  price: number
  carbs: number
  isKetoFriendly: boolean
  ketoModifications: string[]
}

// API 응답 타입
export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 검색 및 필터 타입
export interface RecipeFilters {
  mealType?: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  cookingTime?: number
  difficulty?: 'easy' | 'medium' | 'hard'
  ingredients?: string[]
  calorieRange?: [number, number]
  excludeAllergies?: boolean
}

export interface RestaurantFilters {
  location?: {
    lat: number
    lng: number
    radius: number // km
  }
  category?: string
  priceRange?: number[]
  rating?: number
  ketoScore?: number
}

// AI 추천 관련 타입
export interface RecommendationRequest {
  userId?: string
  preferences?: Partial<UserPreferences>
  filters?: RecipeFilters | RestaurantFilters
  context?: string
}

export interface RecommendationResponse {
  recommendations: Recipe[] | Restaurant[]
  reasoning: string
  confidence: number
}

// 인증 관련 타입
export interface LoginCredentials {
  email: string
  password: string
}

export interface GoogleAuthResponse {
  accessToken: string
  refreshToken: string
  user: User
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

// 구독 관련 타입
export interface SubscriptionInfo {
  isActive: boolean
  plan: 'free' | 'premium'
  startDate?: string
  endDate?: string
  autoRenewal: boolean
}

// 다이어트 계획 타입
export interface DietPlan {
  currentWeight: number
  targetWeight: number
  intensity: 'low' | 'medium' | 'high'
  startDate: string
  estimatedEndDate: string
  daysRemaining: number
  dailyCalories: number
  macroTargets: MacroRatio
}

// 캘린더 관련 타입
export interface MealPlan {
  id: string
  date: string
  meals: {
    breakfast?: Recipe
    lunch?: Recipe
    dinner?: Recipe
  }
  completed: {
    breakfast: boolean
    lunch: boolean
    dinner: boolean
  }
  totalNutrition: NutritionInfo
}

export interface CalendarEvent {
  date: string
  mealPlan: MealPlan
  isCompleted: boolean
  completionRate: number
}

// 결제 관련 타입
export interface PaymentInfo {
  plan: 'premium'
  amount: number
  currency: string
  billingCycle: 'monthly' | 'yearly'
  paymentMethod: 'card' | 'kakao' | 'naver'
}

export interface PaymentRequest {
  planId: string
  paymentMethod: string
  billingCycle: 'monthly' | 'yearly'
}

// 진행률 추적 타입
export interface ProgressStats {
  streakDays: number
  totalDaysOnPlan: number
  completionRate: number
  weightProgress: number
  daysUntilGoal: number
}

// 에러 타입
export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
}

// 폼 관련 타입
export interface ContactForm {
  name: string
  email: string
  message: string
}

export interface FeedbackForm {
  rating: number
  comment: string
  category: 'recipe' | 'restaurant' | 'app'
  targetId?: string
}

export interface InitialDietSetup {
  currentWeight: number
  targetWeight: number
  intensity: 'low' | 'medium' | 'high'
  timeframe: number // 주 단위
  activityLevel: 'sedentary' | 'light' | 'moderate' | 'active'
}
