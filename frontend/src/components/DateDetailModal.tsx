import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Edit, Calendar, Clock, Utensils, Target } from 'lucide-react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { MealData } from '@/data/ketoMeals'
import { MealDetailModal } from './MealDetailModal'

interface DateDetailModalProps {
  isOpen: boolean
  onClose: () => void
  selectedDate: Date
  mealData: MealData | null
  onSaveMeal: (date: Date, mealData: MealData) => void
  onToggleComplete?: (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => void
  isMealChecked?: (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => boolean
}

export function DateDetailModal({ 
  isOpen, 
  onClose, 
  selectedDate, 
  mealData, 
  onSaveMeal,
  onToggleComplete,
  isMealChecked
}: DateDetailModalProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedMealData, setEditedMealData] = useState<MealData>({
    breakfast: mealData?.breakfast || '',
    lunch: mealData?.lunch || '',
    dinner: mealData?.dinner || '',
    snack: mealData?.snack || ''
  })
  const [selectedMealForDetail, setSelectedMealForDetail] = useState<{
    type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
    content: string
    info: { label: string; icon: string; time: string }
  } | null>(null)

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

  const handleMealClick = (mealKey: string) => {
    if (!mealData || !mealData[mealKey as keyof MealData]) return
    
    const meal = meals.find(m => m.key === mealKey)
    if (meal) {
      setSelectedMealForDetail({
        type: mealKey as 'breakfast' | 'lunch' | 'dinner' | 'snack',
        content: String(mealData[mealKey as keyof MealData] || ''),
        info: {
          label: meal.label,
          icon: meal.icon,
          time: meal.time
        }
      })
    }
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
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            {format(selectedDate, 'yyyy년 M월 d일 (E)', { locale: ko })}
          </DialogTitle>
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
              {meals.map((meal) => {
                const hasMealData = mealData && mealData[meal.key as keyof MealData]
                const currentHour = new Date().getHours()
                const mealHour = parseInt(meal.time.split(':')[0])
                const today = new Date()
                const selectedDateOnly = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate())
                const todayDateOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate())
                
                // 지난 날짜이거나, 오늘 날짜인데 식사 시간이 지났으면 true
                const isPastMeal = selectedDateOnly < todayDateOnly || 
                  (selectedDateOnly.getTime() === todayDateOnly.getTime() && currentHour > mealHour + 2)
                
                const isCompletedMeal = isMealChecked ? isMealChecked(selectedDate, meal.key as 'breakfast' | 'lunch' | 'dinner' | 'snack') : false
                
                return (
                  <div 
                    key={meal.key} 
                    className={`border rounded-lg p-4 transition-all duration-200 ${
                      hasMealData && !isEditing ? 'cursor-pointer hover:bg-gray-50 hover:shadow-md' : ''
                    } ${
                      isCompletedMeal ? 'bg-green-50 border-green-200' : 
                      isPastMeal && !isCompletedMeal && !isEditing ? 'bg-gray-50 border-gray-200 opacity-60' : ''
                    }`}
                    onClick={() => hasMealData && !isEditing ? handleMealClick(meal.key) : undefined}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{meal.icon}</span>
                        <div>
                          <h4 className={`font-medium flex items-center gap-2 ${
                            isPastMeal && !isCompletedMeal && !isEditing ? 'text-gray-500' : ''
                          }`}>
                            {meal.label}
                            {isCompletedMeal && (
                              <span className="text-green-600">✓</span>
                            )}
                            {isPastMeal && !isCompletedMeal && !isEditing && (
                              <span className="text-gray-400 text-xs">(지난 시간)</span>
                            )}
                          </h4>
                          <div className={`flex items-center gap-1 text-sm ${
                            isPastMeal && !isCompletedMeal && !isEditing ? 'text-gray-400' : 'text-muted-foreground'
                          }`}>
                            <Clock className="h-3 w-3" />
                            {meal.time}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {hasMealData && !isEditing && (
                          <>
                            <div
                              onClick={(e) => {
                                e.stopPropagation()
                                if (onToggleComplete) {
                                  onToggleComplete(selectedDate, meal.key as 'breakfast' | 'lunch' | 'dinner' | 'snack')
                                }
                              }}
                              className="cursor-pointer"
                            >
                              {isCompletedMeal ? (
                                <span className="text-green-500 text-lg">✅</span>
                              ) : (
                                <span className="text-gray-400 text-lg">⭕</span>
                              )}
                            </div>
                            <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                              클릭해서 상세보기
                            </div>
                          </>
                        )}
                        {ketoScore > 75 && (
                          <Badge variant="secondary" className="bg-green-100 text-green-800">
                            키토 친화적
                          </Badge>
                        )}
                      </div>
                    </div>
                    
                    {isEditing ? (
                      <input
                        type="text"
                        value={String(editedMealData[meal.key as keyof MealData] || '')}
                        onChange={(e) => setEditedMealData(prev => ({
                          ...prev,
                          [meal.key]: e.target.value
                        }))}
                        placeholder={`${meal.label} 메뉴를 입력하세요`}
                        className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                      />
                    ) : (
                      <div className={`text-sm ${
                        isCompletedMeal ? 'text-green-700' : 
                        isPastMeal && !isCompletedMeal && !isEditing ? 'text-gray-400' : 
                        'text-muted-foreground'
                      }`}>
                        {hasMealData 
                          ? mealData[meal.key as keyof MealData]
                          : '계획된 식단이 없습니다'
                        }
                      </div>
                    )}
                  </div>
                )
              })}

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

        </div>
      </DialogContent>

      {/* 식단 상세정보 모달 */}
      {selectedMealForDetail && (
        <MealDetailModal
          isOpen={!!selectedMealForDetail}
          onClose={() => setSelectedMealForDetail(null)}
          mealType={selectedMealForDetail.type}
          mealContent={selectedMealForDetail.content}
          mealInfo={selectedMealForDetail.info}
        />
      )}
    </Dialog>
  )
}
