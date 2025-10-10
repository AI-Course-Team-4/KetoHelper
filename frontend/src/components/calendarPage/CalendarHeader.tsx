import { Button } from '@/components/ui/button'
import { Add, DeleteForever } from '@mui/icons-material'

interface CalendarHeaderProps {
  selectedDays: number
  setSelectedDays: (days: number) => void
  isGeneratingMealPlan: boolean
  onGenerateMealPlan: () => void
  onDeleteAllPlans: () => void
  isDeletingAll: boolean
}

export function CalendarHeader({
  selectedDays,
  setSelectedDays,
  isGeneratingMealPlan,
  onGenerateMealPlan,
  onDeleteAllPlans,
  isDeletingAll
}: CalendarHeaderProps) {
  return (
    <div>
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gradient">식단 캘린더</h1>
          <p className="text-muted-foreground mt-1">
            키토 식단 계획을 스마트하게 관리하고 기록하세요
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <select 
            value={selectedDays} 
            onChange={(e) => setSelectedDays(Number(e.target.value))}
            disabled={isGeneratingMealPlan || isDeletingAll}
            className="px-3 py-2 bg-white border-2 border-gray-200 text-gray-700 rounded-lg disabled:opacity-50 focus:border-green-400 focus:outline-none"
          >
            <option value={3}>3일</option>
            <option value={7}>7일</option>
            <option value={14}>14일</option>
            <option value={30}>30일</option>
          </select>
          
          <Button 
            onClick={onGenerateMealPlan}
            disabled={isGeneratingMealPlan || isDeletingAll}
            className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-lg font-semibold disabled:opacity-50 shadow-lg hover:shadow-xl transition-all duration-300"
          >
            <Add sx={{ fontSize: 20, mr: 1 }} />
            {isGeneratingMealPlan ? '생성 중...' : `AI 식단표 생성`}
          </Button>
          
          <Button 
            onClick={onDeleteAllPlans}
            disabled={isGeneratingMealPlan || isDeletingAll}
            variant="destructive"
            className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-lg font-semibold disabled:opacity-50 shadow-lg hover:shadow-xl transition-all duration-300"
          >
            <DeleteForever sx={{ fontSize: 20, mr: 1 }} />
            {isDeletingAll ? '삭제 중...' : '전체 삭제'}
          </Button>
        </div>
      </div>
    </div>
  )
}
