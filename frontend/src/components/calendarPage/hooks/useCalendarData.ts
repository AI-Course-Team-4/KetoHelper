import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { MealData, generateRandomMeal } from '@/data/ketoMeals'
import { usePlansRange } from '@/hooks/useApi'
import { useAuthStore } from '@/store/authStore'
import { useCalendarStore } from '@/store/calendarStore'

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
  const { isRecentSave, clearSaveState, optimisticMeals, isSaving } = useCalendarStore()
  
  // Optimistic 데이터 변화 감지 디버깅
  useEffect(() => {
    console.log(`🔍 useCalendarData - optimisticMeals 변화 감지: ${optimisticMeals.length}개`)
    if (optimisticMeals.length > 0) {
      console.log(`🔍 Optimistic 데이터 상세:`, optimisticMeals)
    }
  }, [optimisticMeals])

  // 현재 월의 시작일과 종료일 계산
  const startOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1)
  const endOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0)

  // API로 실제 데이터 가져오기
  const { data: plansData, isLoading, error, refetch } = usePlansRange(
    format(startOfMonth, 'yyyy-MM-dd'),
    format(endOfMonth, 'yyyy-MM-dd'),
    user?.id || ''
  )
  
  // 전역 캘린더 로딩 상태 가져오기
  const { isCalendarLoading } = useCalendarStore()
  
  // 전체 로딩 상태 (API 로딩 또는 전역 캘린더 로딩)
  const isAnyLoading = isLoading || isCalendarLoading
  // 초기 진입 시 데이터가 아직 없을 때도 로딩을 보장
  const isInitialLoading = !!(user?.id) && !plansData && Object.keys(mealData).length === 0
  
  // 디버깅: 로딩 상태 변화 추적
  useEffect(() => {
    console.log('🔍 useCalendarData 로딩 상태 변화:', {
      isLoading,
      isCalendarLoading,
      isAnyLoading,
      timestamp: new Date().toISOString()
    })
  }, [isLoading, isCalendarLoading, isAnyLoading])
  
  // 데이터가 도착하면 전역 로딩 해제 (워치독)
  useEffect(() => {
    const { setCalendarLoading } = useCalendarStore.getState()
    if (plansData && Array.isArray(plansData)) {
      console.log('✅ plansData 수신 → 전역 캘린더 로딩 해제')
      setCalendarLoading(false)
    }
  }, [plansData])
  
  // Optimistic 데이터가 존재하면 전역 로딩 해제 (백엔드 지연 대비)
  useEffect(() => {
    const { setCalendarLoading } = useCalendarStore.getState()
    if (isCalendarLoading && optimisticMeals.length > 0) {
      console.log('✅ Optimistic 데이터 존재 → 전역 캘린더 로딩 해제')
      setCalendarLoading(false)
    }
  }, [optimisticMeals, isCalendarLoading])
  
  // 최대 10초 워치독 타이머: 로딩이 오래 지속되면 자동 해제
  useEffect(() => {
    if (!isCalendarLoading) return
    const { setCalendarLoading } = useCalendarStore.getState()
    const timer = setTimeout(() => {
      console.log('⏱️ 로딩 워치독 타임아웃(10s) → 전역 캘린더 로딩 강제 해제')
      setCalendarLoading(false)
    }, 10000)
    return () => clearTimeout(timer)
  }, [isCalendarLoading])

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

  // 페이지 포커스 시 데이터 새로고침
  useEffect(() => {
    const handleFocus = () => {
      console.log('🔄 페이지 포커스 - 캘린더 데이터 새로고침')
      refetch()
    }

    // 캘린더 저장 완료 이벤트 리스너
    const handleCalendarSave = () => {
      console.log('🎉 캘린더 저장 완료 이벤트 수신 - 데이터 새로고침')
      refetch()
    }

    window.addEventListener('focus', handleFocus)
    window.addEventListener('calendar-saved', handleCalendarSave)
    
    return () => {
      window.removeEventListener('focus', handleFocus)
      window.removeEventListener('calendar-saved', handleCalendarSave)
    }
  }, [refetch])

  // 전역 상태 기반 저장 완료 감지
  useEffect(() => {
    if (isRecentSave()) {
      console.log('🔄 전역 상태에서 최근 저장 감지 - 데이터 새로고침')
      refetch()
      // 상태 초기화
      clearSaveState()
    }
  }, [isRecentSave, refetch, clearSaveState])

  // API 데이터를 캘린더 형식으로 변환
  useEffect(() => {
    if (plansData && user?.id) {
      console.log('📅 API에서 식단 데이터 로드:', plansData)
      console.log('📅 plansData 타입:', typeof plansData, '길이:', Array.isArray(plansData) ? plansData.length : 'N/A')

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
            convertedData[dateKey].breakfastCompleted = plan.status === 'done'
            convertedPlanIds[dateKey].breakfast = plan.id
          } else if (plan.slot === 'lunch') {
            convertedData[dateKey].lunch = plan.title || plan.notes || ''
            convertedData[dateKey].lunchCompleted = plan.status === 'done'
            convertedPlanIds[dateKey].lunch = plan.id
          } else if (plan.slot === 'dinner') {
            convertedData[dateKey].dinner = plan.title || plan.notes || ''
            convertedData[dateKey].dinnerCompleted = plan.status === 'done'
            convertedPlanIds[dateKey].dinner = plan.id
          } else if (plan.slot === 'snack') {
            convertedData[dateKey].snack = plan.title || plan.notes || ''
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

      // 🚀 Optimistic 데이터 병합 (API 데이터가 없는 경우에만)
      console.log(`🔍 Optimistic 데이터 병합 시작: ${optimisticMeals.length}개`)
      optimisticMeals.forEach(optimisticMeal => {
        const dateKey = formatDateKey(new Date(optimisticMeal.date))
        console.log(`🔍 Optimistic 데이터 처리: ${dateKey} ${optimisticMeal.slot} - ${optimisticMeal.title}`)
        
        if (!convertedData[dateKey]) {
          convertedData[dateKey] = {
            breakfast: '',
            lunch: '',
            dinner: '',
            snack: ''
          }
          console.log(`🔍 새 날짜 데이터 생성: ${dateKey}`)
        }
        
        // 해당 슬롯에 API 데이터가 없을 때만 Optimistic 데이터 사용
        if (!convertedData[dateKey][optimisticMeal.slot]) {
          convertedData[dateKey][optimisticMeal.slot] = optimisticMeal.title
          console.log(`🚀 Optimistic 데이터 추가: ${dateKey} ${optimisticMeal.slot} - ${optimisticMeal.title}`)
        } else {
          console.log(`⚠️ API 데이터가 이미 존재하여 Optimistic 데이터 건너뜀: ${dateKey} ${optimisticMeal.slot}`)
        }
      })

      setMealData(convertedData)
      setPlanIds(convertedPlanIds)
      console.log('✅ API + Optimistic 데이터 변환 완료:', convertedData)
      console.log('✅ Plan IDs 저장 완료:', convertedPlanIds)
      console.log('✅ 변환된 식단 데이터 키들:', Object.keys(convertedData))

      // ✅ 실제 데이터가 로드된 슬롯 기준으로 Optimistic 데이터 정리 (타임존/키 불일치 방지)
      try {
        const { useCalendarStore } = require('@/store/calendarStore')
        const state = useCalendarStore.getState()
        if (state.optimisticMeals.length > 0) {
          const removeIds = state.optimisticMeals
            .filter((m: any) => {
              const key = formatDateKey(new Date(m.date))
              const day = (convertedData as any)[key]
              if (!day) return false
              const slot = m.slot as 'breakfast' | 'lunch' | 'dinner' | 'snack'
              const title = day?.[slot]
              return !!(title && String(title).trim())
            })
            .map((m: any) => m.id)
          if (removeIds.length > 0) {
            state.removeOptimisticMeals(removeIds)
            console.log(`🧹 로드된 날짜의 Optimistic 정리: ${removeIds.length}건`)
          }
        }
      } catch {}
    } else if (!user?.id) {
      // 사용자가 로그인하지 않은 경우 샘플 데이터 사용
      console.log('👤 비로그인 사용자 - 샘플 데이터 로드')
      loadSampleMealData(currentMonth)
    } else if (user?.id && !isAnyLoading && (!plansData || plansData.length === 0)) {
      // 로그인했지만 데이터가 없는 경우
      console.log('📭 로그인 사용자이지만 식단 데이터 없음')
      setMealData({})
      
      // Optimistic 데이터가 있다면 표시
      if (optimisticMeals.length > 0) {
        console.log(`🔍 데이터 없지만 Optimistic 데이터 ${optimisticMeals.length}개 있음 - 표시`)
        const convertedData: Record<string, MealData> = {}
        
        optimisticMeals.forEach(optimisticMeal => {
          const dateKey = formatDateKey(new Date(optimisticMeal.date))
          
          if (!convertedData[dateKey]) {
            convertedData[dateKey] = {
              breakfast: '',
              lunch: '',
              dinner: '',
              snack: ''
            }
          }
          
          convertedData[dateKey][optimisticMeal.slot] = optimisticMeal.title
        })
        
        setMealData(convertedData)
        console.log('🚀 Optimistic 데이터만으로 캘린더 표시:', convertedData)
      }
    }
  }, [plansData, user?.id, currentMonth, isAnyLoading, optimisticMeals])

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

  // Optimistic 데이터인지 확인하는 함수
  const isOptimisticMeal = (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => {
    try {
      const dateKey = formatDateKey(date)
      const optimisticMeal = optimisticMeals.find(meal => 
        meal.date === dateKey && meal.slot === mealType
      )
      return !!optimisticMeal
    } catch (error) {
      console.error('❌ Optimistic 데이터 확인 오류:', error, date, mealType)
      return false
    }
  }

  return {
    mealData,
    planIds,
    mealCheckState,
    isLoading: isAnyLoading || isInitialLoading, // UI 로딩 보장
    error,
    isSaving,
    formatDateKey,
    getMealForDate,
    toggleMealCheck,
    isMealChecked,
    isOptimisticMeal
  }
}
