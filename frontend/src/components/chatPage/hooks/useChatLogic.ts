import { useState, useRef, useEffect, useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { useChatStore } from '@/store/chatStore'
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

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // 라우터
  const location = useLocation()
  
  // 스토어
  const { messages, addMessage, clearMessages } = useChatStore()
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

  // 게스트 사용자 ID 보장 및 SessionStorage에서 데이터 복원
  useEffect(() => {
    if (!isLoggedIn) {
      const guestId = ensureGuestId()
      console.log('🎭 게스트 사용자 ID 보장:', guestId)
      console.log('🔍 useChatLogic 게스트 상태:', { isLoggedIn, isGuest, hasUser: !!user })
      
      // 게스트 사용자는 messages 배열만으로 판단 (SessionStorage 복원 의존하지 않음)
      console.log('🎭 게스트 사용자 - messages 배열로 상태 판단:', { messageCount: messages.length })
    }
  }, [isLoggedIn, ensureGuestId, isGuest, user, addMessage])

  // 채팅 스레드 관련 훅 (로그인 사용자만)
  const { data: chatThreads = [], refetch: refetchThreads } = useGetChatThreads(
    isLoggedIn ? user?.id : undefined, 
    isLoggedIn ? undefined : undefined
  ) as { data: ChatThread[], refetch: () => void }

  const { data: chatHistory = [], refetch: refetchHistory, isLoading: isLoadingHistory } = useGetChatHistory(
    isLoggedIn ? (currentThreadId || '') : '',
    20
  ) as { data: ChatHistory[], refetch: () => void, isLoading: boolean, error: any }
  
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
      hasThread,
      '이전 isThread': isThread
    })
    setIsThread(hasThread)
  }, [isLoggedIn, currentThreadId, messages.length, isThread])

  // hasStartedChatting 제거 - 채팅 기록이 있으면 DB에서 조회되므로 불필요

  // 게스트 사용자 브라우저 탭 닫을 때만 채팅 데이터 삭제
  useEffect(() => {
    if (!isLoggedIn) {
      const handleBeforeUnload = () => {
        console.log('🚪 게스트 사용자 브라우저 탭 닫기 - 채팅 데이터 삭제')
        clearMessages()
        // SessionStorage도 삭제
        if (typeof window !== 'undefined') {
          sessionStorage.removeItem('keto-coach-chat-guest')
        }
      }

      window.addEventListener('beforeunload', handleBeforeUnload)
      
      return () => {
        window.removeEventListener('beforeunload', handleBeforeUnload)
      }
    }
  }, [isLoggedIn, clearMessages])

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

  // 로그인 상태 변화 감지
  useEffect(() => {
    if (user && !isGuest) {
      console.log('🔐 로그인 감지 - 채팅 데이터 초기화')
      clearMessages()
      setCurrentThreadId(null)
      refetchThreads()
      setSelectedPlaceIndexByMsg({})
      
      // 게스트 사용자 SessionStorage 데이터 정리
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem('keto-coach-chat-guest')
        console.log('🗑️ 게스트 사용자 SessionStorage 데이터 정리 완료')
      }
      
      console.log('✅ 로그인 후 채팅 데이터 초기화 완료')
    }
  }, [user, isGuest, clearMessages, refetchThreads])

  // 스레드 목록이 로드되면 첫 번째 스레드 자동 선택 (로그인 사용자만)
  // 스레드 삭제 후 다른 스레드가 있으면 자동 선택
  useEffect(() => {
    if (isLoggedIn && chatThreads.length > 0 && !currentThreadId) {
      console.log('🔄 스레드 자동 선택:', chatThreads[0])
      setCurrentThreadId(chatThreads[0].id)
    }
  }, [isLoggedIn, chatThreads, currentThreadId])

  // 채팅 히스토리 로딩 로직
  useEffect(() => {
    // 로그인하지 않은 경우 무시
    if (!isLoggedIn) {
      setIsLoadingThread(false)
      return
    }
    
    // 스레드가 변경되었을 때 로딩 시작
    if (currentThreadId) {
      setIsLoadingThread(true)
    }
    
    // 로그인한 사용자는 DB 메시지만 사용하므로 로컬 동기화 불필요
    
    // 로딩 완료
    setIsLoadingThread(false)
  }, [currentThreadId, chatHistory, isLoggedIn])

  // 로그인한 사용자의 경우 메시지 동기화는 첫 번째 useEffect에서 처리

  // 게스트 사용자의 경우 스레드 변경 시 로딩 상태 관리
  useEffect(() => {
    if (!isLoggedIn && currentThreadId) {
      // 게스트 사용자의 경우 로딩 시작
      setIsLoadingThread(true)
      
      // 약간의 지연 후 로딩 완료
      const timer = setTimeout(() => {
        setIsLoadingThread(false)
      }, 300)

      return () => clearTimeout(timer)
    }
  }, [currentThreadId, isLoggedIn])

  // 로그아웃 시 채팅 초기화 (게스트 사용자는 제외)
  useEffect(() => {
    if (!isLoggedIn && !isGuest) {
      // 로그인 사용자가 로그아웃한 경우만 초기화
      clearMessages()
      setCurrentThreadId(null)
    }
  }, [isLoggedIn, isGuest, clearMessages, setCurrentThreadId])

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
    addMessage,
    clearMessages,
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
