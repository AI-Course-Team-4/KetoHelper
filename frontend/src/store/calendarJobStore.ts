import { create } from 'zustand'

type JobStatus = 'idle' | 'processing'

interface CalendarJobState {
  // 간단 버전: jobId 없이 확인 기준만 저장
  userId?: string
  startDate?: string // yyyy-MM-dd
  durationDays?: number
  monthKey?: string
  startedAt?: number
  status: JobStatus
  setCriteria: (job: { userId: string; startDate: string; durationDays: number; monthKey?: string }) => void
  clear: () => void
}

export const useCalendarJobStore = create<CalendarJobState>((set) => ({
  userId: undefined,
  startDate: undefined,
  durationDays: undefined,
  monthKey: undefined,
  startedAt: undefined,
  status: 'idle',
  setCriteria: ({ userId, startDate, durationDays, monthKey }) => 
    set({ userId, startDate, durationDays, monthKey, startedAt: Date.now(), status: 'processing' }),
  clear: () => set({ userId: undefined, startDate: undefined, durationDays: undefined, monthKey: undefined, startedAt: undefined, status: 'idle' })
}))


