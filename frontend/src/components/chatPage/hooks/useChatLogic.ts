import { useState, useRef, useEffect, useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { useProfileStore } from '@/store/profileStore'
import { useAuthStore } from '@/store/authStore'
import { useSendMessage, useGetChatThreads, useGetChatHistory, useCreateNewThread, useDeleteThread, ChatHistory, ChatThread, useCreatePlan, useParseDateFromMessage } from '@/hooks/useApi'
import { useQueryClient } from '@tanstack/react-query'

export function useChatLogic() {
  // 상태 관리
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)
  const [isSavingMeal, setIsSavingMeal] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null)
  const [selectedPlaceIndexByMsg, setSelectedPlaceIndexByMsg] = useState<Record<string, number | null>>({})
  const [isLoadingThread, setIsLoadingThread] = useState(false)
  const [isThread, setIsThread] = useState(false)
  // 직전 로그인 상태 추적 (실제 로그아웃 전환만 감지하기 위함)
  const prevIsLoggedInRef = useRef<boolean>(false)

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // 라우터
  const location = useLocation()
  
  // 스토어
  const { profile, loadProfile } = useProfileStore()
  const { user, ensureGuestId, isGuest } = useAuthStore()

  // API 훅들
  const sendMessage = useSendMessage()
  const createNewThread = useCreateNewThread()
  const deleteThread = useDeleteThread()
  const createPlan = useCreatePlan()
  const parseDateFromMessage = useParseDateFromMessage()
  const queryClient = useQueryClient()

  // 로그인 상태 확인 (isGuest 상태도 고려)
  const isLoggedIn = useMemo(() => !!user?.id && !isGuest, [user?.id, isGuest])
  
  // userId 안정화 (매번 새로운 값으로 인식되어 refetch되는 것 방지)
  const stableUserId = useMemo(() => isLoggedIn ? user?.id : undefined, [isLoggedIn, user?.id])
  
  // 게스트/로그인 사용자별 캐시 키 관리
  const stableCacheKey = useMemo(() => {
    if (!isLoggedIn) {
      return `guest-${ensureGuestId()}` // 게스트는 guest_id 기반
    }
    return currentThreadId || '' // 로그인은 thread_id 기반
  }, [isLoggedIn, currentThreadId, ensureGuestId])

  // 채팅 스레드 관련 훅 (로그인 사용자만) - 수동 호출로 변경
  const { data: chatThreads = [], refetch: refetchThreads } = useGetChatThreads(
    stableUserId,
    undefined
  ) as { data: ChatThread[], refetch: () => void }

  // 로그인 사용자만 백엔드 채팅 히스토리 조회
  const { data: chatHistory = [], refetch: refetchHistory, isLoading: isLoadingHistory } = useGetChatHistory(
    isLoggedIn ? stableCacheKey : '', // 게스트는 빈 문자열로 비활성화
    20
  ) as { data: ChatHistory[], refetch: () => void, isLoading: boolean, error: any }

  // 게스트 사용자용 SessionStorage 기반 채팅 히스토리
  const [guestChatHistory, setGuestChatHistory] = useState<ChatHistory[]>([])
  
  // 게스트 사용자 ID 보장 및 SessionStorage에서 채팅 히스토리 로드
  useEffect(() => {
    if (!isLoggedIn) {
      const guestId = ensureGuestId()
      console.log('🎭 게스트 사용자 ID 보장:', guestId)
      console.log('🔍 ensureGuestId 함수 타입:', typeof ensureGuestId)
      console.log('🔍 useChatLogic 게스트 상태:', { isLoggedIn, isGuest, hasUser: !!user })
      console.log('🎭 게스트 사용자 - SessionStorage만 사용, 백엔드 API 호출 안함')
      
      // SessionStorage에서 게스트 채팅 히스토리 로드
      const loadGuestHistory = () => {
        console.log('🔍 loadGuestHistory 호출됨, guestId:', guestId)
        if (guestId) {
          try {
            const key = `guest-chat-${guestId}`
            console.log('🔍 SessionStorage 키:', key)
            const stored = sessionStorage.getItem(key)
            console.log('🔍 SessionStorage 저장된 데이터:', stored)
            if (stored) {
              const parsedHistory = JSON.parse(stored)
              console.log('🔍 파싱된 히스토리:', parsedHistory)
              setGuestChatHistory(parsedHistory)
              console.log('🎭 SessionStorage에서 게스트 채팅 히스토리 로드:', parsedHistory.length, '개')
            } else {
              setGuestChatHistory([])
              console.log('🎭 SessionStorage에 게스트 채팅 히스토리 없음')
            }
          } catch (error) {
            console.error('🎭 SessionStorage 파싱 오류:', error)
            setGuestChatHistory([])
          }
        }
      }
      
      // 초기 로드
      loadGuestHistory()
      
      // SessionStorage 변경 감지를 위한 주기적 체크 (더 자주 체크)
      const interval = setInterval(() => {
        try {
          const stored = sessionStorage.getItem(`guest-chat-${guestId}`)
          if (stored) {
            const parsedHistory = JSON.parse(stored)
            setGuestChatHistory(prev => {
              // 상태가 다를 때만 업데이트
              if (JSON.stringify(prev) !== JSON.stringify(parsedHistory)) {
                console.log('🎭 주기적 체크로 게스트 채팅 히스토리 업데이트:', parsedHistory.length, '개')
                return parsedHistory
              }
              return prev
            })
          }
        } catch (error) {
          console.error('🎭 SessionStorage 주기적 체크 오류:', error)
        }
      }, 500) // 0.5초마다 체크
      
      return () => clearInterval(interval)
    }
  }, [isLoggedIn, ensureGuestId, isGuest, user])
  
  
  // 통합된 채팅 히스토리 (로그인: 백엔드, 게스트: SessionStorage)
  const unifiedChatHistory = useMemo(() => {
    console.log('🔍 unifiedChatHistory 계산:', { isLoggedIn, chatHistoryLength: chatHistory.length, guestChatHistoryLength: guestChatHistory.length })
    if (isLoggedIn) {
      console.log('🔍 로그인 사용자 - chatHistory 반환:', chatHistory)
      return chatHistory // 로그인 사용자: 백엔드에서 조회
    } else {
      console.log('🔍 게스트 사용자 - guestChatHistory 반환:', guestChatHistory)
      return guestChatHistory // 게스트 사용자: SessionStorage에서 조회
    }
  }, [isLoggedIn, chatHistory, guestChatHistory])

  // chatHistory를 messages 형태로 변환 (하위 호환성)
  const messages = useMemo(() => {
    console.log('🔍 messages 계산:', { unifiedChatHistoryLength: unifiedChatHistory.length, unifiedChatHistory })
    const result = unifiedChatHistory.map((msg: any) => ({
      id: msg.id?.toString() || '',
      role: msg.role,
      content: msg.message,
      timestamp: new Date(msg.created_at)
    }))
    console.log('🔍 변환된 messages:', result)
    return result
  }, [unifiedChatHistory])
  
  console.log('🔍 useGetChatHistory 상태:', {
    currentThreadId,
    chatHistoryLength: chatHistory.length,
    chatHistory: chatHistory.map(msg => ({ id: msg.id, message: msg.message })),
    isLoadingHistory
  })
  
  // 프로필 데이터 로드
  useEffect(() => {
    if (user?.id) {
      loadProfile(user.id)
    }
  }, [user?.id, loadProfile])
  // 스레드 상태 감지 및 관리 (로그인/게스트 분기)
  useEffect(() => {
    let hasThread = false

    if (isLoggedIn) {
      // 로그인 사용자: currentThreadId 존재 여부로 판단
      hasThread = !!currentThreadId
    } else {
      // 게스트 사용자: 로컬 messages 존재 여부로 판단
      hasThread = messages.length > 0
    }

    console.log('🔍 스레드 상태 변경:', {
      isLoggedIn,
      currentThreadId,
      messagesLength: messages.length,
      messages: messages.map(m => ({ id: m.id, role: m.role, content: m.content.substring(0, 20) + '...' })),
      hasThread
    })
    setIsThread(hasThread)
  }, [isLoggedIn, currentThreadId, messages.length])

  // hasStartedChatting 제거 - 채팅 기록이 있으면 DB에서 조회되므로 불필요

  // 게스트 사용자 브라우저 탭 닫을 때만 채팅 데이터 삭제
  // SPA 라우팅 문제로 인해 완전히 비활성화
  useEffect(() => {
    if (!isLoggedIn) {
      console.log('🎭 게스트 사용자 - 탭 닫기 감지 완전 비활성화 (SPA 라우팅 문제 해결)')

      // beforeunload 이벤트를 완전히 제거하여 SPA 라우팅에서 세션 스토리지가 사라지는 문제 해결
      // 실제 탭 닫기는 브라우저가 자동으로 세션 스토리지를 정리하므로 수동으로 할 필요 없음
    }
  }, [isLoggedIn])

  // 게스트 사용자 메시지 상태 디버깅 (SessionStorage 무관)
  useEffect(() => {
    if (!isLoggedIn) {
      console.log('🎭 게스트 사용자 메시지 상태 (messages 기반):', { 
        messagesCount: messages.length, 
        isLoggedIn, 
        currentThreadId,
        location: location.pathname,
        isLoadingHistory,
        chatHistoryLength: chatHistory.length,
        messages: messages.map(m => ({ id: m.id, role: m.role, content: m.content.substring(0, 30) + '...' }))
      })
    }
  }, [messages.length, isLoggedIn, currentThreadId, location.pathname, isLoadingHistory, chatHistory.length])

  // 로그인 시 게스트 SessionStorage 정리
  useEffect(() => {
    if (isLoggedIn && typeof window !== 'undefined') {
      // 로그인 성공 시 모든 게스트 SessionStorage 데이터 정리
      const sessionKeys = Object.keys(sessionStorage)
      const guestKeys = sessionKeys.filter(key => key.startsWith('guest-chat-'))
      
      if (guestKeys.length > 0) {
        console.log('🗑️ 로그인 성공 - 게스트 SessionStorage 데이터 정리:', guestKeys)
        guestKeys.forEach(key => {
          sessionStorage.removeItem(key)
        })
        
        // 게스트 채팅 히스토리 상태도 초기화
        setGuestChatHistory([])
      }
    }
  }, [isLoggedIn])

  // 기존 LocalStorage에 잘못 저장된 게스트 데이터 정리
  useEffect(() => {
    if (!isLoggedIn && typeof window !== 'undefined') {
      // 게스트 사용자인데 LocalStorage에 데이터가 있으면 정리
      const localData = localStorage.getItem('keto-coach-chat')
      if (localData) {
        console.log('🗑️ 게스트 사용자 LocalStorage 데이터 정리')
        localStorage.removeItem('keto-coach-chat')
      }
    }
  }, [isLoggedIn])

  // 게스트 사용자는 다른 페이지로 이동해도 채팅 유지 (브라우저 닫을 때만 삭제)

  // 위치 정보 가져오기
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({ lat: position.coords.latitude, lng: position.coords.longitude })
        },
        () => {
          setUserLocation({ lat: 37.4979, lng: 127.0276 }) // 강남역 기본값
        }
      )
    } else {
      setUserLocation({ lat: 37.4979, lng: 127.0276 })
    }
  }, [])

  // 로그인 상태 변화 감지 (한 번만 실행)
  const prevUserIdRef = useRef<string | undefined>(undefined)
  const userId = user?.id
  useEffect(() => {
    console.log('🔍 로그인 상태 체크:', { user: !!user, isGuest, isLoggedIn })

    // 로그인 상태가 변경된 경우에만 실행 (게스트 → 로그인)
    if (userId && !isGuest && prevUserIdRef.current !== userId) {
      console.log('🔐 로그인 감지 - 채팅 데이터 초기화')
      prevUserIdRef.current = userId

      setCurrentThreadId(null)
      setSelectedPlaceIndexByMsg({})

      // 스레드 목록 수동 로드 (한 번만)
      refetchThreads()

      // 게스트 사용자 SessionStorage 데이터 정리 (실제 로그인 시에만)
      if (typeof window !== 'undefined' && userId) {
        sessionStorage.removeItem('keto-coach-chat-guest')
        console.log('🗑️ 게스트 사용자 SessionStorage 데이터 정리 완료')
      }

      console.log('✅ 로그인 후 채팅 데이터 초기화 완료')
    } else {
      console.log('🎭 게스트 사용자 상태 유지 또는 로그인 아님')
    }
  }, [userId, isGuest])

  // 스레드 목록이 로드되면 첫 번째 스레드 자동 선택 (로그인 사용자만)
  // 스레드 삭제 후 다른 스레드가 있으면 자동 선택
  const firstThreadId = chatThreads[0]?.id
  useEffect(() => {
    if (isLoggedIn && firstThreadId && !currentThreadId) {
      console.log('🔄 스레드 자동 선택:', chatThreads[0])
      setCurrentThreadId(firstThreadId)
    }
  }, [isLoggedIn, firstThreadId, currentThreadId, setCurrentThreadId])

  // 스레드가 선택되면 채팅 히스토리 수동 로드
  const prevCacheKeyRef = useRef<string>('')
  useEffect(() => {
    if (stableCacheKey && stableCacheKey !== prevCacheKeyRef.current) {
      console.log('📝 캐시 키 변경됨 - 채팅 히스토리 로드:', stableCacheKey)
      prevCacheKeyRef.current = stableCacheKey
      refetchHistory()
    }
  }, [stableCacheKey, refetchHistory])

  // 채팅 히스토리 로딩 로직
  useEffect(() => {
    // 캐시 키가 변경되었을 때 로딩 시작
    if (stableCacheKey) {
      setIsLoadingThread(true)
    }
    
    // 로딩 완료
    setIsLoadingThread(false)
  }, [stableCacheKey, chatHistory])

  // 게스트 사용자는 스레드 개념이 없으므로 별도 로딩 관리 불필요

  // 실제 로그인 → 로그아웃 전환에서만 초기화 (게스트에는 영향 없음)
  useEffect(() => {
    const wasLoggedIn = prevIsLoggedInRef.current
    if (wasLoggedIn && !isLoggedIn) {
      console.log('🔻 실제 로그아웃 전환 감지 - 채팅 초기화 진행')
      setCurrentThreadId(null)
    }
    prevIsLoggedInRef.current = isLoggedIn
  }, [isLoggedIn])

  // 메시지 변경 시 자동 스크롤
  useEffect(() => {
    if (shouldAutoScroll) {
      const container = scrollAreaRef.current
      if (container) {
        requestAnimationFrame(() => {
          container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
        })
      }
    }
  }, [messages.length, shouldAutoScroll])

  // 초기 스크롤 설정
  useEffect(() => {
    const container = scrollAreaRef.current
    if (container) {
      requestAnimationFrame(() => {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
      })
    }
    setShouldAutoScroll(true)
  }, [])

  return {
    // 상태
    message,
    setMessage,
    isLoading,
    setIsLoading,
    currentThreadId,
    setCurrentThreadId,
    shouldAutoScroll,
    setShouldAutoScroll,
    isSavingMeal,
    setIsSavingMeal,
    isSaving,
    setIsSaving,
    userLocation,
    selectedPlaceIndexByMsg,
    setSelectedPlaceIndexByMsg,
    isLoadingThread,
    setIsLoadingThread,
    
    // Refs
    messagesEndRef,
    scrollAreaRef,
    
    // 스토어
    messages,
    profile,
    user,
    ensureGuestId,
    isGuest,
    
    // API 훅들
    sendMessage,
    createNewThread,
    deleteThread,
    createPlan,
    parseDateFromMessage,
    queryClient,
    
    // 데이터
    chatThreads,
    refetchThreads,
    chatHistory,
    refetchHistory,
    
    // 계산된 값
    isLoggedIn,
    isLoadingHistory,
    isThread
  }
}
