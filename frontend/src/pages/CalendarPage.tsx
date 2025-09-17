import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Calendar, Download, Plus, BarChart, ChevronLeft, ChevronRight } from 'lucide-react'
import { DayPicker } from 'react-day-picker'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import 'react-day-picker/dist/style.css'
import { MealData, generateRandomMeal } from '@/data/ketoMeals'
import { MealModal } from '@/components/MealModal'

export function CalendarPage() {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date())
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [mealData, setMealData] = useState<Record<string, MealData>>({
    '2024-01-15': { breakfast: '아보카도 토스트', lunch: '그릴 치킨 샐러드', dinner: '연어 스테이크' },
    '2024-01-16': { breakfast: '계란 스크램블', lunch: '불고기', dinner: '새우볶음밥' },
    '2024-01-17': { breakfast: '베이컨 에그', lunch: '스테이크', dinner: '생선구이' },
  })
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleDateSelect = (date: Date | undefined) => {
    setSelectedDate(date)
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
  const handleOpenModal = () => {
    setIsModalOpen(true)
  }

  // 모달 닫기 핸들러
  const handleCloseModal = () => {
    setIsModalOpen(false)
  }

  // 식단 저장 핸들러
  const handleSaveMeal = (date: Date, newMealData: MealData) => {
    const dateKey = formatDateKey(date)
    setMealData(prev => ({
      ...prev,
      [dateKey]: newMealData
    }))
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gradient">식단 캘린더</h1>
          <p className="text-muted-foreground mt-1">
            키토 식단 계획을 관리하고 기록하세요
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            ICS 내보내기
          </Button>
          <Button onClick={handleGenerateMealPlan}>
            <Plus className="h-4 w-4 mr-2" />
            식단표 생성
          </Button>
        </div>
      </div>

      {/* 주간 통계 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-600">85%</div>
            <div className="text-sm text-muted-foreground">이행률</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-orange-600">22g</div>
            <div className="text-sm text-muted-foreground">평균 탄수화물</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-blue-600">1,650</div>
            <div className="text-sm text-muted-foreground">평균 칼로리</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-purple-600">30%</div>
            <div className="text-sm text-muted-foreground">외식 비중</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 캘린더 */}
        <Card className="lg:col-span-2 min-h-[700px]">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center">
                <Calendar className="h-5 w-5 mr-2" />
                월간 캘린더
              </CardTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm font-medium min-w-[120px] text-center">
                  {format(currentMonth, 'yyyy년 M월', { locale: ko })}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6 pt-0 -mt-24">
            <div className="calendar-container w-full h-[700px] flex items-center justify-center">
              <DayPicker
                mode="single"
                selected={selectedDate}
                onSelect={handleDateSelect}
                month={currentMonth}
                onMonthChange={handleMonthChange}
                locale={ko}
                className="rdp-custom w-full"
                modifiers={{
                  hasMeal: Object.keys(mealData).map(date => new Date(date))
                }}
                modifiersStyles={{
                  hasMeal: {
                    backgroundColor: '#10b981',
                    color: 'white',
                    fontWeight: 'bold',
                    borderRadius: '12px',
                    boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)'
                  }
                }}
                components={{
                  Day: ({ date, displayMonth }) => {
                    const meal = getMealForDate(date)
                    const isCurrentMonth = date.getMonth() === displayMonth.getMonth()
                    
                    return (
                      <div className="relative w-full h-full flex flex-col">
                        {isCurrentMonth && (
                          <div className="text-sm font-medium text-center py-1">
                            {date.getDate()}
                          </div>
                        )}
                        {meal && isCurrentMonth && (
                          <div className="flex-1 px-1 pb-1">
                            <div className="text-xs text-gray-600 truncate" title={meal.breakfast}>
                              🌅 {meal.breakfast}
                            </div>
                            <div className="text-xs text-gray-600 truncate" title={meal.lunch}>
                              ☀️ {meal.lunch}
                            </div>
                            <div className="text-xs text-gray-600 truncate" title={meal.dinner}>
                              🌙 {meal.dinner}
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  }
                }}
                 styles={{
                   head_cell: {
                     width: '70px',
                     height: '60px',
                     fontSize: '14px',
                     color: '#374151',
                     textTransform: 'uppercase',
                     letterSpacing: '0.8px',
                     backgroundColor: '#f8fafc',
                     borderRight: '1px solid #e2e8f0',
                     borderBottom: '2px solid #e2e8f0',
                     borderTop: '1px solid #e2e8f0',
                     borderLeft: '1px solid #e2e8f0'
                   },
                   cell: {
                     width: '70px',
                     height: '70px',
                     fontSize: '15px',
                     padding: '4px',
                     borderRight: '1px solid #e2e8f0',
                     borderBottom: '1px solid #e2e8f0',
                     borderLeft: '1px solid #e2e8f0',
                     backgroundColor: '#ffffff',
                     position: 'relative'
                   },
                   day: {
                     borderRadius: '12px',
                     transition: 'all 0.2s ease-in-out',
                     width: '62px',
                     height: '62px',
                     display: 'flex',
                     alignItems: 'center',
                     justifyContent: 'center',
                     cursor: 'pointer',
                     position: 'relative',
                     backgroundColor: 'transparent',
                     border: 'none',
                     color: '#374151',
                     fontSize: '15px'
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
          </CardContent>
        </Card>

        {/* 선택된 날짜의 식단 */}
        <Card>
          <CardHeader>
            <CardTitle>
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
                <div key={meal.key} className="border rounded-lg p-3">
                  <div className="flex justify-between items-center">
                    <h4 className="font-medium flex items-center gap-2">
                      <span>{meal.icon}</span>
                      {meal.label}
                    </h4>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={handleOpenModal}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">
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
            
            <Button className="w-full" onClick={handleGenerateMealPlan}>
              AI 식단표 생성
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* 최근 활동 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart className="h-5 w-5 mr-2" />
            최근 활동
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { date: '오늘', action: '점심 식단 완료', status: 'completed' },
              { date: '어제', action: '저녁 식단 스킵', status: 'skipped' },
              { date: '2일 전', action: '7일 식단표 생성', status: 'planned' },
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between py-2 border-b">
                <div>
                  <div className="font-medium">{activity.action}</div>
                  <div className="text-sm text-muted-foreground">{activity.date}</div>
                </div>
                <div className={`text-sm px-2 py-1 rounded ${
                  activity.status === 'completed' ? 'bg-green-100 text-green-800' :
                  activity.status === 'skipped' ? 'bg-red-100 text-red-800' :
                  'bg-blue-100 text-blue-800'
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
        />
      )}
    </div>
  )
}
