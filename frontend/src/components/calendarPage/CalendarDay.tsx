import { MealData } from '@/data/ketoMeals'

interface CalendarDayProps {
  date: Date
  displayMonth: Date
  meal: MealData | null
  isMealChecked: (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => boolean
  isOptimisticMeal?: (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => boolean
  onDateClick: (date: Date) => void
  onToggleMealCheck: (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack') => void
}

export function CalendarDay({
  date,
  displayMonth,
  meal,
  isMealChecked,
  isOptimisticMeal,
  onDateClick,
  onToggleMealCheck
}: CalendarDayProps) {
  const isCurrentMonth = date.getMonth() === displayMonth.getMonth()
  
  // 오늘 날짜인지 확인
  const today = new Date()
  const isToday = date.getDate() === today.getDate() &&
                  date.getMonth() === today.getMonth() &&
                  date.getFullYear() === today.getFullYear()

  // 체크된 식사 개수 계산 (로컬 상태에서)
  const checkedCount = [
    isMealChecked(date, 'breakfast'),
    isMealChecked(date, 'lunch'),
    isMealChecked(date, 'dinner'),
    isMealChecked(date, 'snack')
  ].filter(Boolean).length

  return (
    <div
      className="relative w-full h-full flex flex-col min-w-0 cursor-pointer hover:bg-gray-50 transition-colors rounded-lg"
      onClick={() => isCurrentMonth && onDateClick(date)}
    >
      {isCurrentMonth && (
        <div className="date-number w-full flex items-center justify-between px-3">
          <span className={`font-semibold ${isToday ? 'bg-gray-700 text-white px-2 py-1 rounded' : ''}`}>
            {date.getDate()}
          </span>
          {checkedCount > 0 && (
            <div className="absolute -top-1 -right-1 bg-green-500 rounded-full w-4 h-4 flex items-center justify-center">
              <span className="text-white text-xs font-bold">✓</span>
            </div>
          )}
        </div>
      )}

      {meal && isCurrentMonth && (
        <div className="meal-info-container w-full min-w-0 flex flex-col p-1 gap-0.5">
          {/* 아침 */}
          {meal.breakfast?.trim() && (
            <div className={`w-full grid grid-cols-[auto,1fr,auto] items-center gap-1 group px-2 ${isOptimisticMeal?.(date, 'breakfast') ? 'opacity-90' : ''}`}>
              <span className="text-xs">🌅</span>
              <span className="min-w-0 truncate text-xs text-left" title={meal.breakfast}>
                <span className="hidden sm:inline">{meal.breakfast}</span>
                <span className="sm:hidden">
                  {meal.breakfast.length > 8 ? meal.breakfast.slice(0, 8) + '…' : meal.breakfast}
                </span>
                {isOptimisticMeal?.(date, 'breakfast') && <span className="text-blue-500 text-xs ml-1">⏳</span>}
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); onToggleMealCheck(date, 'breakfast'); }}
                className="justify-self-end opacity-60 group-hover:opacity-100 transition-opacity text-xs"
                aria-label="breakfast done"
                disabled={isOptimisticMeal?.(date, 'breakfast')}
              >
                {isMealChecked(date, 'breakfast') ? <span className="text-green-500">✅</span> : <span className="text-gray-400">⭕</span>}
              </button>
            </div>
          )}

          {/* 점심 */}
          {meal.lunch?.trim() && (
            <div className={`w-full grid grid-cols-[auto,1fr,auto] items-center gap-1 group px-2 ${isOptimisticMeal?.(date, 'lunch') ? 'opacity-90' : ''}`}>
              <span className="text-xs">☀️</span>
              <span className="min-w-0 truncate text-xs text-left" title={meal.lunch}>
                <span className="hidden sm:inline">{meal.lunch}</span>
                <span className="sm:hidden">
                  {meal.lunch.length > 8 ? meal.lunch.slice(0, 8) + '…' : meal.lunch}
                </span>
                {isOptimisticMeal?.(date, 'lunch') && <span className="text-blue-500 text-xs ml-1">⏳</span>}
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); onToggleMealCheck(date, 'lunch'); }}
                className="justify-self-end opacity-60 group-hover:opacity-100 transition-opacity text-xs"
                aria-label="lunch done"
                disabled={isOptimisticMeal?.(date, 'lunch')}
              >
                {isMealChecked(date, 'lunch') ? <span className="text-green-500">✅</span> : <span className="text-gray-400">⭕</span>}
              </button>
            </div>
          )}

          {/* 저녁 */}
          {meal.dinner?.trim() && (
            <div className={`w-full grid grid-cols-[auto,1fr,auto] items-center gap-1 group px-2 ${isOptimisticMeal?.(date, 'dinner') ? 'opacity-90' : ''}`}>
              <span className="text-xs">🌙</span>
              <span className="min-w-0 truncate text-xs text-left" title={meal.dinner}>
                <span className="hidden sm:inline">{meal.dinner}</span>
                <span className="sm:hidden">
                  {meal.dinner.length > 8 ? meal.dinner.slice(0, 8) + '…' : meal.dinner}
                </span>
                {isOptimisticMeal?.(date, 'dinner') && <span className="text-blue-500 text-xs ml-1">⏳</span>}
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); onToggleMealCheck(date, 'dinner'); }}
                className="justify-self-end opacity-60 group-hover:opacity-100 transition-opacity text-xs"
                aria-label="dinner done"
                disabled={isOptimisticMeal?.(date, 'dinner')}
              >
                {isMealChecked(date, 'dinner') ? <span className="text-green-500">✅</span> : <span className="text-gray-400">⭕</span>}
              </button>
            </div>
          )}

          {/* 간식 */}
          {meal.snack?.trim() && (
            <div className={`w-full grid grid-cols-[auto,1fr,auto] items-center gap-1 group text-purple-600 px-2 ${isOptimisticMeal?.(date, 'snack') ? 'opacity-90' : ''}`}>
              <span className="text-xs">🍎</span>
              <span className="min-w-0 truncate text-xs text-left" title={meal.snack}>
                <span className="hidden sm:inline">{meal.snack}</span>
                <span className="sm:hidden">
                  {meal.snack.length > 8 ? meal.snack.slice(0, 8) + '…' : meal.snack}
                </span>
                {isOptimisticMeal?.(date, 'snack') && <span className="text-blue-500 text-xs ml-1">⏳</span>}
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); onToggleMealCheck(date, 'snack'); }}
                className="justify-self-end opacity-60 group-hover:opacity-100 transition-opacity text-xs"
                aria-label="snack done"
                disabled={isOptimisticMeal?.(date, 'snack')}
              >
                {isMealChecked(date, 'snack') ? <span className="text-green-500">✅</span> : <span className="text-gray-400">⭕</span>}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
