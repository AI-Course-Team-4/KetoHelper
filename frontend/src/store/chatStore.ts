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
  updateMessage: (id: string, partial: Partial<ChatMessage>) => void
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
        console.log('📝 ChatStore: 메시지 추가', { messageId: message.id, role: message.role, content: message.content.substring(0, 50) + '...' })
        set((state) => ({
          messages: [...state.messages, message]
        }))
      },
      
      updateMessage: (id, partial) => {
        set((state) => ({
          messages: state.messages.map(m => m.id === id ? { ...m, ...partial } : m)
        }))
      },
      
      clearMessages: () => {
        console.trace("chatStore.clearMessages")
        console.log('🗑️ ChatStore: 메시지 클리어', { currentMessagesCount: get().messages.length })
        set((state) => {
          if (state.messages.length === 0) return state // 변화 없으면 그대로
          return { ...state, messages: [], currentSessionId: null }
        })
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
      storage: typeof window !== 'undefined' ? {
            getItem: (name) => {
              // authStore에서 게스트 상태 확인
              const authData = localStorage.getItem('keto-auth')
              let isGuest = true // 기본값을 게스트로 설정
              
              if (authData) {
                try {
                  const parsed = JSON.parse(authData)
                  // user가 없으면 게스트 사용자로 판단
                  isGuest = !parsed.state?.user
                  console.log('🔍 게스트 판단:', { 
                    hasUser: !!parsed.state?.user, 
                    isGuest, 
                    authData: parsed.state 
                  })
                } catch (e) {
                  console.error('Auth 데이터 파싱 실패:', e)
                }
              }
              
              if (isGuest) {
                console.log('📖 게스트 사용자 - SessionStorage에서 읽기')
                const str = sessionStorage.getItem(name + '-guest')
                if (!str) return null
                return JSON.parse(str)
              } else {
                console.log('📖 로그인 사용자 - LocalStorage에서 읽기')
                const str = localStorage.getItem(name)
                if (!str) return null
                return JSON.parse(str)
              }
            },
        setItem: (name, value) => {
          // authStore에서 게스트 상태 확인
          const authData = localStorage.getItem('keto-auth')
          let isGuest = true // 기본값을 게스트로 설정
          
          if (authData) {
            try {
              const parsed = JSON.parse(authData)
              // user가 없으면 게스트 사용자로 판단
              isGuest = !parsed.state?.user
              console.log('🔍 게스트 판단 (setItem):', { 
                hasUser: !!parsed.state?.user, 
                isGuest, 
                authData: parsed.state 
              })
            } catch (e) {
              console.error('Auth 데이터 파싱 실패:', e)
            }
          }
          
          if (isGuest) {
            const messageCount = (value as any)?.messages?.length || 0
            console.log('💾 게스트 사용자 - SessionStorage에 저장', { name: name + '-guest', messageCount })
            sessionStorage.setItem(name + '-guest', JSON.stringify(value))
            // 세션 스토리지가 안정적으로 유지되므로 백업 로직 제거
            // localStorage.setItem(name + '-guest-backup', JSON.stringify(value))
          } else {
            const messageCount = (value as any)?.messages?.length || 0
            console.log('💾 로그인 사용자 - LocalStorage에 저장', { name, messageCount })
            localStorage.setItem(name, JSON.stringify(value))
          }
        },
        removeItem: (name) => {
          localStorage.removeItem(name)
          sessionStorage.removeItem(name + '-guest')
        }
      } : undefined,
      onRehydrateStorage: () => (state) => {
        if (state) {
          // 최근 50개 메시지만 유지
          if (state.messages.length > 50) {
            state.messages = state.messages.slice(-50)
          }
        }
        
        // 게스트 사용자인 경우 SessionStorage에서 데이터 로드
        if (typeof window !== 'undefined') {
          const authData = localStorage.getItem('keto-auth')
          let isGuest = true
          
          if (authData) {
            try {
              const parsed = JSON.parse(authData)
              // user가 없으면 게스트 사용자로 판단
              isGuest = !parsed.state?.user
            } catch (e) {
              console.error('Auth 데이터 파싱 실패:', e)
            }
          }
          
          if (isGuest) {
            console.log('🔄 게스트 사용자 - SessionStorage에서 데이터 로드 시도')
            const guestData = sessionStorage.getItem('keto-coach-chat-guest')
            if (guestData) {
              try {
                const parsed = JSON.parse(guestData)
                console.log('📖 게스트 SessionStorage 데이터 로드 성공:', { messageCount: parsed.messages?.length || 0 })
                // onRehydrateStorage에서는 직접 할당만 하고, 실제 복원은 useChatLogic에서 처리
                if (parsed.messages && parsed.messages.length > 0 && state) {
                  console.log('📝 onRehydrateStorage: 게스트 데이터 발견, useChatLogic에서 복원 예정')
                  // 직접 할당하지 않고 로그만 출력
                  console.log('📝 게스트 데이터 발견, useChatLogic에서 복원 예정')
                }
              } catch (e) {
                console.error('게스트 데이터 파싱 실패:', e)
              }
            } else {
              console.log('📭 게스트 SessionStorage에 데이터 없음')
              // 세션 스토리지가 안정적으로 유지되므로 백업 복구 로직 제거
            }
          }
        }
      }
    }
  )
)
