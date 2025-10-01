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
    mutationFn: async (data: ChatRequest): Promise<ChatResponse> => {
      const response = await api.post('/chat/', data)
      return response.data
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
      
      // 새 채팅이든 기존 채팅이든 임시 메시지 추가
      const threadId = variables.thread_id || `temp-thread-${Date.now()}`
      
      console.log('📝 임시 사용자 메시지:', { threadId, tempUserMessage })
      
      // 채팅 히스토리에 임시 메시지 추가 (새 채팅에서도 웰컴 스크린이 사라지도록)
      const queryKey = ['chat-history', threadId, 20]
      
      queryClient.setQueryData(queryKey, (old: ChatHistory[] | undefined) => {
        const newData = [...(old || []), tempUserMessage]
        console.log('💾 사용자 메시지 캐시 업데이트:', { 
          threadId, 
          oldLength: old?.length, 
          newLength: newData.length,
          newData: newData.map(msg => ({ id: msg.id, message: msg.message }))
        })
        return newData
      })
      
      // 즉시 refetch하여 사용자 메시지가 바로 표시되도록 함
      setTimeout(() => {
        queryClient.refetchQueries({ queryKey: ['chat-history', threadId, 20] })
      }, 0)
      
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
      if (data.thread_id) {
        // 1. 임시 사용자 메시지를 실제 메시지로 교체
        queryClient.setQueryData(['chat-history', data.thread_id, 20], (old: ChatHistory[] | undefined) => {
          if (!old) return old
          return old.map(msg => 
            msg.id.toString().startsWith('temp-') 
              ? { 
                  id: `user-${Date.now()}`, 
                  role: 'user', 
                  message: variables.message, 
                  created_at: new Date().toISOString() 
                }
              : msg
          )
        })
        
        // 2. AI 응답 추가 (로딩 인디케이터와 자연스럽게 교체)
        if (data.response) {
          console.log('🤖 AI 응답 추가:', data.response.substring(0, 50) + '...')
          
      // 전역 이벤트 제거: 로딩 상태는 호출 측에서 관리
          
          // AI 응답을 즉시 추가 (타이핑 애니메이션은 MessageItem에서 처리)
          queryClient.setQueryData(['chat-history', data.thread_id, 20], (old: ChatHistory[] | undefined) => {
              const newData = [
                ...(old || []),
                {
                  id: `ai-${Date.now()}`,
                  role: 'assistant',
                  message: data.response, // 실제 메시지 내용으로 즉시 추가
                  created_at: new Date().toISOString()
                }
              ]
              console.log('✅ AI 응답 캐시 업데이트:', { 
                oldLength: old?.length, 
                newLength: newData.length 
              })
              return newData
            })
            
            // AI 응답 추가 후 useGetChatHistory가 즉시 감지하도록 강제 refetch
            queryClient.invalidateQueries({ queryKey: ['chat-history', data.thread_id, 20] })
        }
      }
      
      // 채팅 스레드 목록 새로고침
      queryClient.invalidateQueries({ queryKey: ['chat-threads'] })
    },
    onError: (_error, variables) => {
      // 에러 시 임시 메시지 제거
      if (variables.thread_id) {
        queryClient.setQueryData(['chat-history', variables.thread_id, 20], (old: ChatHistory[] | undefined) => {
          if (!old) return old
          return old.filter(msg => !msg.id.toString().startsWith('temp-'))
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
    enabled: !!(userId || guestId),
    staleTime: 60 * 1000, // 1분간 fresh 상태 유지
    gcTime: 10 * 60 * 1000, // 10분간 캐시 유지
    refetchOnWindowFocus: false, // 윈도우 포커스 시 자동 새로고침 비활성화
    refetchOnMount: true // 컴포넌트 마운트 시 새로고침 활성화
  })
}

// 채팅 히스토리 조회
export function useGetChatHistory(threadId: string, limit = 20, before?: string) {
  return useQuery({
    queryKey: ['chat-history', threadId, limit, before],
    queryFn: async (): Promise<ChatHistory[]> => {
      const params: any = { limit }
      if (before) params.before = before

      const response = await api.get(`/chat/history/${threadId}`, { params })
      return response.data
    },
    // temp-thread-* 는 서버 호출하지 않음 (신규 채팅 준비용 가상 ID)
    enabled: !!threadId && threadId.length > 0 && !threadId.startsWith('temp-thread-'),
    staleTime: 5 * 60 * 1000, // 5분간 fresh 상태 유지 (캐시 우선 사용)
    gcTime: 10 * 60 * 1000, // 10분간 캐시 유지
    refetchOnWindowFocus: false, // 윈도우 포커스 시 자동 새로고침 비활성화
    refetchOnMount: true // 컴포넌트 마운트 시 새로고침 활성화
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
      const response = await api.get('/places/', { params })
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
      const response = await api.get('/plans/range', {
        params: { start: startDate, end: endDate, user_id: userId }
      })
      return response.data
    },
    enabled: !!(startDate && endDate && userId)
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
    }
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
    mutationFn: async (data: MealPlanRequest & { user_id: string }) => {
      const response = await api.post('/plans/generate', data, {
        params: { user_id: data.user_id }
      })
      return response.data
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
