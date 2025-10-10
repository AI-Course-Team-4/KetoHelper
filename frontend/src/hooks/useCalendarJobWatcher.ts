import { useEffect } from 'react'
import { useQueryClient, useQuery } from '@tanstack/react-query'
import { useCalendarJobStore } from '@/store/calendarJobStore'
import { api } from '@/hooks/useApi'

// 백엔드 파라미터 명세에 맞춰 'start' 사용 (기존 'start_date' 아님)
async function fetchSimpleStatus(params: { user_id: string; start: string; duration_days: number }) {
  const res = await api.get('/plans/status', { params })
  return res.data as { status: 'processing' | 'done'; found_count: number }
}

export function useCalendarJobWatcher() {
  const queryClient = useQueryClient()
  const { userId, startDate, durationDays, monthKey, clear, status } = useCalendarJobStore()

  const enabled = !!(userId && startDate && durationDays)
  const { data } = useQuery<{ status: 'processing' | 'done'; found_count: number }>({
    queryKey: ['calendar-job', userId, startDate, durationDays],
    queryFn: () => fetchSimpleStatus({ user_id: userId!, start: startDate!, duration_days: durationDays! }),
    enabled,
    refetchInterval: (q) => (q.state.data?.status === 'processing' ? 1000 : false)
  })

  useEffect(() => {
    if (!data) return
    if (data.status === 'done') {
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })
      queryClient.refetchQueries({ queryKey: ['plans-range'] })
      // ✅ Optimistic 데이터 전부 제거 및 저장 상태 초기화
      try {
        const { useCalendarStore } = require('@/store/calendarStore')
        const state = useCalendarStore.getState()
        if (state.optimisticMeals.length > 0) {
          state.removeOptimisticMeals(state.optimisticMeals.map((m: any) => m.id))
        }
        state.clearSaveState()
      } catch {}
      clear()
    }
  }, [data, queryClient, clear, monthKey, status])
}


