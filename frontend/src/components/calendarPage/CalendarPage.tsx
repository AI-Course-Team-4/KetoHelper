import { useState } from 'react'
import { CalendarHeader } from './CalendarHeader'
import { CalendarGrid } from './CalendarGrid'
import { SelectedDateMeals } from './SelectedDateMeals'
import { RecentActivity } from './RecentActivity'
import { MealModal } from '@/components/MealModal'
import { DateDetailModal } from '@/components/DateDetailModal'
import { useCalendarData } from './hooks/useCalendarData'
import { useMealOperations } from './hooks/useMealOperations'
import { useMealPlanGeneration } from './hooks/useMealPlanGeneration'

export function CalendarPage() {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date())
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedMealType, setSelectedMealType] = useState<string | null>(null)
  const [isDateDetailModalOpen, setIsDateDetailModalOpen] = useState(false)
  const [clickedDate, setClickedDate] = useState<Date | null>(null)

  // 훅들 사용
  const {
    mealData,
    planIds,
    isLoading,
    error,
    getMealForDate,
    toggleMealCheck,
    isMealChecked
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

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <CalendarHeader
        selectedDays={selectedDays}
        setSelectedDays={setSelectedDays}
        isGeneratingMealPlan={isGeneratingMealPlan}
        onGenerateMealPlan={handleGenerateMealPlan}
      />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 캘린더 */}
        <CalendarGrid
          currentMonth={currentMonth}
          selectedDate={selectedDate}
          mealData={mealData}
          isLoading={isLoading}
          error={error}
          onDateSelect={handleDateSelect}
          onMonthChange={handleMonthChange}
          onDateClick={handleDateClick}
          getMealForDate={getMealForDate}
          isMealChecked={isMealChecked}
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
