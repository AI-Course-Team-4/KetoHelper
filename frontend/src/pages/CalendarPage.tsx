import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CalendarToday, Add, BarChart, ChevronLeft, ChevronRight, Close, Save } from '@mui/icons-material'
import { DayPicker } from 'react-day-picker'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import 'react-day-picker/dist/style.css'
import { MealData, generateRandomMeal } from '@/data/ketoMeals'
import { MealModal } from '@/components/MealModal'
import { DateDetailModal } from '@/components/DateDetailModal'
import { usePlansRange, useCreatePlan, useGenerateMealPlan, useUpdatePlan, useDeletePlan } from '@/hooks/useApi'
import { useAuthStore } from '@/store/authStore'
import { useProfileStore } from '@/store/profileStore'
import { useQueryClient } from '@tanstack/react-query'

// 컴포넌트 상단에 추가
const getMealText = (mealData: MealData | null, mealType: string): string => {
  if (!mealData) return '';

  switch (mealType) {
    case 'breakfast':
      return mealData.breakfast || '';
    case 'lunch':
      return mealData.lunch || '';
    case 'dinner':
      return mealData.dinner || '';
    case 'snack':
      return mealData.snack || '';
    default:
      return '';
  }
};

export function CalendarPage() {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date())
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [mealData, setMealData] = useState<Record<string, MealData>>({})
  const [planIds, setPlanIds] = useState<Record<string, Record<string, string>>>({}) // {dateKey: {breakfast: planId, lunch: planId, ...}}
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedMealType, setSelectedMealType] = useState<string | null>(null)
  const [isDateDetailModalOpen, setIsDateDetailModalOpen] = useState(false)
  const [clickedDate, setClickedDate] = useState<Date | null>(null)
  const [generatedMealPlan, setGeneratedMealPlan] = useState<Record<string, MealData> | null>(null)
  const [showMealPlanSaveModal, setShowMealPlanSaveModal] = useState(false)
  const [selectedDays, setSelectedDays] = useState(7) // 기본 7일
  // 체크 상태만을 위한 로컬 state (UI용)
  const [mealCheckState, setMealCheckState] = useState<Record<string, {
    breakfastCompleted?: boolean
    lunchCompleted?: boolean
    dinnerCompleted?: boolean
    snackCompleted?: boolean
  }>>({})

  // 사용자 인증 정보
  const { user } = useAuthStore()
  const { profile } = useProfileStore()
  const createPlan = useCreatePlan()
  const generateMealPlan = useGenerateMealPlan()
  const updatePlan = useUpdatePlan()
  const deletePlan = useDeletePlan()
  const queryClient = useQueryClient()
  const [isGeneratingMealPlan, setIsGeneratingMealPlan] = useState(false)
  const [isSavingMealPlan, setIsSavingMealPlan] = useState(false)

  // 현재 월의 시작일과 종료일 계산
  const startOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1)
  const endOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0)

  // API로 실제 데이터 가져오기
  const { data: plansData, isLoading, error } = usePlansRange(
    format(startOfMonth, 'yyyy-MM-dd'),
    format(endOfMonth, 'yyyy-MM-dd'),
    user?.id || ''
  )

  // API 데이터를 캘린더 형식으로 변환
  useEffect(() => {
    if (plansData && user?.id) {
      console.log('📅 API에서 식단 데이터 로드:', plansData)

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

      setMealData(convertedData)
      setPlanIds(convertedPlanIds)
      console.log('✅ API 데이터 변환 완료:', convertedData)
      console.log('✅ Plan IDs 저장 완료:', convertedPlanIds)
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

  // 샘플 데이터 생성 (UI 테스트용)
  const loadSampleMealData = (month: Date) => {
    console.log('🎨 샘플 데이터 로드 (UI 테스트용)')

    // 간단한 샘플 데이터 생성
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

  const handleDateSelect = (date: Date | undefined) => {
    setSelectedDate(date)
  }

  // 날짜 클릭 핸들러 (모달 열기)
  const handleDateClick = (date: Date) => {
    setClickedDate(date)
    setIsDateDetailModalOpen(true)
  }

  const handleMonthChange = (month: Date) => {
    setCurrentMonth(month)
  }

  // AI 식단표 생성 버튼 클릭 핸들러
  const handleGenerateMealPlan = async () => {
    if (!user?.id) {
      alert('로그인이 필요합니다.')
      return
    }

    setIsGeneratingMealPlan(true)

    try {
      console.log('🤖 AI 식단표 생성 시작...')

      // AI 식단 생성 API 호출
      const mealPlanData = await generateMealPlan.mutateAsync({
        user_id: user.id,
        days: selectedDays, // 선택된 일수만큼 식단표 생성
        kcal_target: profile?.goals_kcal || 1800,
        carbs_max: profile?.goals_carbs_g || 20,
        allergies: profile?.allergy_names || [],
        dislikes: profile?.dislike_names || []
      })

      console.log('✅ AI 식단표 생성 완료:', mealPlanData)

      // 생성된 식단을 상태에 저장하고 저장 모달 표시
      setGeneratedMealPlan(mealPlanData)
      setShowMealPlanSaveModal(true)

    } catch (error) {
      console.error('❌ AI 식단표 생성 실패:', error)

      // 사용자에게 오류 메시지 표시
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'
      alert(`AI 식단표 생성에 실패했습니다.\n${errorMessage}\n\n기본 식단으로 대체합니다.`)

      // 폴백: 로컬 랜덤 식단 생성
      console.log('📝 폴백: 로컬 랜덤 식단 생성')
      const newMealData: Record<string, MealData> = {}

      try {
        // 선택된 일수만큼 랜덤 식단 생성
        for (let day = 0; day < selectedDays; day++) {
          const currentDate = new Date()
          if (isNaN(currentDate.getTime())) {
            console.error('❌ 현재 날짜가 유효하지 않습니다.')
            break
          }

          currentDate.setDate(currentDate.getDate() + day)
          const dateString = format(currentDate, 'yyyy-MM-dd')

          // 선택된 일수만큼 식단 생성
          newMealData[dateString] = generateRandomMeal()
        }

        if (Object.keys(newMealData).length > 0) {
          setGeneratedMealPlan(newMealData)
          setShowMealPlanSaveModal(true)
        } else {
          console.error('❌ 폴백 식단 생성 실패')
          alert('식단 생성에 완전히 실패했습니다. 다시 시도해주세요.')
        }
      } catch (fallbackError) {
        console.error('❌ 폴백 식단 생성 중 오류:', fallbackError)
        alert('기본 식단 생성도 실패했습니다. 잠시 후 다시 시도해주세요.')
      }

    } finally {
      setIsGeneratingMealPlan(false)
    }
  }

  // 날짜 문자열로 변환하는 헬퍼 함수
  const formatDateKey = (date: Date) => {
    try {
      if (!date || isNaN(date.getTime())) {
        console.warn('⚠️ 유효하지 않은 날짜:', date)
        return format(new Date(), 'yyyy-MM-dd') // 기본값으로 오늘 날짜 사용
      }
      return format(date, 'yyyy-MM-dd')
    } catch (error) {
      console.error('❌ 날짜 포맷 변환 오류:', error, date)
      return format(new Date(), 'yyyy-MM-dd') // 오류 시 오늘 날짜 반환
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

  // 모달 열기 핸들러
  const handleOpenModal = (mealType?: string) => {
    setSelectedMealType(mealType || null)
    setIsModalOpen(true)
  }

  // 모달 닫기 핸들러
  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedMealType(null)
  }

  // 날짜 상세 모달 닫기 핸들러
  const handleCloseDateDetailModal = () => {
    setIsDateDetailModalOpen(false)
    setClickedDate(null)
  }

  // AI 생성 식단표 저장 핸들러 (병렬 처리 최적화)
  const handleSaveGeneratedMealPlan = async () => {
    if (!user?.id || !generatedMealPlan) {
      alert('로그인이 필요하거나 저장할 식단이 없습니다.')
      return
    }

    setIsSavingMealPlan(true)

    try {
      console.log('💾 AI 생성 식단표 저장 시작... (병렬 처리)')
      const startTime = Date.now()

      // 모든 저장 요청을 배열로 준비
      const savePromises: Promise<any>[] = []
      const saveInfo: Array<{ dateString: string, slot: string, title: string }> = []

      for (const [dateString, mealData] of Object.entries(generatedMealPlan)) {
        const mealSlots = ['breakfast', 'lunch', 'dinner', 'snack'] as const

        for (const slot of mealSlots) {
          const mealTitle = mealData[slot]
          if (mealTitle && mealTitle.trim()) {
            const planData = {
              user_id: user.id,
              date: dateString,
              slot: slot,
              type: 'recipe' as const,
              ref_id: '',
              title: mealTitle.trim(),
              location: undefined,
              macros: undefined,
              notes: undefined
            }

            // Promise를 배열에 추가 (즉시 실행되지 않음)
            savePromises.push(createPlan.mutateAsync(planData))
            saveInfo.push({ dateString, slot, title: mealTitle.trim() })
          }
        }
      }

      console.log(`📊 총 ${savePromises.length}개 식단을 병렬로 저장 시작...`)

      // 모든 API 호출을 병렬로 실행 (하나라도 실패하면 전체 실패)
      try {
        await Promise.all(savePromises)

        const endTime = Date.now()
        const duration = ((endTime - startTime) / 1000).toFixed(1)

        console.log(`⚡ 전체 저장 완료! 소요시간: ${duration}초`)
        console.log(`✅ 총 ${savePromises.length}개 식단 저장 성공`)

        // 캘린더 데이터 새로고침
        queryClient.invalidateQueries({ queryKey: ['plans-range'] })

        // 생성된 식단을 로컬 상태에도 반영
        setMealData(prev => ({ ...prev, ...generatedMealPlan }))

        // 모달 닫기
        setShowMealPlanSaveModal(false)
        setGeneratedMealPlan(null)

        alert(`✅ AI 식단표 저장 완료! (${duration}초)\n총 ${savePromises.length}개 식단이 저장되었습니다.`)

      } catch (error) {
        const endTime = Date.now()
        const duration = ((endTime - startTime) / 1000).toFixed(1)

        console.error(`❌ 저장 실패! 소요시간: ${duration}초`, error)
        throw new Error(`저장에 실패했습니다. (${duration}초)`)
      }

    } catch (error) {
      console.error('❌ AI 식단표 저장 실패:', error)
      alert('식단표 저장에 실패했습니다. 다시 시도해주세요.')
    } finally {
      setIsSavingMealPlan(false)
    }
  }

  // AI 생성 식단표 저장 모달 닫기 핸들러
  const handleCloseMealPlanSaveModal = () => {
    setShowMealPlanSaveModal(false)
    setGeneratedMealPlan(null)
    setSelectedDays(7) // 기본값으로 재설정
  }

  // 추가 일수 식단 생성 핸들러
  const handleGenerateMoreDays = async (additionalDays: number) => {
    if (!user?.id || !generatedMealPlan) {
      alert('오류가 발생했습니다.')
      return
    }

    setIsGeneratingMealPlan(true)

    try {
      console.log(`🤖 추가 ${additionalDays}일 식단표 생성 시작...`)

      // 현재 생성된 식단의 마지막 날짜 찾기
      const existingDates = Object.keys(generatedMealPlan).sort()
      if (existingDates.length === 0) {
        console.error('❌ 기존 식단 데이터가 없습니다.')
        alert('기존 식단 데이터가 없어 추가 생성할 수 없습니다.')
        return
      }

      const lastDateString = existingDates[existingDates.length - 1]
      const lastDate = new Date(lastDateString)

      if (isNaN(lastDate.getTime())) {
        console.error('❌ 마지막 날짜가 유효하지 않습니다:', lastDateString)
        alert('날짜 정보가 올바르지 않아 추가 생성할 수 없습니다.')
        return
      }

      // 추가 일수만큼 생성
      const newMealData: Record<string, MealData> = { ...generatedMealPlan }

      try {
        // AI 식단 생성 API 호출 (추가 일수)
        const additionalMealPlan = await generateMealPlan.mutateAsync({
          user_id: user.id,
          days: additionalDays,
          kcal_target: profile?.goals_kcal || 1800,
          carbs_max: profile?.goals_carbs_g || 20,
          allergies: profile?.allergy_names || [],
          dislikes: profile?.dislike_names || []
        })

        // 기존 데이터와 합치기
        Object.assign(newMealData, additionalMealPlan)

      } catch (error) {
        console.error('❌ 추가 AI 식단 생성 실패, 폴백 사용:', error)

        // 폴백: 로컬 랜덤 식단 생성
        try {
          for (let day = 1; day <= additionalDays; day++) {
            const newDate = new Date(lastDate)
            newDate.setDate(lastDate.getDate() + day)

            if (isNaN(newDate.getTime())) {
              console.error('❌ 새 날짜 생성 실패:', day)
              continue
            }

            const dateString = format(newDate, 'yyyy-MM-dd')
            newMealData[dateString] = generateRandomMeal()
          }
        } catch (fallbackError) {
          console.error('❌ 폴백 식단 생성 실패:', fallbackError)
          alert('추가 식단 생성에 실패했습니다.')
          return
        }
      }

      setGeneratedMealPlan(newMealData)
      setSelectedDays(existingDates.length + additionalDays)

      console.log(`✅ 추가 ${additionalDays}일 식단 생성 완료`)

    } catch (error) {
      console.error('❌ 추가 식단 생성 실패:', error)
      alert('추가 식단 생성에 실패했습니다. 다시 시도해주세요.')
    } finally {
      setIsGeneratingMealPlan(false)
    }
  }

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

  // 실제 API를 사용한 식단 저장/수정
  const handleSaveMeal = async (date: Date, newMealData: MealData) => {
    if (!user?.id) {
      alert('로그인이 필요합니다.')
      return
    }

    console.log('💾 API 저장/수정 시작:', { date, newMealData })

    try {
      const dateString = format(date, 'yyyy-MM-dd')
      const dateKey = formatDateKey(date)
      const mealSlots = ['breakfast', 'lunch', 'dinner', 'snack'] as const
      const existingPlanIds = planIds[dateKey] || {}

      for (const slot of mealSlots) {
        const mealTitle = newMealData[slot]
        const existingPlanId = existingPlanIds[slot]

        if (mealTitle && mealTitle.trim()) {
          // 식단이 있는 경우 - 새로 생성 또는 수정
          try {
            const planData = {
              user_id: user.id,
              date: dateString,
              slot: slot,
              type: 'recipe' as const,
              ref_id: '',
              title: mealTitle.trim(),
              location: undefined,
              macros: undefined,
              notes: undefined
            }

            if (existingPlanId) {
              // 기존 plan 업데이트
              await updatePlan.mutateAsync({
                planId: existingPlanId,
                updates: { notes: mealTitle.trim() },
                userId: user.id
              })
              console.log(`✅ ${slot} 수정 완료:`, mealTitle)
            } else {
              // 새 plan 생성
              await createPlan.mutateAsync(planData)
              console.log(`✅ ${slot} 생성 완료:`, mealTitle)
            }
          } catch (error) {
            console.error(`❌ ${slot} 저장/수정 실패:`, error)
          }
        } else if (existingPlanId) {
          // 식단이 비어있지만 기존 plan이 있는 경우 - 삭제
          try {
            await deletePlan.mutateAsync({
              planId: existingPlanId,
              userId: user.id
            })
            console.log(`✅ ${slot} 삭제 완료`)
          } catch (error) {
            console.error(`❌ ${slot} 삭제 실패:`, error)
          }
        }
      }

      // 캘린더 데이터 새로고침
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })

      console.log('✅ 식단 저장/수정/삭제 완료!')
    } catch (error) {
      console.error('❌ 식단 처리 실패:', error)
      alert('식단 처리에 실패했습니다. 다시 시도해주세요.')
    }
  }

  // 개별 식단 삭제 함수
  const handleDeleteMeal = async (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => {
    if (!user?.id) {
      alert('로그인이 필요합니다.')
      return
    }

    const dateKey = formatDateKey(date)
    const planId = planIds[dateKey]?.[mealType]

    if (!planId) {
      alert('삭제할 식단이 없습니다.')
      return
    }

    if (!confirm('이 식단을 삭제하시겠습니까?')) {
      return
    }

    try {
      await deletePlan.mutateAsync({
        planId: planId,
        userId: user.id
      })

      // 캘린더 데이터 새로고침
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })

      console.log(`✅ ${mealType} 삭제 완료`)
    } catch (error) {
      console.error(`❌ ${mealType} 삭제 실패:`, error)
      alert('식단 삭제에 실패했습니다. 다시 시도해주세요.')
    }
  }

  // 하루 전체 식단 삭제 함수
  const handleDeleteAllMeals = async (date: Date) => {
    if (!user?.id) {
      alert('로그인이 필요합니다.')
      return
    }

    const dateKey = formatDateKey(date)
    const dayPlanIds = planIds[dateKey]

    if (!dayPlanIds || Object.keys(dayPlanIds).length === 0) {
      alert('삭제할 식단이 없습니다.')
      return
    }

    try {
      console.log('🗑️ 하루 전체 식단 삭제 시작...')

      // 모든 식단 삭제를 병렬로 처리
      const deletePromises = Object.entries(dayPlanIds).map(([, planId]) =>
        deletePlan.mutateAsync({
          planId: planId,
          userId: user.id
        })
      )

      await Promise.all(deletePromises)

      // 캘린더 데이터 새로고침
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })

      console.log(`✅ ${format(date, 'M월 d일')} 전체 식단 삭제 완료`)
      alert(`${format(date, 'M월 d일')} 식단이 모두 삭제되었습니다.`)

    } catch (error) {
      console.error('❌ 전체 식단 삭제 실패:', error)
      alert('전체 식단 삭제에 실패했습니다. 다시 시도해주세요.')
    }
  }

  // UI 테스트 모드 (로그인 불필요)

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white">
        <div className="relative p-6">
          <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
            <div className="flex-1">
              <h1 className="text-3xl font-bold mb-2">🥑 식단 캘린더</h1>
              <p className="text-green-100">
                키토 식단 계획을 스마트하게 관리하고 기록하세요
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <select 
                value={selectedDays} 
                onChange={(e) => setSelectedDays(Number(e.target.value))}
                disabled={isGeneratingMealPlan}
                className="px-3 py-2 bg-white/20 border border-white/30 text-white rounded-lg disabled:opacity-50"
              >
                <option value={3} className="text-gray-800">3일</option>
                <option value={7} className="text-gray-800">7일</option>
                <option value={14} className="text-gray-800">14일</option>
                <option value={30} className="text-gray-800">30일</option>
              </select>
              
              <Button 
                onClick={handleGenerateMealPlan}
                disabled={isGeneratingMealPlan}
                className="px-3 py-2 bg-white border border-white text-green-600 rounded-lg hover:bg-green-50 hover:text-green-700 font-semibold disabled:opacity-50 shadow-md"
              >
                <Add sx={{ fontSize: 20, mr: 1 }} />
                {isGeneratingMealPlan ? '생성 중...' : `AI 식단표 생성`}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* 주간 통계 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border border-gray-200 bg-gradient-to-br from-green-50 to-emerald-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-600">85%</div>
                <div className="text-sm font-medium text-green-700">이행률</div>
              </div>
              <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                <BarChart className="h-5 w-5 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 bg-gradient-to-br from-orange-50 to-amber-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-orange-600">22g</div>
                <div className="text-sm font-medium text-orange-700">평균 탄수화물</div>
              </div>
              <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-lg">C</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 bg-gradient-to-br from-blue-50 to-cyan-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-600">1,650</div>
                <div className="text-sm font-medium text-blue-700">평균 칼로리</div>
              </div>
              <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xl">🔥</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 bg-gradient-to-br from-purple-50 to-violet-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-purple-600">30%</div>
                <div className="text-sm font-medium text-purple-700">외식 비중</div>
              </div>
              <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xl">🍽️</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 캘린더 */}
        <Card className="lg:col-span-3 border border-gray-200">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center text-xl font-bold">
                <CalendarToday sx={{ fontSize: 24, mr: 1.5, color: 'green.600' }} />
                월간 캘린더
              </CardTitle>
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
                  className="hover:bg-green-50 hover:border-green-300"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-lg font-bold min-w-[140px] text-center bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                  {format(currentMonth, 'yyyy년 M월', { locale: ko })}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
                  className="hover:bg-green-50 hover:border-green-300"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6 pt-0">
            {isLoading && (
              <div className="flex items-center justify-center py-8">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-2"></div>
                  <p className="text-gray-600">식단 데이터를 불러오는 중...</p>
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-center justify-center py-8">
                <div className="text-center text-red-600">
                  <p>데이터를 불러오는 중 오류가 발생했습니다.</p>
                  <p className="text-sm mt-1">샘플 데이터를 표시합니다.</p>
                </div>
              </div>
            )}

            {!isLoading && !error && (
              <div className="calendar-container w-full flex items-start justify-center overflow-x-auto">
                <DayPicker
                  mode="single"
                  selected={selectedDate}
                  onSelect={handleDateSelect}
                  month={currentMonth}
                  onMonthChange={handleMonthChange}
                  locale={ko}
                  className="rdp-custom w-full"
                  modifiers={{
                    hasMeal: Object.keys(mealData).map(date => new Date(date)),
                    hasPartialMeal: Object.keys(mealData).filter(date => {
                      const meal = mealData[date]
                      const mealCount = [meal.breakfast, meal.lunch, meal.dinner].filter(Boolean).length
                      return mealCount > 0 && mealCount < 3
                    }).map(date => new Date(date)),
                    hasCompleteMeal: Object.keys(mealData).filter(date => {
                      const meal = mealData[date]
                      return meal.breakfast && meal.lunch && meal.dinner
                    }).map(date => new Date(date)),
                    today: new Date() // 오늘 날짜 추가
                  }}
                  modifiersStyles={{
                    hasPartialMeal: {
                      backgroundColor: '#f59e0b',
                      color: 'white',
                      fontWeight: 'bold',
                      borderRadius: '12px',
                      boxShadow: '0 2px 8px rgba(245, 158, 11, 0.3)'
                    },
                    hasCompleteMeal: {
                      backgroundColor: '#10b981',
                      color: 'white',
                      fontWeight: 'bold',
                      borderRadius: '12px',
                      boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)'
                    },
                    today: {
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      fontWeight: 'bold',
                      borderRadius: '12px',
                      boxShadow: '0 2px 8px rgba(59, 130, 246, 0.4)',
                      border: '2px solid #1d4ed8'
                    }
                  }}
                  components={{
                    Day: ({ date, displayMonth }) => {
                      const meal = getMealForDate(date)
                      const isCurrentMonth = date.getMonth() === displayMonth.getMonth()



                      // 체크된 식사 개수 계산 (로컬 상태에서)
                      const checkedCount = [
                        isMealChecked(date, 'breakfast'),
                        isMealChecked(date, 'lunch'),
                        isMealChecked(date, 'dinner'),
                        isMealChecked(date, 'snack')
                      ].filter(Boolean).length

                      return (
                        <div
                          className="relative w-full h-full flex flex-col min-w-0 cursor-pointer hover:bg-gray-50 transition-colors rounded-lg"
                          onClick={() => isCurrentMonth && handleDateClick(date)}
                        >
                          {isCurrentMonth && (
                            <div className="date-number w-full flex items-center justify-between px-3">
                              <span>{date.getDate()}</span>
                              {checkedCount > 0 && (
                                <div className="absolute -top-1 -right-1 bg-green-500 rounded-full w-4 h-4 flex items-center justify-center">
                                  <span className="text-white text-xs font-bold">✓</span>
                                </div>
                              )}
                            </div>
                          )}

                          {meal && isCurrentMonth && (
                            <div className="meal-info-container w-full min-w-0 flex flex-col p-1 gap-0.5">
                              {/* 공통 줄 클래스 */}
                              {/* grid-cols-[auto,1fr,auto] : 아이콘 | 텍스트 | 체크 */}
                              {/* items-center : 수직 정렬, gap-1 : 간격 */}
                              {/* text-xs 는 부모나 필요한 span에 */}
                              {/* 아침 */}
                              {meal.breakfast?.trim() && (
                                <div className="w-full grid grid-cols-[auto,1fr,auto] items-center gap-1 group px-2">
                                  <span className="text-xs">🌅</span>
                                  <span className="min-w-0 truncate text-xs text-left" title={meal.breakfast}>
                                    <span className="hidden sm:inline">{meal.breakfast}</span>
                                    <span className="sm:hidden">
                                      {meal.breakfast.length > 8 ? meal.breakfast.slice(0, 8) + '…' : meal.breakfast}
                                    </span>
                                  </span>
                                  <button
                                    onClick={(e) => { e.stopPropagation(); toggleMealCheck(date, 'breakfast'); }}
                                    className="justify-self-end opacity-60 group-hover:opacity-100 transition-opacity text-xs"
                                    aria-label="breakfast done"
                                  >
                                    {isMealChecked(date, 'breakfast') ? <span className="text-green-500">✅</span> : <span className="text-gray-400">⭕</span>}
                                  </button>
                                </div>
                              )}

                              {/* 점심 */}
                              {meal.lunch?.trim() && (
                                <div className="w-full grid grid-cols-[auto,1fr,auto] items-center gap-1 group px-2">
                                  <span className="text-xs">☀️</span>
                                  <span className="min-w-0 truncate text-xs text-left" title={meal.lunch}>
                                    <span className="hidden sm:inline">{meal.lunch}</span>
                                    <span className="sm:hidden">
                                      {meal.lunch.length > 8 ? meal.lunch.slice(0, 8) + '…' : meal.lunch}
                                    </span>
                                  </span>
                                  <button
                                    onClick={(e) => { e.stopPropagation(); toggleMealCheck(date, 'lunch'); }}
                                    className="justify-self-end opacity-60 group-hover:opacity-100 transition-opacity text-xs"
                                    aria-label="lunch done"
                                  >
                                    {isMealChecked(date, 'lunch') ? <span className="text-green-500">✅</span> : <span className="text-gray-400">⭕</span>}
                                  </button>
                                </div>
                              )}

                              {/* 저녁 */}
                              {meal.dinner?.trim() && (
                                <div className="w-full grid grid-cols-[auto,1fr,auto] items-center gap-1 group px-2">
                                  <span className="text-xs">🌙</span>
                                  <span className="min-w-0 truncate text-xs text-left" title={meal.dinner}>
                                    <span className="hidden sm:inline">{meal.dinner}</span>
                                    <span className="sm:hidden">
                                      {meal.dinner.length > 8 ? meal.dinner.slice(0, 8) + '…' : meal.dinner}
                                    </span>
                                  </span>
                                  <button
                                    onClick={(e) => { e.stopPropagation(); toggleMealCheck(date, 'dinner'); }}
                                    className="justify-self-end opacity-60 group-hover:opacity-100 transition-opacity text-xs"
                                    aria-label="dinner done"
                                  >
                                    {isMealChecked(date, 'dinner') ? <span className="text-green-500">✅</span> : <span className="text-gray-400">⭕</span>}
                                  </button>
                                </div>
                              )}

                              {/* 간식 */}
                              {meal.snack?.trim() && (
                                <div className="w-full grid grid-cols-[auto,1fr,auto] items-center gap-1 group text-purple-600 px-2">
                                  <span className="text-xs">🍎</span>
                                  <span className="min-w-0 truncate text-xs text-left" title={meal.snack}>
                                    <span className="hidden sm:inline">{meal.snack}</span>
                                    <span className="sm:hidden">
                                      {meal.snack.length > 8 ? meal.snack.slice(0, 8) + '…' : meal.snack}
                                    </span>
                                  </span>
                                  <button
                                    onClick={(e) => { e.stopPropagation(); toggleMealCheck(date, 'snack'); }}
                                    className="justify-self-end opacity-60 group-hover:opacity-100 transition-opacity text-xs"
                                    aria-label="snack done"
                                  >
                                    {isMealChecked(date, 'snack') ? <span className="text-green-500">✅</span> : <span className="text-gray-400">⭕</span>}
                                  </button>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    }
                  }}
                  styles={{
                    head_cell: {
                      width: '120px',
                      height: '40px',
                      minWidth: '120px',
                      maxWidth: '120px',
                      fontSize: '12px',
                      color: '#374151',
                      textTransform: 'uppercase',
                      letterSpacing: '0.8px',
                      backgroundColor: '#f8fafc',
                      borderRight: '1px solid #e2e8f0',
                      borderBottom: '2px solid #e2e8f0',
                      borderTop: '1px solid #e2e8f0',
                      borderLeft: '1px solid #e2e8f0',
                      position: 'sticky',
                      top: '0',
                      zIndex: '10',
                      textAlign: 'center'
                    },
                    cell: {
                      width: '120px',
                      height: '100px',
                      minWidth: '120px',
                      maxWidth: '120px',
                      minHeight: '100px',
                      maxHeight: '100px',
                      fontSize: '12px',
                      padding: '2px',
                      borderRight: '1px solid #e2e8f0',
                      borderBottom: '1px solid #e2e8f0',
                      borderLeft: '1px solid #e2e8f0',
                      backgroundColor: '#ffffff',
                      position: 'relative',
                      verticalAlign: 'top',
                      overflow: 'hidden',
                      boxSizing: 'border-box'
                    },
                    day: {
                      borderRadius: '8px',
                      transition: 'all 0.2s ease-in-out',
                      width: '100%',
                      height: '96px',
                      maxHeight: '96px',
                      display: 'flex',
                      alignItems: 'flex-start',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      position: 'relative',
                      backgroundColor: 'transparent',
                      border: 'none',
                      color: '#374151',
                      fontSize: '12px',
                      flexDirection: 'column',
                      padding: '2px',
                      boxSizing: 'border-box',
                      overflow: 'hidden'
                    },
                    table: {
                      width: '100%',
                      maxWidth: '100%',
                      borderCollapse: 'separate',
                      borderSpacing: '0',
                      borderRadius: '16px',
                      overflow: 'hidden',
                      backgroundColor: '#ffffff'
                    },
                    months: {
                      width: '100%'
                    },
                    month: {
                      width: '100%'
                    },
                    caption: {
                      display: 'none'
                    },
                    caption_label: {
                      display: 'none'
                    }
                  }}
                />
              </div>
            )}

            {/* 캘린더 범례 */}
            {/* <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium mb-3 text-gray-700">캘린더 사용법</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-blue-500 rounded border-2 border-blue-700" />
                  <span>오늘 날짜</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-500 rounded" />
                  <span>완전한 식단</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-amber-500 rounded" />
                  <span>부분적 식단</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="bg-green-500 rounded-full w-4 h-4 flex items-center justify-center">
                    <span className="text-white text-xs font-bold">✓</span>
                  </div>
                  <span>섭취 완료</span>
                </div>
              </div>
            </div> */}
          </CardContent>
        </Card>

        {/* 선택된 날짜의 식단 */}
        <Card className="lg:col-span-1 border border-gray-200">
          <CardHeader className="pb-4 h-[88px]">
            <CardTitle className="flex items-center text-xl font-bold">
              <CalendarToday sx={{ fontSize: 24, mr: 1.5, color: 'green.600' }} />
              {selectedDate ? format(selectedDate, 'M월 d일', { locale: ko }) : '오늘의'} 식단
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pt-0">
            {selectedDate ? (() => {
              const selectedMeal = getMealForDate(selectedDate)
              const meals = [
                { key: 'breakfast', label: '아침', icon: '🌅' },
                { key: 'lunch', label: '점심', icon: '☀️' },
                { key: 'dinner', label: '저녁', icon: '🌙' },
                { key: 'snack', label: '간식', icon: '🍎' }
              ]

              return meals.map((meal) => (
                <div
                  key={meal.key}
                  className="border border-gray-200 rounded-lg p-3 cursor-pointer bg-white hover:bg-gray-50 transition-all duration-200"
                  onClick={() => handleOpenModal(meal.key)}
                >
                  <div className="flex justify-between items-center">
                    <h4 className="font-semibold flex items-center gap-2 text-gray-800">
                      <span className="text-lg">{meal.icon}</span>
                      {meal.label}
                    </h4>
                    <div className="w-6 h-6 rounded-full bg-green-100 hover:bg-green-200 flex items-center justify-center transition-colors">
                      <Add sx={{ fontSize: 14, color: 'green.600' }} />
                    </div>
                  </div>
                  <div className="text-xs text-gray-600 mt-1 ml-8">
                    {(() => {
                      const mealText = getMealText(selectedMeal, meal.key);
                      return mealText.trim() !== '' ? mealText : '계획된 식단이 없습니다';
                    })()}
                  </div>
                </div>
              ))
            })() : (
              <div className="text-center text-gray-500 py-8 text-sm">
                날짜를 선택하면 해당 날의 식단을 볼 수 있습니다
              </div>
            )}

            {/* 일수 선택 옵션 */}
            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                생성할 일수
              </label>
              <select
                value={selectedDays}
                onChange={(e) => setSelectedDays(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
                disabled={isGeneratingMealPlan}
              >
                <option value={3}>3일</option>
                <option value={7}>7일</option>
                <option value={14}>14일</option>
                <option value={30}>30일</option>
              </select>
            </div>

            <Button
              className="w-full bg-green-500 hover:bg-green-600 text-white font-medium py-2 rounded-lg transition-colors"
              onClick={handleGenerateMealPlan}
              disabled={isGeneratingMealPlan}
            >
              {isGeneratingMealPlan ? '생성 중...' : 'AI 식단표 생성'}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* 최근 활동 */}
      <Card className="border border-gray-200 bg-gradient-to-br from-white to-blue-50/30">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center text-xl font-bold">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mr-3">
              <BarChart className="h-5 w-5 text-white" />
            </div>
            최근 활동
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { date: '오늘', action: '점심 식단 완료', status: 'completed', icon: '✅' },
              { date: '어제', action: '저녁 식단 스킵', status: 'skipped', icon: '⏭️' },
              { date: '2일 전', action: '7일 식단표 생성', status: 'planned', icon: '📋' },
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-4 rounded-xl bg-white/60 border border-gray-200 transition-all duration-300">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <span className="text-2xl flex-shrink-0">{activity.icon}</span>
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold text-gray-800 truncate">{activity.action}</div>
                    <div className="text-sm text-gray-500">{activity.date}</div>
                  </div>
                </div>
                <div className={`text-sm px-3 py-1 rounded-full font-medium flex-shrink-0 ${activity.status === 'completed' ? 'bg-green-100 text-green-700 border border-green-200' :
                  activity.status === 'skipped' ? 'bg-red-100 text-red-700 border border-red-200' :
                    'bg-blue-100 text-blue-700 border border-blue-200'
                  }`}>
                  {activity.status === 'completed' ? '완료' :
                    activity.status === 'skipped' ? '스킵' : '계획'}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 식단 모달 */}
      {selectedDate && (
        <MealModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          selectedDate={selectedDate}
          mealData={getMealForDate(selectedDate)}
          onSave={handleSaveMeal}
          selectedMealType={selectedMealType}
        />
      )}

      {/* 날짜 상세 모달 */}
      {clickedDate && (
        <DateDetailModal
          isOpen={isDateDetailModalOpen}
          onClose={handleCloseDateDetailModal}
          selectedDate={clickedDate}
          mealData={getMealForDate(clickedDate)}
          onSaveMeal={handleSaveMeal}
          onToggleComplete={toggleMealCheck}
          isMealChecked={isMealChecked}
          onDeleteMeal={handleDeleteMeal}
          onDeleteAllMeals={handleDeleteAllMeals}
        />
      )}

      {/* AI 생성 식단표 저장 모달 */}
      {showMealPlanSaveModal && generatedMealPlan && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                  <span className="text-3xl">🤖</span>
                  AI 생성 식단표 미리보기
                  <span className="text-lg font-normal text-gray-500">
                    ({Object.keys(generatedMealPlan).length}일)
                  </span>
                </h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCloseMealPlanSaveModal}
                  className="hover:bg-gray-100"
                  disabled={isGeneratingMealPlan || isSavingMealPlan}
                >
                  <Close sx={{ fontSize: 20 }} />
                </Button>
              </div>
              <div className="flex items-center justify-between mt-3">
                <p className="text-gray-600">
                  생성된 식단표를 확인하고 캘린더에 저장하세요.
                </p>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">더 필요하신가요?</span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleGenerateMoreDays(3)}
                    disabled={isGeneratingMealPlan || isSavingMealPlan}
                    className="text-xs border-green-300 text-green-700 hover:bg-green-50 disabled:opacity-50"
                  >
                    {isGeneratingMealPlan ? '생성중...' : '+3일'}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleGenerateMoreDays(7)}
                    disabled={isGeneratingMealPlan || isSavingMealPlan}
                    className="text-xs border-green-300 text-green-700 hover:bg-green-50 disabled:opacity-50"
                  >
                    {isGeneratingMealPlan ? '생성중...' : '+7일'}
                  </Button>
                </div>
              </div>
            </div>

            <div className="p-6">
              <div className="grid gap-4">
                {Object.entries(generatedMealPlan).map(([dateString, mealData]) => (
                  <div key={dateString} className="border border-gray-200 rounded-xl p-4 bg-gray-50">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                      <CalendarToday sx={{ fontSize: 20, color: 'green.600' }} />
                      {format(new Date(dateString), 'M월 d일 (EEE)', { locale: ko })}
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                      {[
                        { key: 'breakfast', label: '아침', icon: '🌅' },
                        { key: 'lunch', label: '점심', icon: '☀️' },
                        { key: 'dinner', label: '저녁', icon: '🌙' },
                        { key: 'snack', label: '간식', icon: '🍎' }
                      ].map((meal) => (
                        <div key={meal.key} className="bg-white p-3 rounded-lg border border-gray-100">
                          <div className="font-medium text-green-700 text-sm flex items-center gap-1 mb-1">
                            <span>{meal.icon}</span>
                            {meal.label}
                          </div>
                          <div className="text-sm text-gray-600">
                            {mealData[meal.key as keyof MealData] || '없음'}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-3 mt-6 pt-4 border-t border-gray-200">
                <Button
                  onClick={handleSaveGeneratedMealPlan}
                  disabled={isSavingMealPlan}
                  className="flex-1 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {isSavingMealPlan ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></div>
                      저장 중...
                    </>
                  ) : (
                    <>
                      <Save sx={{ fontSize: 20, mr: 1 }} />
                      캘린더에 저장하기
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleCloseMealPlanSaveModal}
                  disabled={isSavingMealPlan}
                  className="flex-1 py-3 rounded-xl border-2 border-gray-300 hover:bg-gray-50 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  취소
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
