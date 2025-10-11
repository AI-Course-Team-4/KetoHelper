import { useEffect, useState } from 'react'
import { useIsFetching } from '@tanstack/react-query'
import { useCalendarJobWatcher } from '@/hooks/useCalendarJobWatcher'
import { CalendarHeader } from './CalendarHeader'
import { CalendarGrid } from './CalendarGrid'
import { SelectedDateMeals } from './SelectedDateMeals'
import { RecentActivity } from './RecentActivity'
import { MealModal } from '@/components/MealModal'
import { DateDetailModal } from '@/components/DateDetailModal'
import { useCalendarData } from './hooks/useCalendarData'
import { useMealOperations } from './hooks/useMealOperations'
import { useMealPlanGeneration } from './hooks/useMealPlanGeneration'
import { useDeleteAllPlans } from '@/hooks/useApi'
import { useAuthStore } from '@/store/authStore'
import { useCalendarStore } from '@/store/calendarStore'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'

export function CalendarPage() {
  // 저장 상태 워처 연결: 페이지 활성 시에만 폴링
  useCalendarJobWatcher()
  const queryClient = useQueryClient()
  
  // 캘린더 진입 시 항상 최신 데이터로 리로드 (확실한 일관성 보장)
  useEffect(() => {
    console.log('🔍 CalendarPage 초기 리로드')
    try {
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })
      queryClient.refetchQueries({ queryKey: ['plans-range'] })
    } catch (e) {
      console.warn('plans-range 초기 리로드 실패:', e)
    }
  }, [])

  // plans-range가 네트워크에서 진행 중인지 전역 감지
  const fetchingPlans = useIsFetching({ queryKey: ['plans-range'] })
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date())
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedMealType, setSelectedMealType] = useState<string | null>(null)
  const [isDateDetailModalOpen, setIsDateDetailModalOpen] = useState(false)
  const [clickedDate, setClickedDate] = useState<Date | null>(null)

  const { user } = useAuthStore()
  const { clearSaveState } = useCalendarStore()
  const deleteAllPlansMutation = useDeleteAllPlans()

  // 훅들 사용
  const {
    mealData,
    planIds,
    isLoading,
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

  const {
    selectedDays,
    setSelectedDays,
    isGeneratingMealPlan,
    handleGenerateMealPlan
  } = useMealPlanGeneration()

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

  const handleOpenModal = (mealType?: string) => {
    setSelectedMealType(mealType || null)
    setIsModalOpen(true)
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

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <CalendarHeader
        selectedDays={selectedDays}
        setSelectedDays={setSelectedDays}
        isGeneratingMealPlan={isGeneratingMealPlan}
        onGenerateMealPlan={handleGenerateMealPlan}
        onDeleteAllPlans={handleDeleteAllPlans}
        isDeletingAll={deleteAllPlansMutation.isPending}
      />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 캘린더 */}
                <CalendarGrid
                  currentMonth={currentMonth}
                  selectedDate={selectedDate}
                  mealData={mealData}
                   isLoading={isLoading}
                  error={error}
                  fetchingPlans={fetchingPlans}
                  onDateSelect={handleDateSelect}
                  onMonthChange={handleMonthChange}
                  onDateClick={handleDateClick}
                  getMealForDate={getMealForDate}
                  isMealChecked={isMealChecked}
                  isOptimisticMeal={isOptimisticMeal}
                  onToggleMealCheck={toggleMealCheck}
                />

        {/* 선택된 날짜의 식단 */}
        <SelectedDateMeals
          selectedDate={selectedDate}
          getMealForDate={getMealForDate}
          onOpenModal={handleOpenModal}
        />
      </div>

      {/* 최근 활동 */}
      <RecentActivity />

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
