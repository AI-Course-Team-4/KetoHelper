import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axiosClient from '@/lib/axiosClient'

// axiosClient를 사용하여 토큰 갱신과 인증을 자동으로 처리
export const api = axiosClient

// Date Parsing API
export interface DateParseRequest {
  message: string
  context?: string
}

export interface ParsedDateInfo {
  date: string // ISO format
  description: string
  is_relative: boolean
  confidence: number
  method: 'rule-based' | 'llm-assisted' | 'fallback'
  iso_string: string
  display_string: string
}

export interface DateParseResponse {
  success: boolean
  parsed_date?: ParsedDateInfo
  error_message?: string
}

// 메시지에서 날짜 추출
export function useParseDateFromMessage() {
  return useMutation({
    mutationFn: async (data: DateParseRequest): Promise<DateParseResponse> => {
      const response = await api.post('/parse-date', data)
      return response.data
    }
  })
}

// 자연어 날짜 파싱
export function useParseNaturalDate() {
  return useMutation({
    mutationFn: async (data: DateParseRequest): Promise<DateParseResponse> => {
      const response = await api.post('/parse-natural-date', data)
      return response.data
    }
  })
}

// Chat API
export interface ChatRequest {
  message: string
  location?: { lat: number; lng: number }
  radius_km?: number
  profile?: {
    allergies?: string[]
    dislikes?: string[]
    goals_kcal?: number
    goals_carbs_g?: number
  }
  thread_id?: string
  user_id?: string
  guest_id?: string
  chat_history?: Array<{
    id: string
    role: string
    message: string
    created_at: string
  }>
  days?: number
}

export interface ChatResponse {
  response: string
  intent: string
  results?: any[]
  tool_calls?: Array<{
    tool: string
    [key: string]: any
  }>
  session_id?: string
  thread_id?: string
  assistantBatch?: Array<{
    role: string
    message: string
  }>
  meal_plan_data?: {
    duration_days: number
    days: Array<{
      breakfast?: { title: string }
      lunch?: { title: string }
      dinner?: { title: string }
      snack?: { title: string }
    }>
    total_macros?: any
    notes?: string[]
  }
  save_to_calendar_data?: {
    action: string
    start_date: string
    duration_days: number
    message: string
  }
}

// 채팅 스레드 관련 타입
export interface ChatThread {
  id: string
  title: string
  last_message_at: string
  created_at: string
}

export interface ChatHistory {
  id: number
  thread_id: string
  role: string
  message: string
  created_at: string
}

