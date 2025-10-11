import { create } from 'zustand'

export interface OptimisticMealData {
  id: string
  date: string
  slot: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  title: string
  type: 'optimistic'
  timestamp: number
}

interface CalendarSaveState {
  // 저장 완료 상태
  lastSaveTimestamp: number | null
  lastSaveData: {
    durationDays: number
    validMealCount: number
    startDate: string
  } | null
  
  // 전역 캘린더 로딩 상태
  isCalendarLoading: boolean
  
  // Optimistic Update 상태
  isSaving: boolean
  optimisticMeals: OptimisticMealData[]
  
  // 전역 캘린더 로딩 상태 설정
  setCalendarLoading: (loading: boolean) => void
  
  // 저장 완료 플래그 설정
  setSaveCompleted: (data: {
    durationDays: number
    validMealCount: number
    startDate: string
  }) => void
  
  // Optimistic 데이터 추가
  addOptimisticMeals: (meals: Omit<OptimisticMealData, 'id' | 'timestamp'>[]) => void
  
  // Optimistic 데이터 제거
  removeOptimisticMeals: (mealIds: string[]) => void
  
  // 저장 상태 초기화
  clearSaveState: () => void
  
  // 최근 저장 여부 확인 (5분 이내)
  isRecentSave: () => boolean
}

export const useCalendarStore = create<CalendarSaveState>((set, get) => ({
  lastSaveTimestamp: null,
  lastSaveData: null,
  isCalendarLoading: false,
  isSaving: false,
  optimisticMeals: [],
  
  setCalendarLoading: (loading) => {
    console.log(`🔄 전역 캘린더 로딩 상태 변경: ${loading}`)
    set({ isCalendarLoading: loading })
  },
  
  setSaveCompleted: (data) => {
    set({
      lastSaveTimestamp: Date.now(),
      lastSaveData: data,
      isSaving: false,
      isCalendarLoading: false
    })
  },
  
  addOptimisticMeals: (meals) => {
    console.log(`🔍 addOptimisticMeals 호출: ${meals.length}개 식단`)
    const optimisticMeals = meals.map(meal => ({
      ...meal,
      id: `optimistic-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now()
    }))
    
    console.log(`🔍 생성된 Optimistic 데이터:`, optimisticMeals)
    
    set(state => {
      const newState = {
        isSaving: true,
        optimisticMeals: [...state.optimisticMeals, ...optimisticMeals]
      }
      console.log(`🔍 CalendarStore 상태 업데이트:`, newState)
      return newState
    })
  },
  
  removeOptimisticMeals: (mealIds) => {
    set(state => ({
      optimisticMeals: state.optimisticMeals.filter(meal => !mealIds.includes(meal.id))
    }))
  },
  
  clearSaveState: () => {
    set({
      lastSaveTimestamp: null,
      lastSaveData: null,
      isSaving: false,
      isCalendarLoading: false,
      optimisticMeals: []
    })
  },
  
  isRecentSave: () => {
    const { lastSaveTimestamp } = get()
    if (!lastSaveTimestamp) return false
    
    const timeDiff = Date.now() - lastSaveTimestamp
    return timeDiff < 5 * 60 * 1000 // 5분 이내
  }
}))
