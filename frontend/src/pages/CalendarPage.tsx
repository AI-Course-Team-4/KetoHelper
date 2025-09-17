import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Calendar, Download, Plus, BarChart, ChevronLeft, ChevronRight } from 'lucide-react'
import { DayPicker } from 'react-day-picker'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import 'react-day-picker/dist/style.css'

export function CalendarPage() {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date())
  const [currentMonth, setCurrentMonth] = useState(new Date())

  // 샘플 식단 데이터 (실제로는 API에서 가져올 데이터)
  const mealData = {
    '2024-01-15': { breakfast: '아보카도 토스트', lunch: '그릴 치킨 샐러드', dinner: '연어 스테이크' },
    '2024-01-16': { breakfast: '계란 스크램블', lunch: '불고기', dinner: '새우볶음밥' },
    '2024-01-17': { breakfast: '베이컨 에그', lunch: '스테이크', dinner: '생선구이' },
  }

  const handleDateSelect = (date: Date | undefined) => {
    setSelectedDate(date)
  }

  const handleMonthChange = (month: Date) => {
    setCurrentMonth(month)
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
          <Button>
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
                styles={{
                  head_cell: {
                    width: '60px',
                    height: '50px',
                    fontSize: '16px',
                    fontWeight: '700',
                    color: '#6b7280',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  },
                  cell: {
                    width: '60px',
                    height: '60px',
                    fontSize: '16px',
                    padding: '8px'
                  },
                  day: {
                    borderRadius: '12px',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    fontWeight: '500',
                    width: '44px',
                    height: '44px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    position: 'relative'
                  },
                  table: {
                    width: '100%',
                    maxWidth: '100%'
                  },
                  months: {
                    width: '100%'
                  },
                  month: {
                    width: '100%'
                  }
                }}
              />
            </div>
          </CardContent>
        </Card>

        {/* 오늘의 식단 */}
        <Card>
          <CardHeader>
            <CardTitle>오늘의 식단</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {['아침', '점심', '저녁', '간식'].map((meal) => (
              <div key={meal} className="border rounded-lg p-3">
                <div className="flex justify-between items-center">
                  <h4 className="font-medium">{meal}</h4>
                  <Button variant="ghost" size="sm">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="text-sm text-muted-foreground mt-1">
                  계획된 식단이 없습니다
                </div>
              </div>
            ))}
            
            <Button className="w-full">
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
    </div>
  )
}