export function useSendMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['send-message'],
    retry: false,

    mutationFn: async (data: ChatRequest): Promise<ChatResponse> => {
      // 중복 실행 방지 임시 비활성화 (게스트 사용자 테스트용)
      // if (isExecutingRef.current) {
      //   throw new Error('이전 요청이 진행 중입니다')
      // }

      // isExecutingRef.current = true

      try {
        const response = await api.post('/chat/', data)
        return response.data
      } finally {
        // isExecutingRef.current = false
      }
    },
    onMutate: async (variables) => {
      console.log('🚀 Optimistic Update 시작:', variables)
      
      // Optimistic Update: 사용자 메시지를 즉시 UI에 추가
      const tempUserMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        message: variables.message,
        created_at: new Date().toISOString()
      }
      
      // 게스트/로그인 사용자별 캐시 키 결정
      const cacheKey = variables.guest_id 
        ? `guest-${variables.guest_id}` // 게스트는 guest_id 기반
        : (variables.thread_id || `temp-thread-${Date.now()}`) // 로그인은 thread_id 기반
      
      console.log('📝 임시 사용자 메시지:', { cacheKey, tempUserMessage })
      
      // 채팅 히스토리에 임시 메시지 추가 (새 채팅에서도 웰컴 스크린이 사라지도록)
      const queryKey = ['chat-history', cacheKey, 20]
      
      queryClient.setQueryData(queryKey, (old: ChatHistory[] | undefined) => {
        const newData = [...(old || []), tempUserMessage]
        console.log('💾 사용자 메시지 캐시 업데이트:', { 
          cacheKey, 
          oldLength: old?.length, 
          newLength: newData.length,
          newData: newData.map(msg => ({ id: msg.id, message: msg.message }))
        })
        return newData
      })
      
      // Optimistic Update로 즉시 표시되므로 refetch 불필요
      
      // 채팅 스레드 목록도 업데이트 (기존 스레드가 있는 경우만)
      if (variables.thread_id) {
        queryClient.setQueryData(['chat-threads'], (old: ChatThread[] | undefined) => {
          if (!old) return old
          return old.map(thread => 
            thread.id === variables.thread_id 
              ? { ...thread, updated_at: new Date().toISOString() }
              : thread
          )
        })
      }
    },
    onSuccess: (data, variables) => {
      // 서버 응답 후 실제 데이터로 교체
      // 게스트/로그인 사용자별 캐시 키 결정
      const cacheKey = variables.guest_id 
        ? `guest-${variables.guest_id}` // 게스트는 guest_id 기반
        : (data.thread_id || variables.thread_id || `temp-thread-${Date.now()}`) // 로그인은 thread_id 기반
      
      if (cacheKey) {
        // 1. 임시 사용자 메시지를 실제 메시지로 교체하고 AI 응답 추가
        queryClient.setQueryData(['chat-history', cacheKey, 20], (old: ChatHistory[] | undefined) => {
          if (!old) return []

          // 임시 메시지를 실제 메시지로 교체
          const updatedMessages = old.map(msg =>
            msg.id.toString().startsWith('temp-')
              ? {
                  id: `user-${Date.now()}`,
                  role: 'user',
                  message: variables.message,
                  created_at: new Date().toISOString()
                }
              : msg
          )

          // AI 응답 추가 (invalidateQueries 대신 직접 캐시 업데이트)
          if (data.response) {
            console.log('🤖 AI 응답 도착:', data.response.substring(0, 50) + '...')
            return [
              ...updatedMessages,
              {
                id: `assistant-${Date.now()}`,
                role: 'assistant',
                message: data.response,
                created_at: new Date().toISOString()
              }
            ]
          }

          return updatedMessages
        })

        // 새 스레드가 생성된 경우에만 스레드 목록 새로고침
        if (!variables.thread_id && data.thread_id) {
          queryClient.invalidateQueries({ queryKey: ['chat-threads'] })
        }
      }
      
      // 🆕 캘린더 저장이 포함된 경우 plans-range 캐시 즉시 업데이트
      if (data.response && (
        data.response.includes('성공적으로 캘린더에 저장') ||
        data.response.includes('캘린더에 저장') ||
        data.response.includes('저장되었습니다')
      )) {
        console.log('💾 캘린더 저장 감지 - plans-range 캐시 즉시 업데이트')
        
        // 모든 plans-range 쿼리 무효화하여 새 데이터 로드
        queryClient.invalidateQueries({ queryKey: ['plans-range'] })
        
        // 백그라운드에서 새 데이터 가져오기
        queryClient.refetchQueries({ queryKey: ['plans-range'] })
        
        console.log('✅ plans-range 캐시 업데이트 완료')
      }
    },
    onError: (error: any, variables) => {
      // 에러 시 임시 메시지를 실제 메시지로 교체하고 에러 메시지 추가
      // 게스트/로그인 사용자별 캐시 키 결정
      const cacheKey = variables.guest_id 
        ? `guest-${variables.guest_id}` // 게스트는 guest_id 기반
        : (variables.thread_id || `temp-thread-${Date.now()}`) // 로그인은 thread_id 기반
      
      if (cacheKey) {
        queryClient.setQueryData(['chat-history', cacheKey, 20], (old: ChatHistory[] | undefined) => {
          if (!old) return []

          // 임시 메시지를 실제 사용자 메시지로 교체
          const withoutTemp = old.filter(msg => !msg.id.toString().startsWith('temp-'))

          // 타임아웃 또는 네트워크 에러 판별
          const isTimeout = error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')
          const errorMessage = isTimeout
            ? '⏱️ 요청 처리 시간이 초과되었습니다. 복잡한 요청은 시간이 걸릴 수 있습니다. 잠시 후 다시 시도해주세요.'
            : '❌ 메시지 전송에 실패했습니다. 네트워크 연결을 확인하고 다시 시도해주세요.'

          return [
            ...withoutTemp,
            {
              id: `user-${Date.now()}`,
              role: 'user',
              message: variables.message,
              created_at: new Date().toISOString()
            },
            {
              id: `error-${Date.now()}`,
              role: 'assistant',
              message: errorMessage,
              created_at: new Date().toISOString()
            }
          ]
        })
      }
    }
  })
}

