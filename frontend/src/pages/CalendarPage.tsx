import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CalendarToday, Add, BarChart, ChevronLeft, ChevronRight } from '@mui/icons-material'
import { DayPicker } from 'react-day-picker'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import 'react-day-picker/dist/style.css'
import { MealData, generateRandomMeal } from '@/data/ketoMeals'
import { MealModal } from '@/components/MealModal'
import { DateDetailModal } from '@/components/DateDetailModal'

export function CalendarPage() {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date())
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [mealData, setMealData] = useState<Record<string, MealData>>({})
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedMealType, setSelectedMealType] = useState<string | null>(null)
  const [isDateDetailModalOpen, setIsDateDetailModalOpen] = useState(false)
  const [clickedDate, setClickedDate] = useState<Date | null>(null)
  // 체크 상태만을 위한 로컬 state (UI용)
  const [mealCheckState, setMealCheckState] = useState<Record<string, {
    breakfastCompleted?: boolean
    lunchCompleted?: boolean
    dinnerCompleted?: boolean
    snackCompleted?: boolean
  }>>({})

  // 컴포넌트 마운트 시 샘플 데이터 로드
  useEffect(() => {
    loadSampleMealData(currentMonth)
  }, [currentMonth])

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

  // 식단 생성 버튼 클릭 핸들러
  const handleGenerateMealPlan = () => {
    const newMealData = { ...mealData }
    
    // 현재 월의 모든 날짜에 랜덤 식단 생성
    const year = currentMonth.getFullYear()
    const month = currentMonth.getMonth()
    const daysInMonth = new Date(year, month + 1, 0).getDate()
    
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day)
      const dateString = format(date, 'yyyy-MM-dd')
      
      // 모든 날짜에 식단 생성
      newMealData[dateString] = generateRandomMeal()
    }
    
    setMealData(newMealData)
  }

  // 날짜 문자열로 변환하는 헬퍼 함수
  const formatDateKey = (date: Date) => format(date, 'yyyy-MM-dd')

  // 특정 날짜의 식단 정보 가져오기
  const getMealForDate = (date: Date) => {
    const dateKey = formatDateKey(date)
    return mealData[dateKey] || null
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

  // 간단한 체크 토글 함수 (로컬 UI만)
  const toggleMealCheck = (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => {
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
  }

  // 체크 상태 확인 함수
  const isMealChecked = (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => {
    const dateKey = formatDateKey(date)
    const checkState = mealCheckState[dateKey]
    
    if (!checkState) return false
    
    if (mealType === 'breakfast') return checkState.breakfastCompleted || false
    else if (mealType === 'lunch') return checkState.lunchCompleted || false
    else if (mealType === 'dinner') return checkState.dinnerCompleted || false
    else if (mealType === 'snack') return checkState.snackCompleted || false
    
    return false
  }

  // 간단한 로컬 저장 (UI 테스트용)
  const handleSaveMeal = (date: Date, newMealData: MealData) => {
    console.log('💾 로컬 저장:', { date, newMealData })
    
    const dateKey = formatDateKey(date)
    setMealData(prev => ({
      ...prev,
      [dateKey]: newMealData
    }))
    
    console.log('✅ 로컬 저장 완료!')
  }

  // UI 테스트 모드 (로그인 불필요)

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-green-500 via-emerald-500 to-teal-600 text-white">
        <div className="absolute inset-0 bg-white/10 backdrop-blur-sm" />
        <div className="relative p-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-4xl font-bold mb-2">🥑 식단 캘린더</h1>
              <p className="text-green-100 text-lg">
                키토 식단 계획을 스마트하게 관리하고 기록하세요
              </p>
            </div>
            
            <div className="flex gap-3">
              <Button 
                onClick={handleGenerateMealPlan}
                className="bg-white/20 hover:bg-white/30 text-white border-white/30 backdrop-blur-sm shadow-lg"
                variant="outline"
              >
                <Add sx={{ fontSize: 20, mr: 1 }} />
                AI 식단표 생성
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* 주간 통계 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="border-0 shadow-lg bg-gradient-to-br from-green-50 to-emerald-50 hover:shadow-xl transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-green-600">85%</div>
                <div className="text-sm font-medium text-green-700 mt-1">이행률</div>
              </div>
              <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                <BarChart className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-0 shadow-lg bg-gradient-to-br from-orange-50 to-amber-50 hover:shadow-xl transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-orange-600">22g</div>
                <div className="text-sm font-medium text-orange-700 mt-1">평균 탄수화물</div>
              </div>
              <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-lg">C</span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-50 to-cyan-50 hover:shadow-xl transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-blue-600">1,650</div>
                <div className="text-sm font-medium text-blue-700 mt-1">평균 칼로리</div>
              </div>
              <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white text-2xl">🔥</span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-0 shadow-lg bg-gradient-to-br from-purple-50 to-violet-50 hover:shadow-xl transition-all duration-300">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-purple-600">30%</div>
                <div className="text-sm font-medium text-purple-700 mt-1">외식 비중</div>
              </div>
              <div className="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white text-2xl">🍽️</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 캘린더 */}
        <Card className="lg:col-span-2 border-0 shadow-xl bg-white/80 backdrop-blur-sm">
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
                  className="hover:bg-green-50 hover:border-green-300 transition-colors"
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
                  className="hover:bg-green-50 hover:border-green-300 transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6 pt-0">
            <div className="calendar-container w-full flex items-start justify-center">
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
                        className="relative w-full h-full flex flex-col cursor-pointer hover:bg-gray-50 transition-colors rounded-lg"
                        onClick={() => isCurrentMonth && handleDateClick(date)}
                        style={{ minHeight: '80px' }}
                      >
                        {isCurrentMonth && (
                          <div className="date-number w-full flex items-center justify-between px-1">
                            <span>{date.getDate()}</span>
                            {/* 체크된 식사가 있으면 체크 아이콘 표시 */}
                            {checkedCount > 0 && (
                              <div className="absolute -top-1 -right-1 bg-green-500 rounded-full w-4 h-4 flex items-center justify-center">
                                <span className="text-white text-xs font-bold">✓</span>
                              </div>
                            )}
                          </div>
                        )}
                        {meal && isCurrentMonth && (
                          <div className="meal-info-container flex-1 p-1">
                            {meal.breakfast && (
                              <div className="meal-info text-xs flex items-center justify-between group">
                                <span className="truncate mr-1" title={meal.breakfast}>
                                  🌅 {meal.breakfast}
                                </span>
                                <div
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleMealCheck(date, 'breakfast')
                                  }}
                                  className="cursor-pointer opacity-60 group-hover:opacity-100 transition-opacity"
                                >
                                  {isMealChecked(date, 'breakfast') ? (
                                    <span className="text-green-500 text-sm">✅</span>
                                  ) : (
                                    <span className="text-gray-400 text-sm">⭕</span>
                                  )}
                                </div>
                              </div>
                            )}
                            {meal.lunch && (
                              <div className="meal-info text-xs flex items-center justify-between group">
                                <span className="truncate mr-1" title={meal.lunch}>
                                  ☀️ {meal.lunch}
                                </span>
                                <div
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleMealCheck(date, 'lunch')
                                  }}
                                  className="cursor-pointer opacity-60 group-hover:opacity-100 transition-opacity"
                                >
                                  {isMealChecked(date, 'lunch') ? (
                                    <span className="text-green-500 text-sm">✅</span>
                                  ) : (
                                    <span className="text-gray-400 text-sm">⭕</span>
                                  )}
                                </div>
                              </div>
                            )}
                            {meal.dinner && (
                              <div className="meal-info text-xs flex items-center justify-between group">
                                <span className="truncate mr-1" title={meal.dinner}>
                                  🌙 {meal.dinner}
                                </span>
                                <div
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleMealCheck(date, 'dinner')
                                  }}
                                  className="cursor-pointer opacity-60 group-hover:opacity-100 transition-opacity"
                                >
                                  {isMealChecked(date, 'dinner') ? (
                                    <span className="text-green-500 text-sm">✅</span>
                                  ) : (
                                    <span className="text-gray-400 text-sm">⭕</span>
                                  )}
                                </div>
                              </div>
                            )}
                            {meal.snack && (
                              <div className="meal-info text-xs flex items-center justify-between group text-purple-600">
                                <span className="truncate mr-1" title={meal.snack}>
                                  🍎 {meal.snack}
                                </span>
                                <div
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleMealCheck(date, 'snack')
                                  }}
                                  className="cursor-pointer opacity-60 group-hover:opacity-100 transition-opacity"
                                >
                                  {isMealChecked(date, 'snack') ? (
                                    <span className="text-green-500 text-sm">✅</span>
                                  ) : (
                                    <span className="text-gray-400 text-sm">⭕</span>
                                  )}
                                </div>
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
                     width: '70px',
                     height: '50px',
                     fontSize: '14px',
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
                     zIndex: '10'
                   },
                   cell: {
                     width: '70px',
                     minHeight: '80px',
                     fontSize: '15px',
                     padding: '4px',
                     borderRight: '1px solid #e2e8f0',
                     borderBottom: '1px solid #e2e8f0',
                     borderLeft: '1px solid #e2e8f0',
                     backgroundColor: '#ffffff',
                     position: 'relative',
                     verticalAlign: 'top'
                   },
                   day: {
                     borderRadius: '12px',
                     transition: 'all 0.2s ease-in-out',
                     width: '62px',
                     minHeight: '72px',
                     display: 'flex',
                     alignItems: 'flex-start',
                     justifyContent: 'center',
                     cursor: 'pointer',
                     position: 'relative',
                     backgroundColor: 'transparent',
                     border: 'none',
                     color: '#374151',
                     fontSize: '15px',
                     flexDirection: 'column',
                     padding: '4px'
                   },
                   table: {
                     width: '100%',
                     maxWidth: '100%',
                     borderCollapse: 'separate',
                     borderSpacing: '0',
                     borderRadius: '16px',
                     overflow: 'hidden',
                     boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
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
            
            {/* 캘린더 범례 */}
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium mb-3 text-gray-700">캘린더 사용법</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-blue-500 rounded border-2 border-blue-700" />
                  <span>오늘 날짜</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-500 rounded" />
                  <span>완전한 식단 (아침, 점심, 저녁)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-amber-500 rounded" />
                  <span>부분적 식단 (1-2끼)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="bg-green-500 rounded-full w-4 h-4 flex items-center justify-center">
                    <span className="text-white text-xs font-bold">✓</span>
                  </div>
                  <span>섭취 완료된 식단이 있음</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full border-2 border-green-500 bg-green-500 flex items-center justify-center">
                    <span className="text-white font-bold text-xs">✓</span>
                  </div>
                  <span>음식 옆 호버 시 체크 표시</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-purple-600">🍎</span>
                  <span>간식 (완전한 식단 시에만 표시)</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 선택된 날짜의 식단 */}
        <Card className="border-0 shadow-xl bg-gradient-to-br from-white to-green-50/30">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold flex items-center gap-2">
              <span className="text-2xl">📅</span>
              {selectedDate ? format(selectedDate, 'M월 d일', { locale: ko }) : '오늘의'} 식단
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
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
                  className="border-0 rounded-xl p-4 cursor-pointer bg-gradient-to-r from-white to-gray-50 hover:from-green-50 hover:to-emerald-50 hover:shadow-md transition-all duration-300 shadow-sm"
                  onClick={() => handleOpenModal(meal.key)}
                >
                  <div className="flex justify-between items-center">
                    <h4 className="font-semibold flex items-center gap-3 text-gray-800">
                      <span className="text-2xl">{meal.icon}</span>
                      {meal.label}
                    </h4>
                    <div className="w-8 h-8 rounded-full bg-green-100 hover:bg-green-200 flex items-center justify-center transition-colors">
                      <Add sx={{ fontSize: 16, color: 'green.600' }} />
                    </div>
                  </div>
                  <div className="text-sm text-gray-600 mt-2 ml-11">
                    {selectedMeal && selectedMeal[meal.key as keyof MealData] 
                      ? selectedMeal[meal.key as keyof MealData]
                      : '계획된 식단이 없습니다'
                    }
                  </div>
                </div>
              ))
            })() : (
              <div className="text-center text-muted-foreground py-8">
                날짜를 선택하면 해당 날의 식단을 볼 수 있습니다
              </div>
            )}
            
            <Button 
              className="w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300" 
              onClick={handleGenerateMealPlan}
            >
              <span className="mr-2">🤖</span>
              AI 식단표 생성
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* 최근 활동 */}
      <Card className="border-0 shadow-xl bg-gradient-to-br from-white to-blue-50/30">
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
              <div key={index} className="flex items-center justify-between p-4 rounded-xl bg-white/60 border border-gray-100 hover:shadow-md transition-all duration-300">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{activity.icon}</span>
                  <div>
                    <div className="font-semibold text-gray-800">{activity.action}</div>
                    <div className="text-sm text-gray-500">{activity.date}</div>
                  </div>
                </div>
                <div className={`text-sm px-3 py-1 rounded-full font-medium ${
                  activity.status === 'completed' ? 'bg-green-100 text-green-700 border border-green-200' :
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
        />
      )}
    </div>
  )
}
