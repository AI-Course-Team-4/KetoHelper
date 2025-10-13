import { Button } from '@/components/ui/button'
import { DeleteForever, ChevronLeft, ChevronRight } from '@mui/icons-material'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'

interface CalendarHeaderProps {
  onDeleteAllPlans: () => void
  onDeleteMonthPlans: () => void
  isDeletingAll: boolean
  isDeletingMonth: boolean
  currentMonth: Date
  onMonthChange: (month: Date) => void
}

export function CalendarHeader({
  onDeleteAllPlans,
  onDeleteMonthPlans,
  isDeletingAll,
  isDeletingMonth,
  currentMonth,
  onMonthChange
}: CalendarHeaderProps) {
  return (
    <div>
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
        <div className="flex-1 flex items-center gap-4">
          <h1 className="text-2xl font-bold text-gradient">식단 캘린더</h1>
          {/* 월 이동 컨트롤 */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onMonthChange(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
              className="hover:bg-green-50 hover:border-green-300"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-lg font-bold min-w-[140px] text-center bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
              {format(currentMonth, 'yyyy년 M월', { locale: ko })}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onMonthChange(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
              className="hover:bg-green-50 hover:border-green-300"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Button 
            onClick={onDeleteMonthPlans}
            disabled={isDeletingAll || isDeletingMonth}
            variant="destructive"
            className="px-4 py-2 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white rounded-lg font-semibold disabled:opacity-50 shadow-lg hover:shadow-xl transition-all duration-300"
          >
            <DeleteForever sx={{ fontSize: 20, mr: 1 }} />
            {isDeletingMonth ? '삭제 중...' : '월별 삭제'}
          </Button>
          
          <Button 
            onClick={onDeleteAllPlans}
            disabled={isDeletingAll || isDeletingMonth}
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