// 채팅 스레드 목록 조회
export function useGetChatThreads(userId?: string, guestId?: string, limit = 20) {
  return useQuery({
    queryKey: ['chat-threads', userId, guestId, limit],
    queryFn: async (): Promise<ChatThread[]> => {
      const params: any = { limit }
      if (userId) params.user_id = userId
      if (guestId) params.guest_id = guestId

      const response = await api.get('/chat/threads', { params })
      return response.data
    },
    enabled: false, //수동으로만 호출 (자동 호출 완전 차단)
    staleTime: Infinity, // 절대 stale 되지 않음
    gcTime: 10 * 60 * 1000, // 10분간 캐시 유지
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchInterval: false, // 자동 폴링 비활성화
    refetchIntervalInBackground: false
  })
}

// 채팅 히스토리 조회
export function useGetChatHistory(threadId: string, limit = 20, before?: string) {
  return useQuery({
    queryKey: ['chat-history', threadId, limit],  // before 제거 (페이징 시에만 사용)
    queryFn: async (): Promise<ChatHistory[]> => {
      const params: any = { limit }
      if (before) params.before = before

      const response = await api.get(`/chat/history/${threadId}`, { params })
      return response.data
    },
    // temp-thread-* 는 서버 호출하지 않음 (신규 채팅 준비용 가상 ID)
    enabled: false, // 수동으로만 호출 (자동 호출 완전 차단)
    staleTime: Infinity, // 절대 stale 되지 않음
    gcTime: 10 * 60 * 1000, // 10분간 캐시 유지
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchInterval: false, // 자동 폴링 비활성화
    refetchIntervalInBackground: false
  })
}

// 새 채팅 스레드 생성
export function useCreateNewThread() {
  return useMutation({
    mutationFn: async (data: { userId?: string; guestId?: string }): Promise<ChatThread> => {
      const params: any = {}
      if (data.userId) params.user_id = data.userId
      if (data.guestId) params.guest_id = data.guestId

      const response = await api.post('/chat/threads/new', {}, { params })
      return response.data
    }
  })
}

// 채팅 스레드 삭제
export function useDeleteThread() {
  return useMutation({
    mutationFn: async (threadId: string): Promise<{ message: string }> => {
      const response = await api.delete(`/chat/threads/${threadId}`)
      return response.data
    }
  })
}

