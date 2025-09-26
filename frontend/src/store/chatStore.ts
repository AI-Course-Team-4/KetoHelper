import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface LLMParsedMeal {
  breakfast: string
  lunch: string
  dinner: string
  snack?: string
  date?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  results?: any[]
  timestamp: Date
  sessionId?: string
  mealData?: LLMParsedMeal | null  // 식단 데이터 추가
}

interface ChatState {
  messages: ChatMessage[]
  currentSessionId: string | null
  isLoading: boolean
  
  // Actions
  addMessage: (message: ChatMessage) => void
  clearMessages: () => void
  setLoading: (loading: boolean) => void
  setSessionId: (sessionId: string) => void
  getMessagesForSession: (sessionId: string) => ChatMessage[]
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      currentSessionId: null,
      isLoading: false,
      
      addMessage: (message) => {
        set((state) => ({
          messages: [...state.messages, message]
        }))
      },
      
      clearMessages: () => {
        console.log('🗑️ ChatStore: 메시지 클리어')
        set({ messages: [], currentSessionId: null })
      },
      
      setLoading: (loading) => {
        set({ isLoading: loading })
      },
      
      setSessionId: (sessionId) => {
        set({ currentSessionId: sessionId })
      },
      
      getMessagesForSession: (sessionId) => {
        return get().messages.filter(msg => msg.sessionId === sessionId)
      }
    }),
    {
      name: 'keto-coach-chat',
      partialize: (state) => ({
        messages: state.messages.slice(-50) // 최근 50개만 저장
      })
    }
  )
)
