import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CalendarToday, ChevronLeft, ChevronRight } from '@mui/icons-material'
import { DayPicker } from 'react-day-picker'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import 'react-day-picker/dist/style.css'
import { CalendarDay } from './CalendarDay'
import { MealData } from '@/data/ketoMeals'

interface CalendarGridProps {
  currentMonth: Date
  selectedDate: Date | undefined
  mealData: Record<string, MealData>
  isLoading: boolean
  isLoadingOverlay?: boolean
  error: any
  fetchingPlans?: number
  onDateSelect: (date: Date | undefined) => void
  onMonthChange: (month: Date) => void
  onDateClick: (date: Date) => void
  getMealForDate: (date: Date) => MealData | null
  isMealChecked: (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => boolean
  isOptimisticMeal?: (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => boolean
  onToggleMealCheck: (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => void
}

export function CalendarGrid({
  currentMonth,
  selectedDate,
  mealData,
  isLoading,
  isLoadingOverlay,
  error,
  fetchingPlans = 0,
  onDateSelect,
  onMonthChange,
  onDateClick,
  getMealForDate,
  isMealChecked,
  isOptimisticMeal,
  onToggleMealCheck
}: CalendarGridProps) {
  // 디버깅: 오버레이 로딩 상태 확인
  console.log('🔍 CalendarGrid 오버레이 상태:', {
    isLoadingOverlay,
    isLoading,
    timestamp: new Date().toISOString()
  })
  
  return (
    <Card className="lg:col-span-3 border border-gray-200 relative">
      {/* 오버레이 로딩 - 캘린더 전체 덮어씌우기 */}
      {isLoadingOverlay && (
        <div className="absolute inset-0 bg-white/90 backdrop-blur-sm z-50 flex items-center justify-center h-[600px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-2"></div>
            <p className="text-gray-600 font-medium">업데이트 중...</p>
          </div>
        </div>
      )}
      
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
              onClick={() => onMonthChange(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
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
              onClick={() => onMonthChange(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
              className="hover:bg-green-50 hover:border-green-300"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6 pt-0">
                {isLoading && (
                    <div className="flex items-center justify-center h-[600px] w-full">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-2"></div>
                        <p className="text-gray-600 font-medium">캘린더 데이터를 불러오는 중...</p>
                        <p className="text-sm text-gray-500 mt-1">잠시만 기다려주세요</p>
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
                   <div className="calendar-container w-full flex items-start justify-center overflow-x-auto relative">
                     <DayPicker
              mode="single"
              selected={selectedDate}
              onSelect={onDateSelect}
              month={currentMonth}
              onMonthChange={onMonthChange}
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
                today: new Date()
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
                  return (
                    <CalendarDay
                      date={date}
                      displayMonth={displayMonth}
                      meal={meal}
                      isMealChecked={isMealChecked}
                      isOptimisticMeal={isOptimisticMeal}
                      onDateClick={onDateClick}
                      onToggleMealCheck={onToggleMealCheck}
                    />
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
      </CardContent>
    </Card>
  )
}