// 스트리밍 채팅 API
export async function* sendMessageStream(data: ChatRequest): AsyncGenerator<any, void, unknown> {
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('Response body is not readable')
  }

  const decoder = new TextDecoder()

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            yield data
          } catch (e) {
            console.warn('Failed to parse SSE data:', line)
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

// Places API
export interface PlaceSearchRequest {
  q: string
  lat: number
  lng: number
  radius?: number
  category?: string
}

export function useSearchPlaces() {
  return useMutation({
    mutationFn: async (params: PlaceSearchRequest) => {
      const response = await api.get('/places', { params })
      return response.data
    }
  })
}

export function useNearbyPlaces(lat: number, lng: number, radius = 1000, minScore = 70) {
  return useQuery({
    queryKey: ['nearby-places', lat, lng, radius, minScore],
    queryFn: async () => {
      const response = await api.get('/places/nearby', {
        params: { lat, lng, radius, min_score: minScore }
      })
      return response.data
    },
    enabled: !!(lat && lng)
  })
}

// Plans API
export interface PlanCreateRequest {
  date: string
  slot: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  type: 'recipe' | 'place'
  ref_id: string
  title: string
  macros?: any
  location?: any
  notes?: string
}

export function useCreatePlan() {
  return useMutation({
    mutationFn: async (data: PlanCreateRequest & { user_id: string }) => {
      const response = await api.post('/plans/item', data, {
        params: { user_id: data.user_id }
      })
      return response.data
    }
  })
}

// 캘린더 입력창 전용: 단일 식단 추가 (백엔드에서 빈 입력 검증 포함)
export function useAddMealToCalendar() {
  return useMutation({
    mutationFn: async (data: PlanCreateRequest & { user_id: string }) => {
      const response = await api.post('/plans/calendar/add_meal', data, {
        params: { user_id: data.user_id }
      })
      return response.data
    }
  })
}

export function usePlansRange(startDate: string, endDate: string, userId: string) {
  return useQuery({
    queryKey: ['plans-range', startDate, endDate, userId],
    queryFn: async () => {
      console.log('🌐 API 호출 시작:', {
        url: '/plans/range',
        params: { start: startDate, end: endDate, user_id: userId },
        timestamp: new Date().toISOString()
      })
      
      const response = await api.get('/plans/range', {
        params: { start: startDate, end: endDate, user_id: userId }
      })
      
      console.log('🌐 API 응답 받음:', {
        status: response.status,
        dataLength: response.data ? response.data.length : 0,
        data: response.data,
        timestamp: new Date().toISOString()
      })
      
      return response.data
    },
    enabled: !!(startDate && endDate && userId),
    refetchOnWindowFocus: false, // 포커스 시 리페치 비활성화
    staleTime: 5 * 60 * 1000, // 5분간 신선한 데이터로 간주
    gcTime: 30 * 60 * 1000, // 30분간 캐시 유지
  })
}

export function useUpdatePlan() {
  return useMutation({
    mutationFn: async ({ planId, updates, userId }: {
      planId: string
      updates: { status?: string; notes?: string }
      userId: string
    }) => {
      const response = await api.patch(`/plans/item/${planId}`, updates, {
        params: { user_id: userId }
      })
      return response.data
    },
    // 동시 실행 허용 및 재시도 설정
    retry: 2,
    retryDelay: 1000
  })
}

export function useDeletePlan() {
  return useMutation({
    mutationFn: async ({ planId, userId }: {
      planId: string
      userId: string
    }) => {
      const response = await api.delete(`/plans/item/${planId}`, {
        params: { user_id: userId }
      })
      return response.data
    }
  })
}

// 전체 식단 계획 삭제
export function useDeleteAllPlans() {
  return useMutation({
    mutationFn: async (userId: string) => {
      const response = await api.delete('/plans/all', {
        params: { user_id: userId }
      })
      return response.data
    }
  })
}

// 월별 식단 계획 삭제
export function useDeleteMonthPlans() {
  return useMutation({
    mutationFn: async ({ userId, year, month }: { userId: string; year: number; month: number }) => {
      const response = await api.delete('/plans/month', {
        params: { user_id: userId, year, month }
      })
      return response.data
    }
  })
}

// Meal Plan Generation
export interface MealPlanRequest {
  days?: number
  kcal_target?: number
  carbs_max?: number
  allergies?: string[]
  dislikes?: string[]
}

export function useGenerateMealPlan() {
  return useMutation({
    mutationFn: async (data: { user_id: string; days: number }) => {
      // 개인화된 식단표 생성 (프로필 자동 적용)
      const response = await fetch(`/api/v1/plans/generate/personalized?user_id=${data.user_id}&days=${data.days}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      if (!response.ok) throw new Error('식단 생성 실패')

      const result = await response.json()
      return result
    }
  })
}

export function useCommitMealPlan() {
  return useMutation({
    mutationFn: async ({
      mealPlan,
      userId,
      startDate
    }: {
      mealPlan: any
      userId: string
      startDate: string
    }) => {
      const response = await api.post('/plans/commit', mealPlan, {
        params: { user_id: userId, start_date: startDate }
      })
      return response.data
    }
  })
}

// Statistics
export function usePlanStatistics(startDate: string, endDate: string, userId: string) {
  return useQuery({
    queryKey: ['plan-statistics', startDate, endDate, userId],
    queryFn: async () => {
      const response = await api.get(`/plans/stats/${startDate}/${endDate}`, {
        params: { user_id: userId }
      })
      return response.data
    },
    enabled: !!(startDate && endDate && userId)
  })
}

// Export functions
export function useExportWeekICS() {
  return useMutation({
    mutationFn: async ({ startDate, userId }: { startDate: string; userId: string }) => {
      const response = await api.get(`/plans/week/${startDate}/export.ics`, {
        params: { user_id: userId },
        responseType: 'blob'
      })

      // 파일 다운로드
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `keto_meal_plan_${startDate}.ics`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      return response.data
    }
  })
}

export function useShoppingList(startDate: string, userId: string) {
  return useQuery({
    queryKey: ['shopping-list', startDate, userId],
    queryFn: async () => {
      const response = await api.get(`/plans/week/${startDate}/shopping-list`, {
        params: { user_id: userId }
      })
      return response.data
    },
    enabled: !!(startDate && userId)
  })
}
