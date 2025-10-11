import { useState } from 'react'
import { Dialog, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Edit, CalendarToday, AccessTime, Restaurant, Delete } from '@mui/icons-material'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { MealData } from '@/data/ketoMeals'

interface DateDetailModalProps {
  isOpen: boolean
  onClose: () => void
  selectedDate: Date
  mealData: MealData | null
  onSaveMeal: (date: Date, mealData: MealData) => void
  onToggleComplete?: (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => void
  isMealChecked?: (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => boolean
  onDeleteMeal?: (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => void
  onDeleteAllMeals?: (date: Date) => void
}

export function DateDetailModal({ 
  isOpen, 
  onClose, 
  selectedDate, 
  mealData, 
  onSaveMeal,
  onToggleComplete,
  isMealChecked,
  onDeleteMeal,
  onDeleteAllMeals
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

  const handleMealClick = (mealContent: string, recipeUrl?: string) => {
    if (!mealContent || mealContent.trim() === '') return
    
    if (recipeUrl && recipeUrl.trim() !== '') {
      // URL이 있으면 해당 레시피 페이지로 이동
      window.open(recipeUrl, '_blank')
    } else {
      // URL이 없으면 구글 검색
      const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(mealContent)}`
      window.open(searchUrl, '_blank')
    }
  }

  const meals = [
    { key: 'breakfast', label: '아침', icon: '🌅', time: '07:00' },
    { key: 'lunch', label: '점심', icon: '☀️', time: '12:00' },
    { key: 'dinner', label: '저녁', icon: '🌙', time: '18:00' },
    { key: 'snack', label: '간식', icon: '🍎', time: '15:00' }
  ]

  return (
    <Dialog open={isOpen} onClose={onClose} onOpenChange={onClose} maxWidth="md">
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <CalendarToday sx={{ fontSize: 20 }} />
          {format(selectedDate, 'yyyy년 M월 d일 (E)', { locale: ko })}
        </DialogTitle>
      </DialogHeader>

      <div className="space-y-6">
          {/* 식단 정보 */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Restaurant sx={{ fontSize: 20 }} />
                식단 계획
              </CardTitle>
              <div className="flex items-center gap-2">
                {isEditing ? (
                  <>
                    <Button onClick={handleSave} size="sm">
                      저장
                    </Button>
                    <Button variant="outline" onClick={handleCancel} size="sm">
                      취소
                    </Button>
                  </>
                ) : (
                  <>
                    {onDeleteAllMeals && mealData && Object.values(mealData).some(meal => meal && meal.trim() !== '') && (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => {
                          if (confirm('이 날의 모든 식단을 삭제하시겠습니까?')) {
                            onDeleteAllMeals(selectedDate)
                          }
                        }}
                        className="border-red-300 text-red-600 hover:bg-red-50"
                      >
                        <Delete className="h-4 w-4 mr-2" />
                        전체 삭제
                      </Button>
                    )}
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setIsEditing(!isEditing)}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      편집
                    </Button>
                  </>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {meals.map((meal) => {
                const mealKey = meal.key as 'breakfast' | 'lunch' | 'dinner' | 'snack'
                const mealContent = mealData?.[mealKey] || ''
                const urlKey = `${meal.key}Url` as 'breakfastUrl' | 'lunchUrl' | 'dinnerUrl' | 'snackUrl'
                const recipeUrl = mealData?.[urlKey]
                const hasMealData = mealContent && mealContent.trim() !== ''
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
                    onClick={() => {
                      if (hasMealData && !isEditing) {
                        handleMealClick(mealContent, recipeUrl)
                      }
                    }}
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
                            <AccessTime sx={{ fontSize: 12 }} />
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
                            {onDeleteMeal && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  onDeleteMeal(selectedDate, meal.key as 'breakfast' | 'lunch' | 'dinner' | 'snack')
                                }}
                                className="h-6 w-6 p-0 border-red-300 text-red-600 hover:bg-red-50"
                              >
                                <Delete sx={{ fontSize: 14 }} />
                              </Button>
                            )}
                          </>
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
                          ? mealContent
                          : '계획된 식단이 없습니다'
                        }
                      </div>
                    )}
                  </div>
                )
              })}
            </CardContent>
          </Card>
        </div>
    </Dialog>
  )
}