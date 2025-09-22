import { useMutation, useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, ''); // 끝 슬래시 제거

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,   // ← Railway 도메인 + /api/v1
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});
console.log('API_BASE =', API_BASE);
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
}

export interface ChatResponse {
  response: string
  intent: string
  results?: any[]
  tool_calls?: Array<{
    tool: string
    [key: string]: any
  }>
}

export function useSendMessage() {
  return useMutation({
    mutationFn: async (data: ChatRequest): Promise<ChatResponse> => {
      const response = await api.post('/chat/', data)
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
  refId: string
  title: string
  macros?: any
  location?: any
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
