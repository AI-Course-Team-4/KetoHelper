import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Add } from '@mui/icons-material'
import { CalendarToday } from '@mui/icons-material'
import { format, isToday } from 'date-fns'
import { ko } from 'date-fns/locale'
import { MealData } from '@/data/ketoMeals'

interface SelectedDateMealsProps {
  selectedDate: Date | undefined
  getMealForDate: (date: Date) => MealData | null
  onOpenModal: (mealType?: string) => void
}

// 컴포넌트 상단에 추가
const getMealText = (mealData: MealData | null, mealType: string): string => {
  if (!mealData) return '';

  switch (mealType) {
    case 'breakfast':
      return mealData.breakfast || '';
    case 'lunch':
      return mealData.lunch || '';
    case 'dinner':
      return mealData.dinner || '';
    case 'snack':
      return mealData.snack || '';
    default:
      return '';
  }
};

export function SelectedDateMeals({
  selectedDate,
  getMealForDate,
  onOpenModal
}: SelectedDateMealsProps) {
  return (
    <Card className="lg:col-span-1 border border-gray-200">
      <CardHeader className="pb-4 h-[88px]">
        <CardTitle className="flex items-center text-xl font-bold">
          <CalendarToday sx={{ fontSize: 24, mr: 1.5, color: 'green.600' }} />
          {selectedDate && isToday(selectedDate) ? '오늘의' : selectedDate ? format(selectedDate, 'M월 d일', { locale: ko }) : '오늘의'} 식단
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
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
              className="border border-gray-200 rounded-lg p-3 cursor-pointer bg-white hover:bg-gray-50 transition-all duration-200"
              onClick={() => onOpenModal(meal.key)}
            >
              <div className="flex justify-between items-center">
                <h4 className="font-semibold flex items-center gap-2 text-gray-800">
                  <span className="text-lg">{meal.icon}</span>
                  {meal.label}
                </h4>
                <div className="w-6 h-6 rounded-full bg-green-100 hover:bg-green-200 flex items-center justify-center transition-colors">
                  <Add sx={{ fontSize: 14, color: 'green.600' }} />
                </div>
              </div>
              <div className="text-xs text-gray-600 mt-1 ml-8">
                {(() => {
                  const mealText = getMealText(selectedMeal, meal.key);
                  return mealText.trim() !== '' ? mealText : '계획된 식단이 없습니다';
                })()}
              </div>
            </div>
          ))
        })() : (
          <div className="text-center text-gray-500 py-8 text-sm">
            날짜를 선택하면 해당 날의 식단을 볼 수 있습니다
          </div>
        )}
      </CardContent>
    </Card>
  )
}
