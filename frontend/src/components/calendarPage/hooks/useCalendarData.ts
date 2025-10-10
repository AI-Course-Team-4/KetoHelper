import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { MealData, generateRandomMeal } from '@/data/ketoMeals'
import { usePlansRange } from '@/hooks/useApi'
import { useAuthStore } from '@/store/authStore'

export function useCalendarData(currentMonth: Date) {
  const [mealData, setMealData] = useState<Record<string, MealData>>({})
  const [planIds, setPlanIds] = useState<Record<string, Record<string, string>>>({})
  const [mealCheckState, setMealCheckState] = useState<Record<string, {
    breakfastCompleted?: boolean
    lunchCompleted?: boolean
    dinnerCompleted?: boolean
    snackCompleted?: boolean
  }>>({})

  const { user } = useAuthStore()

  // 현재 월의 시작일과 종료일 계산
  const startOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1)
  const endOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0)

  // API로 실제 데이터 가져오기
  const { data: plansData, isLoading, error } = usePlansRange(
    format(startOfMonth, 'yyyy-MM-dd'),
    format(endOfMonth, 'yyyy-MM-dd'),
    user?.id || ''
  )

  // 날짜 문자열로 변환하는 헬퍼 함수
  const formatDateKey = (date: Date) => {
    try {
      if (!date || isNaN(date.getTime())) {
        console.warn('⚠️ 유효하지 않은 날짜:', date)
        return format(new Date(), 'yyyy-MM-dd')
      }
      return format(date, 'yyyy-MM-dd')
    } catch (error) {
      console.error('❌ 날짜 포맷 변환 오류:', error, date)
      return format(new Date(), 'yyyy-MM-dd')
    }
  }

  // 특정 날짜의 식단 정보 가져오기
  const getMealForDate = (date: Date) => {
    try {
      const dateKey = formatDateKey(date)
      return mealData[dateKey] || null
    } catch (error) {
      console.error('❌ 식단 정보 조회 오류:', error, date)
      return null
    }
  }

  // 샘플 데이터 생성 (UI 테스트용)
  const loadSampleMealData = (month: Date) => {
    console.log('🎨 샘플 데이터 로드 (UI 테스트용)')

    const sampleData: Record<string, MealData> = {}

    // 현재 월의 몇 개 날짜에 샘플 식단 추가
    for (let day = 1; day <= 10; day++) {
      const sampleDate = new Date(month.getFullYear(), month.getMonth(), day)
      const dateKey = formatDateKey(sampleDate)

      sampleData[dateKey] = generateRandomMeal()
    }

    setMealData(sampleData)
    console.log('✅ 샘플 데이터 로드 완료')
  }

  // API 데이터를 캘린더 형식으로 변환
  useEffect(() => {
    if (plansData && user?.id) {
      const convertedData: Record<string, MealData> = {}
      const convertedPlanIds: Record<string, Record<string, string>> = {}

      plansData.forEach((plan: any) => {
        // 날짜 유효성 검사
        if (!plan.date || !plan.id || !plan.slot) {
          console.warn('⚠️ 유효하지 않은 plan 데이터:', plan)
          return
        }

        try {
          const planDate = new Date(plan.date)
          if (isNaN(planDate.getTime())) {
            console.warn('⚠️ 유효하지 않은 날짜:', plan.date)
            return
          }

          const dateKey = formatDateKey(planDate)

          if (!convertedData[dateKey]) {
            convertedData[dateKey] = {
              breakfast: '',
              lunch: '',
              dinner: '',
              snack: ''
            }
          }

          if (!convertedPlanIds[dateKey]) {
            convertedPlanIds[dateKey] = {}
          }
          // 슬롯에 맞는 식단 데이터 설정
          if (plan.slot === 'breakfast') {
            convertedData[dateKey].breakfast = plan.title || plan.notes || ''
            convertedData[dateKey].breakfastUrl = plan.url  // ✅ URL 추가
            convertedData[dateKey].breakfastCompleted = plan.status === 'done'
            convertedPlanIds[dateKey].breakfast = plan.id
          } else if (plan.slot === 'lunch') {
            convertedData[dateKey].lunch = plan.title || plan.notes || ''
            convertedData[dateKey].lunchUrl = plan.url  // ✅ URL 추가
            convertedData[dateKey].lunchCompleted = plan.status === 'done'
            convertedPlanIds[dateKey].lunch = plan.id
          } else if (plan.slot === 'dinner') {
            convertedData[dateKey].dinner = plan.title || plan.notes || ''
            convertedData[dateKey].dinnerUrl = plan.url  // ✅ URL 추가
            convertedData[dateKey].dinnerCompleted = plan.status === 'done'
            convertedPlanIds[dateKey].dinner = plan.id
          } else if (plan.slot === 'snack') {
            convertedData[dateKey].snack = plan.title || plan.notes || ''
            convertedData[dateKey].snackUrl = plan.url  // ✅ URL 추가
            convertedData[dateKey].snackCompleted = plan.status === 'done'
            convertedPlanIds[dateKey].snack = plan.id
          } else {
            console.warn('⚠️ 알 수 없는 slot 타입:', plan.slot)
          }
        } catch (error) {
          console.error('❌ 날짜 변환 오류:', error, plan)
          return
        }
      })

      setMealData(convertedData)
      setPlanIds(convertedPlanIds)
    } else if (!user?.id) {
      // 사용자가 로그인하지 않은 경우 샘플 데이터 사용
      console.log('👤 비로그인 사용자 - 샘플 데이터 로드')
      loadSampleMealData(currentMonth)
    } else if (user?.id && !isLoading && !plansData) {
      // 로그인했지만 데이터가 없는 경우
      console.log('📭 로그인 사용자이지만 식단 데이터 없음')
      setMealData({})
    }
  }, [plansData, user?.id, currentMonth, isLoading])

  // 간단한 체크 토글 함수 (로컬 UI만)
  const toggleMealCheck = (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => {
    try {
      const dateKey = formatDateKey(date)

      setMealCheckState(prev => {
        const currentState = prev[dateKey] || {}
        const newState = { ...currentState }

        if (mealType === 'breakfast') newState.breakfastCompleted = !currentState.breakfastCompleted
        else if (mealType === 'lunch') newState.lunchCompleted = !currentState.lunchCompleted
        else if (mealType === 'dinner') newState.dinnerCompleted = !currentState.dinnerCompleted
        else if (mealType === 'snack') newState.snackCompleted = !currentState.snackCompleted

        return {
          ...prev,
          [dateKey]: newState
        }
      })

      console.log(`✅ ${mealType} 체크 토글 (로컬 UI)`)
    } catch (error) {
      console.error('❌ 식단 체크 토글 오류:', error, date, mealType)
    }
  }

  // 체크 상태 확인 함수
  const isMealChecked = (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => {
    try {
      const dateKey = formatDateKey(date)
      const checkState = mealCheckState[dateKey]

      if (!checkState) return false

      if (mealType === 'breakfast') return checkState.breakfastCompleted || false
      else if (mealType === 'lunch') return checkState.lunchCompleted || false
      else if (mealType === 'dinner') return checkState.dinnerCompleted || false
      else if (mealType === 'snack') return checkState.snackCompleted || false

      return false
    } catch (error) {
      console.error('❌ 식단 체크 상태 확인 오류:', error, date, mealType)
      return false
    }
  }

  return {
    mealData,
    planIds,
    mealCheckState,
    isLoading,
    error,
    formatDateKey,
    getMealForDate,
    toggleMealCheck,
    isMealChecked
  }
}
