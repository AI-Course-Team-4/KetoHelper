import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Calendar, Download, Plus, BarChart } from 'lucide-react'

export function CalendarPage() {
  const [selectedDate, setSelectedDate] = useState(new Date())

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
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Calendar className="h-5 w-5 mr-2" />
              월간 캘린더
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-96 bg-muted rounded-lg flex items-center justify-center">
              <div className="text-center">
                <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                <p className="text-muted-foreground">
                  react-day-picker 캘린더가 여기에 표시됩니다
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  날짜별 식단 계획 및 기록
                </p>
              </div>
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
