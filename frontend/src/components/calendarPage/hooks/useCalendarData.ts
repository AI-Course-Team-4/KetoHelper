import { useState, useEffect, useMemo } from 'react'
import { format } from 'date-fns'
import { useQueryClient } from '@tanstack/react-query'
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
  
  // 이전 데이터와 비교하기 위한 상태
  const [previousPlansData, setPreviousPlansData] = useState<any[] | null>(null)

  const { user } = useAuthStore()
  const { isRecentSave, clearSaveState, optimisticMeals, isSaving } = useCalendarStore()
  

  // 현재 월의 시작일과 종료일 계산
  const startOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1)
  const endOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0)

  // API로 실제 데이터 가져오기
  const startDate = format(startOfMonth, 'yyyy-MM-dd')
  const endDate = format(endOfMonth, 'yyyy-MM-dd')
  const userId = user?.id || ''
  
  console.log('🔍 API 호출 파라미터:', {
    startDate,
    endDate,
    userId,
    currentMonth: format(currentMonth, 'yyyy-MM')
  })
  
  const { data: plansData, isLoading, isFetching, error, refetch } = usePlansRange(
    startDate,
    endDate,
    userId
  )
  
  // React Query 캐시 상태 직접 확인
  const queryClient = useQueryClient()
  const cacheKey = ['plans-range', startDate, endDate, userId]
  const cachedData = queryClient.getQueryData(cacheKey)
  
  console.log('🔍 React Query 캐시 상태:', {
    cacheKey,
    hasCachedData: !!cachedData,
    cachedDataLength: Array.isArray(cachedData) ? cachedData.length : 'not-array',
    cachedData: cachedData,
    plansDataLength: plansData ? plansData.length : 0,
    isLoading,
    isFetching,
    timestamp: new Date().toISOString()
  })
  
  // 캐시된 데이터 우선 사용 (React Query 캐시에서 직접 가져오기)
  const effectivePlansData = cachedData || plansData
  const hasCachedData = !!(effectivePlansData && Array.isArray(effectivePlansData) && effectivePlansData.length > 0)
  
  console.log('🔍 효과적인 데이터 선택:', {
    usingCachedData: !!cachedData,
    cachedDataLength: Array.isArray(cachedData) ? cachedData.length : 0,
    plansDataLength: Array.isArray(plansData) ? plansData.length : 0,
    effectiveDataLength: Array.isArray(effectivePlansData) ? effectivePlansData.length : 0,
    hasCachedData
  })
  
  // 캐시 데이터 상태 로깅
  console.log('🔍 캐시 데이터 상태:', {
    hasCachedData,
    plansDataLength: plansData ? plansData.length : 0,
    mealDataKeys: Object.keys(mealData).length,
    currentMonth: format(currentMonth, 'yyyy-MM'),
    userId: user?.id || 'no-user',
    timestamp: new Date().toISOString()
  })
  
  // 월이 변경될 때마다 강제로 데이터 새로고침
  useEffect(() => {
    console.log(`🔄 월 변경 감지: ${format(currentMonth, 'yyyy-MM')} - 데이터 새로고침`)
    
    // 캐시된 데이터가 있으면 먼저 보여주고 백그라운드에서 새로고침
    if (hasCachedData) {
      console.log('📦 캐시된 데이터 있음 - 먼저 표시하고 백그라운드에서 새로고침')
      // 로딩 상태는 표시하지 않음 (캐시된 데이터가 이미 보여지고 있으므로)
      refetch()
    } else {
      console.log('📭 캐시된 데이터 없음 - 로딩 표시하고 새로고침')
      // 로딩 상태 표시
      const { setCalendarLoading } = useCalendarStore.getState()
      setCalendarLoading(true)
      refetch()
    }
  }, [currentMonth, refetch, hasCachedData])
  
  // 전역 캘린더 로딩 상태 가져오기
  const { isCalendarLoading } = useCalendarStore()
  
  // 채팅에서 저장 후 캘린더로 이동했을 때 즉시 데이터 새로고침
  useEffect(() => {
    console.log('🔍 저장 감지 체크:', {
      isRecentSave: isRecentSave(),
      hasCachedData,
      timestamp: new Date().toISOString()
    })
    
    if (isRecentSave()) {
      console.log('💾 최근 저장 감지 - 캘린더 데이터 즉시 새로고침')
      
      // 캐시된 데이터가 있으면 먼저 보여주고 백그라운드에서 새로고침
      if (hasCachedData) {
        console.log('📦 저장 후 캐시된 데이터 있음 - 먼저 표시하고 백그라운드에서 새로고침')
        // 로딩 상태는 표시하지 않음 (캐시된 데이터가 이미 보여지고 있으므로)
        refetch()
      } else {
        console.log('📭 저장 후 캐시된 데이터 없음 - 로딩 표시하고 새로고침')
        // 로딩 상태 표시
        const { setCalendarLoading } = useCalendarStore.getState()
        setCalendarLoading(true)
        refetch()
      }
      
      // 저장 상태 초기화 (2초 후)
      setTimeout(() => {
        clearSaveState()
      }, 2000)
    } else {
      // 저장 감지가 안되더라도 캐시된 데이터가 있으면 항상 먼저 보여주기
      if (hasCachedData) {
        console.log('📦 캐시된 데이터 있음 - 먼저 표시 (저장 감지 없음)')
        // 백그라운드에서 새로고침
        refetch()
      }
    }
  }, [isRecentSave, refetch, clearSaveState, hasCachedData])
  
  // 저장 후 로딩 상태를 더 오래 유지하기 위한 추가 로직
  useEffect(() => {
    if (isCalendarLoading && isRecentSave()) {
      console.log('🔄 저장 후 로딩 상태 유지 중...')
      // 3초 후에 로딩 상태 해제 (데이터 로드 완료를 기다림)
      const timer = setTimeout(() => {
        const { setCalendarLoading } = useCalendarStore.getState()
        setCalendarLoading(false)
        console.log('⏰ 저장 후 로딩 상태 자동 해제')
      }, 3000)
      
      return () => clearTimeout(timer)
    }
  }, [isCalendarLoading, isRecentSave])
  
  // 월 변경 시 로딩 상태 자동 해제
  useEffect(() => {
    if (isCalendarLoading && !isRecentSave()) {
      console.log('🔄 월 변경 로딩 상태 유지 중...')
      // 2초 후에 로딩 상태 해제 (월 변경은 더 빠르게)
      const timer = setTimeout(() => {
        const { setCalendarLoading } = useCalendarStore.getState()
        setCalendarLoading(false)
        console.log('⏰ 월 변경 로딩 상태 자동 해제')
      }, 2000)
      
      return () => clearTimeout(timer)
    }
  }, [isCalendarLoading, isRecentSave])
  
  // 데이터가 실제로 변경되었는지 확인
  const hasDataChanged = useMemo(() => {
    if (!plansData || !Array.isArray(plansData) || !previousPlansData) {
      return true // 첫 로드이거나 이전 데이터가 없으면 변경된 것으로 간주
    }
    
    // 길이가 다르면 변경됨
    if (plansData.length !== previousPlansData.length) {
      return true
    }
    
    // 각 항목의 핵심 필드 비교 (id, title, date, slot)
    return plansData.some((currentPlan, index) => {
      const previousPlan = previousPlansData[index]
      if (!previousPlan) return true
      
      return (
        currentPlan.id !== previousPlan.id ||
        currentPlan.title !== previousPlan.title ||
        currentPlan.date !== previousPlan.date ||
        currentPlan.slot !== previousPlan.slot
      )
    })
  }, [plansData, previousPlansData])
  
  // 전체 로딩 상태 (API 로딩 또는 전역 캘린더 로딩)
  const isAnyLoading = isLoading || isCalendarLoading
  
  // 채팅 저장 후 로딩: 저장 감지 시 무조건 로딩 표시
  const isPostSaveLoading = isCalendarLoading && isRecentSave()
  
  // 캐시된 데이터가 있으면 먼저 보여주고, 그 위에 로딩 오버레이만 표시
  const shouldShowLoading = isAnyLoading && !hasCachedData
  
  // 오버레이 로딩: 채팅 저장 후에는 무조건 표시, 그 외에는 캐시된 데이터가 있을 때만
  const shouldShowOverlay = isPostSaveLoading || (isAnyLoading && hasCachedData)
  
  
  // 초기 진입 시 데이터가 아직 없을 때도 로딩을 보장
  const isInitialLoading = !!(user?.id) && !plansData && Object.keys(mealData).length === 0
  
  // 데이터가 변경되었을 때 이전 데이터 업데이트
  useEffect(() => {
    if (plansData && Array.isArray(plansData) && hasDataChanged) {
      console.log('📊 데이터 변경 감지 - 이전 데이터 업데이트')
      setPreviousPlansData([...plansData])
    }
  }, [plansData, hasDataChanged])

  
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

  // 캘린더 저장 완료 이벤트 리스너 (저장 후에만 리페치)
  useEffect(() => {
    const handleCalendarSave = () => {
      console.log('🎉 캘린더 저장 완료 이벤트 수신 - 데이터 새로고침')
      refetch()
    }

    window.addEventListener('calendar-saved', handleCalendarSave)
    
    return () => {
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
    console.log('🔄 데이터 변환 로직 체크:', {
      hasPlansData: !!plansData,
      hasUserId: !!user?.id,
      isArray: Array.isArray(plansData),
      plansDataLength: plansData ? plansData.length : 0,
      userId: user?.id || 'no-user'
    })
    
    if (effectivePlansData && user?.id && Array.isArray(effectivePlansData)) {
      console.log('📅 효과적인 식단 데이터 로드:', effectivePlansData)
      console.log('📅 데이터 타입:', typeof effectivePlansData, '길이:', effectivePlansData.length)

      const convertedData: Record<string, MealData> = {}
      const convertedPlanIds: Record<string, Record<string, string>> = {}

      effectivePlansData.forEach((plan: any, index: number) => {
        console.log(`🔄 변환 중 [${index + 1}/${effectivePlansData.length}]:`, {
          id: plan.id,
          date: plan.date,
          slot: plan.slot,
          title: plan.title,
          notes: plan.notes,
          url: plan.url
        })
        
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
          console.log(`📅 날짜 키 생성: ${plan.date} → ${dateKey}`)

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
          // 슬롯에 맞는 식단 데이터 설정 (URL 포함)
          if (plan.slot === 'breakfast') {
            convertedData[dateKey].breakfast = plan.title || plan.notes || ''
            convertedData[dateKey].breakfastUrl = plan.url || undefined
            convertedData[dateKey].breakfastCompleted = plan.status === 'done'
            convertedPlanIds[dateKey].breakfast = plan.id
          } else if (plan.slot === 'lunch') {
            convertedData[dateKey].lunch = plan.title || plan.notes || ''
            convertedData[dateKey].lunchUrl = plan.url || undefined
            convertedData[dateKey].lunchCompleted = plan.status === 'done'
            convertedPlanIds[dateKey].lunch = plan.id
          } else if (plan.slot === 'dinner') {
            convertedData[dateKey].dinner = plan.title || plan.notes || ''
            convertedData[dateKey].dinnerUrl = plan.url || undefined
            convertedData[dateKey].dinnerCompleted = plan.status === 'done'
            convertedPlanIds[dateKey].dinner = plan.id
          } else if (plan.slot === 'snack') {
            convertedData[dateKey].snack = plan.title || plan.notes || ''
            convertedData[dateKey].snackUrl = plan.url || undefined
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
      console.log('📊 변환 결과 요약:', {
        원본데이터개수: effectivePlansData.length,
        변환된날짜개수: Object.keys(convertedData).length,
        변환된데이터키: Object.keys(convertedData),
        각날짜별슬롯개수: Object.entries(convertedData).map(([date, data]) => ({
          날짜: date,
          슬롯개수: Object.values(data).filter(v => v !== '').length
        }))
      })
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
    } else if (user?.id && !isAnyLoading && (!effectivePlansData || !Array.isArray(effectivePlansData) || effectivePlansData.length === 0)) {
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
    isLoading: shouldShowLoading || isInitialLoading, // 캐시된 데이터가 없을 때만 전체 로딩
    isLoadingOverlay: shouldShowOverlay, // 캐시된 데이터가 있을 때 오버레이 로딩
    error,
    isSaving,
    formatDateKey,
    getMealForDate,
    toggleMealCheck,
    isMealChecked,
    isOptimisticMeal
  }
}
