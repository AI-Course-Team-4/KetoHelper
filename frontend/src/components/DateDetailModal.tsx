import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { X, Plus, Edit, Calendar, Clock, Utensils, Target, TrendingUp } from 'lucide-react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { MealData } from '@/data/ketoMeals'

interface DateDetailModalProps {
  isOpen: boolean
  onClose: () => void
  selectedDate: Date
  mealData: MealData | null
  onSaveMeal: (date: Date, mealData: MealData) => void
}

export function DateDetailModal({ 
  isOpen, 
  onClose, 
  selectedDate, 
  mealData, 
  onSaveMeal 
}: DateDetailModalProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedMealData, setEditedMealData] = useState<MealData>({
    breakfast: mealData?.breakfast || '',
    lunch: mealData?.lunch || '',
    dinner: mealData?.dinner || '',
    snack: mealData?.snack || ''
  })

  const handleSave = () => {
    onSaveMeal(selectedDate, editedMealData)
    setIsEditing(false)
  }

  const handleCancel = () => {
    setEditedMealData({
      breakfast: mealData?.breakfast || '',
      lunch: mealData?.lunch || '',
      dinner: mealData?.dinner || '',
      snack: mealData?.snack || ''
    })
    setIsEditing(false)
  }

  const meals = [
    { key: 'breakfast', label: '아침', icon: '🌅', time: '07:00' },
    { key: 'lunch', label: '점심', icon: '☀️', time: '12:00' },
    { key: 'dinner', label: '저녁', icon: '🌙', time: '18:00' },
    { key: 'snack', label: '간식', icon: '🍎', time: '15:00' }
  ]

  // 키토 점수 계산 (예시)
  const calculateKetoScore = () => {
    if (!mealData) return 0
    const mealCount = Object.values(mealData).filter(meal => meal && meal.trim() !== '').length
    return Math.min(mealCount * 25, 100)
  }

  const ketoScore = calculateKetoScore()

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader className="flex flex-row items-center justify-between">
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            {format(selectedDate, 'yyyy년 M월 d일 (E)', { locale: ko })}
          </DialogTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </DialogHeader>

        <div className="space-y-6">
          {/* 키토 점수 및 통계 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-600">{ketoScore}%</div>
                <div className="text-sm text-muted-foreground">키토 점수</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {Object.values(mealData || {}).filter(meal => meal && meal.trim() !== '').length}
                </div>
                <div className="text-sm text-muted-foreground">계획된 식사</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-purple-600">1,650</div>
                <div className="text-sm text-muted-foreground">예상 칼로리</div>
              </CardContent>
            </Card>
          </div>

          {/* 식단 정보 */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Utensils className="h-5 w-5" />
                식단 계획
              </CardTitle>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setIsEditing(!isEditing)}
              >
                <Edit className="h-4 w-4 mr-2" />
                {isEditing ? '취소' : '편집'}
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {meals.map((meal) => (
                <div key={meal.key} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{meal.icon}</span>
                      <div>
                        <h4 className="font-medium">{meal.label}</h4>
                        <div className="flex items-center gap-1 text-sm text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {meal.time}
                        </div>
                      </div>
                    </div>
                    {ketoScore > 75 && (
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        키토 친화적
                      </Badge>
                    )}
                  </div>
                  
                  {isEditing ? (
                    <input
                      type="text"
                      value={editedMealData[meal.key as keyof MealData] || ''}
                      onChange={(e) => setEditedMealData(prev => ({
                        ...prev,
                        [meal.key]: e.target.value
                      }))}
                      placeholder={`${meal.label} 메뉴를 입력하세요`}
                      className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      {mealData && mealData[meal.key as keyof MealData] 
                        ? mealData[meal.key as keyof MealData]
                        : '계획된 식단이 없습니다'
                      }
                    </div>
                  )}
                </div>
              ))}

              {isEditing && (
                <div className="flex gap-2 pt-4">
                  <Button onClick={handleSave} className="flex-1">
                    저장
                  </Button>
                  <Button variant="outline" onClick={handleCancel} className="flex-1">
                    취소
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 추가 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                키토 목표
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">탄수화물</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full" 
                        style={{ width: `${Math.min(ketoScore, 100)}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">20g</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">단백질</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: '80%' }}
                      />
                    </div>
                    <span className="text-sm font-medium">120g</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">지방</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-purple-600 h-2 rounded-full" 
                        style={{ width: '90%' }}
                      />
                    </div>
                    <span className="text-sm font-medium">150g</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 액션 버튼들 */}
          <div className="flex gap-2">
            <Button className="flex-1" onClick={() => {/* AI 식단 추천 */}}>
              <TrendingUp className="h-4 w-4 mr-2" />
              AI 식단 추천
            </Button>
            <Button variant="outline" className="flex-1">
              <Plus className="h-4 w-4 mr-2" />
              식단 추가
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
