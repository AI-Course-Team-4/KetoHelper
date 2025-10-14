import { useEffect, useState } from 'react'
import { useCalendarJobWatcher } from '@/hooks/useCalendarJobWatcher'
import { CalendarHeader } from './CalendarHeader'
import { CalendarGrid } from './CalendarGrid'
import { MealModal } from '@/components/MealModal'
import { DateDetailModal } from '@/components/DateDetailModal'
import { useCalendarData } from './hooks/useCalendarData'
import { useMealOperations } from './hooks/useMealOperations'
import { useDeleteAllPlans, useDeleteMonthPlans } from '@/hooks/useApi'
import { useAuthStore } from '@/store/authStore'
import { useCalendarStore } from '@/store/calendarStore'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'

export function CalendarPage() {
  // 저장 상태 워처 연결: 페이지 활성 시에만 폴링
  useCalendarJobWatcher()
  const queryClient = useQueryClient()
  
  // 캘린더 진입 시 스마트 리로드 (캐시된 데이터가 있으면 사용)
  useEffect(() => {
    console.log('🔍 CalendarPage 스마트 리로드')
    try {
      // plans-range 쿼리들이 캐시되어 있는지 확인
      const queryCache = queryClient.getQueryCache()
      const plansRangeQueries = queryCache.findAll({ queryKey: ['plans-range'] })
      
      // 캐시된 데이터가 있고 신선한 상태인지 확인
      const hasFreshData = plansRangeQueries.some(query => {
        const state = query.state
        const now = Date.now()
        const staleTime = 5 * 60 * 1000 // 5분
        return state.data && state.dataUpdatedAt > now - staleTime // 5분 이내
      })
      
      if (hasFreshData) {
        console.log(`✅ 신선한 plans-range 캐시 발견 - API 요청 생략`)
        return
      }
      
      // 캐시된 데이터가 없거나 오래된 경우에만 리페치
      console.log('⚠️ plans-range 캐시 없음 또는 오래됨 - API 요청 실행')
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })
      queryClient.refetchQueries({ queryKey: ['plans-range'] })
    } catch (e) {
      console.warn('plans-range 초기 리로드 실패:', e)
    }
  }, [])

  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date())
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedMealType, setSelectedMealType] = useState<string | null>(null)
  const [isDateDetailModalOpen, setIsDateDetailModalOpen] = useState(false)
  const [clickedDate, setClickedDate] = useState<Date | null>(null)

  const { user } = useAuthStore()
  const { clearSaveState } = useCalendarStore()
  const deleteAllPlansMutation = useDeleteAllPlans()
  const deleteMonthPlansMutation = useDeleteMonthPlans()

  // 훅들 사용
  const {
    mealData,
    planIds,
    isLoading,
    isLoadingOverlay,
    error,
    getMealForDate,
    toggleMealCheck,
    isMealChecked,
    isOptimisticMeal
  } = useCalendarData(currentMonth)

  const {
    handleSaveMeal,
    handleDeleteMeal,
    handleDeleteAllMeals
  } = useMealOperations()

  // AI 식단표 생성/기간 선택 제거

  // 이벤트 핸들러들
  const handleDateSelect = (date: Date | undefined) => {
    setSelectedDate(date)
  }

  const handleDateClick = (date: Date) => {
    setClickedDate(date)
    setIsDateDetailModalOpen(true)
  }

  const handleMonthChange = (month: Date) => {
    setCurrentMonth(month)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedMealType(null)
  }

  const handleCloseDateDetailModal = () => {
    setIsDateDetailModalOpen(false)
    setClickedDate(null)
  }

  // 전체 삭제 핸들러
  const handleDeleteAllPlans = async () => {
    if (!user?.id) {
      toast.error('로그인이 필요합니다')
      return
    }

    // 확인 대화상자
    const confirmed = window.confirm(
      '⚠️ 정말로 모든 식단 계획을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.'
    )
    
    if (!confirmed) return

    try {
      const result = await deleteAllPlansMutation.mutateAsync(user.id)
      
      // Optimistic 데이터도 정리
      clearSaveState()
      
      // 🚀 React Query 캐시 무효화 (페이지 새로고침 없이)
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })
      queryClient.invalidateQueries({ queryKey: ['plans'] })
      queryClient.invalidateQueries({ queryKey: ['meal-log'] })
      
      // 강제로 데이터 다시 가져오기
      await queryClient.refetchQueries({ queryKey: ['plans-range'] })
      
      toast.success(result.message || '모든 식단 계획이 삭제되었습니다')
      
    } catch (error) {
      console.error('전체 삭제 실패:', error)
      toast.error('삭제 중 오류가 발생했습니다')
    }
  }

  // 월별 삭제 핸들러
  const handleDeleteMonthPlans = async () => {
    if (!user?.id) {
      toast.error('로그인이 필요합니다')
      return
    }

    const year = currentMonth.getFullYear()
    const month = currentMonth.getMonth() + 1 // getMonth()는 0-based

    // 확인 대화상자
    const confirmed = window.confirm(
      `⚠️ ${year}년 ${month}월의 모든 식단 계획을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`
    )
    
    if (!confirmed) return

    try {
      const result = await deleteMonthPlansMutation.mutateAsync({
        userId: user.id,
        year,
        month
      })
      
      // Optimistic 데이터도 정리
      clearSaveState()
      
      // 🚀 React Query 캐시 무효화 (페이지 새로고침 없이)
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })
      queryClient.invalidateQueries({ queryKey: ['plans'] })
      queryClient.invalidateQueries({ queryKey: ['meal-log'] })
      
      // 강제로 데이터 다시 가져오기
      await queryClient.refetchQueries({ queryKey: ['plans-range'] })
      
      toast.success(result.message || `${year}년 ${month}월의 식단 계획이 삭제되었습니다`)
      
    } catch (error) {
      console.error('월별 삭제 실패:', error)
      toast.error('삭제 중 오류가 발생했습니다')
    }
  }

  return (
    <div className="space-y-1">
      {/* 헤더 */}
      <CalendarHeader
        onDeleteAllPlans={handleDeleteAllPlans}
        onDeleteMonthPlans={handleDeleteMonthPlans}
        isDeletingAll={deleteAllPlansMutation.isPending}
        isDeletingMonth={deleteMonthPlansMutation.isPending}
        currentMonth={currentMonth}
        onMonthChange={handleMonthChange}
      />

      {/* 캘린더를 독립적인 컨테이너로 분리 */}
      <div className="w-full">
        <CalendarGrid
          currentMonth={currentMonth}
          selectedDate={selectedDate}
          mealData={mealData}
          isLoading={isLoading}
          isLoadingOverlay={isLoadingOverlay}
          error={error}
          onDateSelect={handleDateSelect}
          onMonthChange={handleMonthChange}
          onDateClick={handleDateClick}
          getMealForDate={getMealForDate}
          isMealChecked={isMealChecked}
          isOptimisticMeal={isOptimisticMeal}
          onToggleMealCheck={toggleMealCheck}
        />
      </div>
      {/* 식단 모달 */}
      {selectedDate && (
        <MealModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          selectedDate={selectedDate}
          mealData={getMealForDate(selectedDate)}
          onSave={(date, mealData) => handleSaveMeal(date, mealData, planIds)}
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
          onSaveMeal={(date, mealData) => handleSaveMeal(date, mealData, planIds)}
          onToggleComplete={toggleMealCheck}
          isMealChecked={isMealChecked}
          onDeleteMeal={(date, mealType) => handleDeleteMeal(date, mealType, planIds)}
          onDeleteAllMeals={(date) => handleDeleteAllMeals(date, planIds)}
        />
      )}
    </div>
  )
}
