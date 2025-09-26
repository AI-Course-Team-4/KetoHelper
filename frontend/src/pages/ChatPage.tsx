import { useState, useRef, useEffect } from 'react'
import { Send, Message, Delete, AccessTime, CalendarToday, Save, Add, Person } from '@mui/icons-material'
import { CircularProgress } from '@mui/material'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
// ScrollArea는 MUI Box로 대체 예정
import { useChatStore, ChatMessage, LLMParsedMeal } from '@/store/chatStore'
import { useProfileStore } from '@/store/profileStore'
import { useAuthStore } from '@/store/authStore'
// import { RecipeCard } from '@/components/RecipeCard'
import { PlaceCard } from '@/components/PlaceCard'
import { useSendMessage, useGetChatThreads, useGetChatHistory, useCreateNewThread, useDeleteThread, ChatHistory, useCreatePlan, useParseDateFromMessage, ParsedDateInfo } from '@/hooks/useApi'
import { useQueryClient } from '@tanstack/react-query'
import { MealParserService } from '@/lib/mealService'
import { format } from 'date-fns'

import KakaoMap from './KakaoMap'


// Message 타입을 ChatMessage로 대체


export function ChatPage() {
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null) // 현재 스레드 ID 추가
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)
  const [isSavingMeal, setIsSavingMeal] = useState<string | null>(null) // 저장 중인 메시지 ID
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null)
  const [selectedPlaceIndexByMsg, setSelectedPlaceIndexByMsg] = useState<Record<string, number | null>>({})

  const { messages, addMessage, clearMessages } = useChatStore()
  // hasStartedChatting을 메시지 존재 여부로 계산
  const hasStartedChatting = messages.length > 0
  const { profile } = useProfileStore()
  const { user, ensureGuestId, isGuest } = useAuthStore()
  const sendMessage = useSendMessage()
  const createNewThread = useCreateNewThread()
  const deleteThread = useDeleteThread()
  const createPlan = useCreatePlan()
  const parseDateFromMessage = useParseDateFromMessage()
  const queryClient = useQueryClient()
  
  // 채팅 스레드 관련 훅 추가
  const { data: chatThreads = [], refetch: refetchThreads } = useGetChatThreads(
    user?.id, 
    !user?.id ? ensureGuestId() : undefined
  )
  
  const { data: chatHistory = [], refetch: refetchHistory } = useGetChatHistory(
    currentThreadId || '',
    20
  )

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

  // 로그인 상태 변화 감지 - 게스트에서 로그인으로 전환 시 채팅 데이터 초기화
  useEffect(() => {
    if (user && !isGuest) {
      console.log('🔐 로그인 감지 - 채팅 데이터 초기화')
      
      // 채팅 메시지 클리어
      clearMessages()
      
      // 현재 스레드 ID 초기화
      setCurrentThreadId(null)
      
      // 스레드 목록 새로고침 (로그인 사용자용)
      refetchThreads()
      
      // 선택된 장소 인덱스 초기화
      setSelectedPlaceIndexByMsg({})
      
      console.log('✅ 로그인 후 채팅 데이터 초기화 완료')
    }
  }, [user, isGuest, clearMessages, refetchThreads])

  // 페이지 로드 시 이전 대화 불러오기
  useEffect(() => {
    const loadPreviousChat = async () => {
      try {
        // 스레드 목록이 로드되면 가장 최근 스레드 선택
        if (chatThreads.length > 0 && !currentThreadId) {
          const latestThread = chatThreads[0]
          setCurrentThreadId(latestThread.id)
        }
      } catch (error) {
        console.error('이전 대화 불러오기 실패:', error)
      }
    }

    loadPreviousChat()
  }, [chatThreads, currentThreadId])

  // 채팅 히스토리가 로드되면 메시지 스토어에 추가
  useEffect(() => {
    if (chatHistory.length > 0) {
      // 기존 메시지 클리어
      clearMessages()
      
      // 히스토리 메시지를 ChatMessage 형태로 변환하여 추가
      chatHistory.forEach((msg: ChatHistory) => {
        const chatMessage: ChatMessage = {
          id: msg.id.toString(),
          role: msg.role as 'user' | 'assistant',
          content: msg.message,
          timestamp: new Date(msg.created_at)
        }
        addMessage(chatMessage)
      })
    }
  }, [chatHistory, clearMessages, addMessage])

  // 시간 포맷팅 함수들
  const formatMessageTime = (timestamp: Date) => {
    // timestamp가 Date 객체인지 확인하고 변환
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()

    // 1분 미만
    if (diff < 60000) return '방금 전'

    // 1시간 미만
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000)
      return `${minutes}분 전`
    }

    // 24시간 미만
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000)
      return `${hours}시간 전`
    }

    // 7일 미만
    if (diff < 604800000) {
      const days = Math.floor(diff / 86400000)
      return `${days}일 전`
    }

    // 그 이상은 날짜로 표시
    return date.toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDetailedTime = (timestamp: Date) => {
    // timestamp가 Date 객체인지 확인하고 변환
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const shouldShowTimestamp = (currentIndex: number) => {
    if (currentIndex === 0) return true

    const currentMessage = messages[currentIndex]
    const previousMessage = messages[currentIndex - 1]

    if (!currentMessage || !previousMessage) return true

    // timestamp가 Date 객체인지 확인하고 변환
    const currentTime = currentMessage.timestamp instanceof Date ? currentMessage.timestamp : new Date(currentMessage.timestamp)
    const previousTime = previousMessage.timestamp instanceof Date ? previousMessage.timestamp : new Date(previousMessage.timestamp)

    const timeDiff = currentTime.getTime() - previousTime.getTime()

    // 5분 이상 차이나면 타임스탬프 표시
    return timeDiff > 300000
  }

  const shouldShowDateSeparator = (currentIndex: number) => {
    if (currentIndex === 0) return true

    const currentMessage = messages[currentIndex]
    const previousMessage = messages[currentIndex - 1]

    if (!currentMessage || !previousMessage) return false

    // timestamp가 Date 객체인지 확인하고 변환
    const currentTime = currentMessage.timestamp instanceof Date ? currentMessage.timestamp : new Date(currentMessage.timestamp)
    const previousTime = previousMessage.timestamp instanceof Date ? previousMessage.timestamp : new Date(previousMessage.timestamp)

    const currentDate = currentTime.toDateString()
    const previousDate = previousTime.toDateString()

    return currentDate !== previousDate
  }

  const formatDateSeparator = (timestamp: Date) => {
    // timestamp가 Date 객체인지 확인하고 변환
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp)

    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 86400000)
    const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())

    if (messageDate.getTime() === today.getTime()) {
      return '오늘'
    } else if (messageDate.getTime() === yesterday.getTime()) {
      return '어제'
    } else {
      return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }
  }

  const scrollToBottom = () => {
    if (!shouldAutoScroll || !scrollAreaRef.current) return
    const container = scrollAreaRef.current as HTMLDivElement
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
  }

  const handleScroll = () => {
    const container = scrollAreaRef.current
    if (!container) return

    const { scrollTop, scrollHeight, clientHeight } = container
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50

    setShouldAutoScroll(isAtBottom)
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, shouldAutoScroll])

  useEffect(() => {
    const container = scrollAreaRef.current
    if (container) {
      container.addEventListener('scroll', handleScroll)
      return () => container.removeEventListener('scroll', handleScroll)
    }
  }, [hasStartedChatting])

  useEffect(() => {
    // 페이지 진입 시 채팅 컴포넌트 내부 스크롤을 부드럽게 맨 아래로 이동
    const container = scrollAreaRef.current
    if (container) {
      requestAnimationFrame(() => {
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
      })
    }
    setShouldAutoScroll(true)
  }, [])

  // 새 채팅 세션 생성
  const createNewChat = async () => {
    try {
      // 새 스레드 생성
      const newThread = await createNewThread.mutateAsync({
        userId: user?.id,
        guestId: !user?.id ? ensureGuestId() : undefined
      })
      
      // 상태 업데이트
      setCurrentThreadId(newThread.id)
      clearMessages()
      setMessage('')
      
      // 스레드 목록 새로고침
      refetchThreads()
      // 새 스레드의 히스토리 새로고침 (빈 목록이 될 것)
      refetchHistory()
      
      console.log('🆕 새 채팅 스레드 생성:', newThread.id)
    } catch (error) {
      console.error('❌ 새 스레드 생성 실패:', error)
      // 실패 시에도 UI는 초기화
      setCurrentThreadId(null)
      clearMessages()
      setMessage('')
    }
  }


  // 스레드 선택 함수 추가
  const selectThread = (threadId: string) => {
    setCurrentThreadId(threadId)
    // 현재 메시지 초기화
    clearMessages()
    setMessage('')
    // 해당 스레드의 히스토리를 새로 불러옴
    refetchHistory()
    console.log('🔄 스레드 전환:', threadId)
  }

  // 스레드 삭제 함수 추가
  const handleDeleteThread = async (threadId: string) => {
    if (!confirm('정말로 이 대화를 삭제하시겠습니까?')) {
      return
    }

    try {
      await deleteThread.mutateAsync(threadId)
      
      // 현재 선택된 스레드가 삭제된 경우 새 채팅으로 이동
      if (currentThreadId === threadId) {
        setCurrentThreadId(null)
        clearMessages()
        setMessage('')
      }
      
      // 스레드 목록 새로고침
      refetchThreads()
      
      console.log('🗑️ 스레드 삭제 완료:', threadId)
    } catch (error) {
      console.error('❌ 스레드 삭제 실패:', error)
      alert('스레드 삭제에 실패했습니다. 다시 시도해주세요.')
    }
  }


  const handleSendMessage = async () => {
    if (!message.trim() || isLoading) return
    setShouldAutoScroll(true)

    // 사용자/게스트 ID 준비
    const userId = user?.id
    const guestId = isGuest ? ensureGuestId() : undefined

    // 현재 스레드가 없으면 새로 생성 (백엔드에서 처리)
    let threadId = currentThreadId

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message.trim(),
      timestamp: new Date()
    }

    addMessage(userMessage)
    setMessage('')
    setIsLoading(true)

    try {
      const response = await sendMessage.mutateAsync({
        message: userMessage.content,
        profile: profile ? {
          allergies: profile.allergy_names,
          dislikes: profile.dislike_names,
          goals_kcal: profile.goals_kcal,
          goals_carbs_g: profile.goals_carbs_g
        } : undefined,
        location: undefined, // TODO: 위치 정보 연동
        radius_km: 5,
        thread_id: threadId || undefined,
        user_id: userId,
        guest_id: guestId
      })

      // 응답에서 thread_id 업데이트
      if (response.thread_id && response.thread_id !== threadId) {
        setCurrentThreadId(response.thread_id)
        threadId = response.thread_id
      }

      // 백엔드에서 반환하는 구조화된 meal_plan_data 사용
      let parsedMeal: LLMParsedMeal | null = null
      
      if (response.meal_plan_data && response.meal_plan_data.days && response.meal_plan_data.days.length > 0) {
        // 백엔드에서 구조화된 데이터가 있으면 첫 번째 날 데이터 사용
        const firstDay = response.meal_plan_data.days[0]
        parsedMeal = {
          breakfast: firstDay.breakfast?.title || '',
          lunch: firstDay.lunch?.title || '',
          dinner: firstDay.dinner?.title || '',
          snack: firstDay.snack?.title || ''
        }
        console.log('✅ 백엔드 meal_plan_data 사용:', parsedMeal)
      } else {
        // 백엔드 구조화 데이터가 없으면 기존 파싱 방식 사용
        parsedMeal = MealParserService.parseMealFromBackendResponse(response)
        console.log('⚠️ 기존 파싱 방식 사용:', parsedMeal)
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        results: response.results,
        timestamp: new Date(),
        mealData: parsedMeal // 파싱된 식단 데이터 추가
      }

      addMessage(assistantMessage)

      // 백엔드에서 제공하는 save_to_calendar_data가 있으면 우선 사용
      if (response.save_to_calendar_data && user?.id) {
        console.log('✅ 백엔드 save_to_calendar_data 사용:', response.save_to_calendar_data)
        setTimeout(() => {
          handleBackendCalendarSave(response.save_to_calendar_data!, parsedMeal)
        }, 1000)
      }
      // 백엔드 데이터가 없으면 기존 로직 사용
      else if (parsedMeal && user?.id) {
        const isAutoSaveRequest = (
          userMessage.content.includes('저장') ||
          userMessage.content.includes('추가') ||
          userMessage.content.includes('계획') ||
          userMessage.content.includes('등록') ||
          userMessage.content.includes('넣어')
        ) && (
          userMessage.content.includes('오늘') ||
          userMessage.content.includes('내일') ||
          userMessage.content.includes('모레') ||
          userMessage.content.includes('다음주') ||
          userMessage.content.includes('캘린더') ||
          /\d{1,2}월\s*\d{1,2}일/.test(userMessage.content) ||
          /\d{1,2}일(?![일월화수목금토])/.test(userMessage.content) ||
          /\d+일\s*[후뒤]/.test(userMessage.content)
        )

        if (isAutoSaveRequest) {
          setTimeout(() => {
            handleSmartMealSave(userMessage.content, parsedMeal)
          }, 1000) // 1초 후 자동 저장
        }
      }
      // 현재 메시지에 식단이 없지만 저장 요청이 있는 경우 이전 메시지에서 식단 데이터 찾기
      else if (!parsedMeal && user?.id) {
        const isSaveRequest = (
          userMessage.content.includes('저장') ||
          userMessage.content.includes('추가') ||
          userMessage.content.includes('계획') ||
          userMessage.content.includes('등록') ||
          userMessage.content.includes('넣어')
        )

        if (isSaveRequest) {
          // 현재 메시지를 추가한 후의 전체 메시지 목록에서 이전 식단 데이터 찾기
          const updatedMessages = [...messages, assistantMessage]
          const recentMealData = findRecentMealData(updatedMessages)

          if (recentMealData) {
            setTimeout(() => {
              handleSmartMealSave(userMessage.content, recentMealData, '이전 식단을')
            }, 1000) // 1초 후 자동 저장
          } else {
            // 이전 식단을 찾을 수 없는 경우 안내 메시지
            const noMealMessage: ChatMessage = {
              id: Date.now().toString(),
              role: 'assistant',
              content: '❌ 저장할 식단을 찾을 수 없습니다. 먼저 식단 추천을 받아주세요.',
              timestamp: new Date()
            }
            setTimeout(() => {
              addMessage(noMealMessage)
            }, 500)
          }
        }
      }

      // 스레드 목록 새로고침
      refetchThreads()
    } catch (error) {
      console.error('메시지 전송 실패:', error)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '죄송합니다. 메시지 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date()
      }
      addMessage(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // 식단 캘린더에 저장 (스마트 날짜 파싱 지원)
  const handleSaveMealToCalendar = async (messageId: string, mealData: LLMParsedMeal, targetDate?: string) => {
    if (!user?.id) {
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: '❌ 식단 저장을 위해 로그인이 필요합니다.',
        timestamp: new Date()
      }
      addMessage(errorMessage)
      return
    }

    setIsSavingMeal(messageId)

    try {
      const dateToSave = targetDate || format(new Date(), 'yyyy-MM-dd')

      // 각 식사 시간대별로 개별 plan 생성
      const mealSlots = ['breakfast', 'lunch', 'dinner', 'snack'] as const
      const savedPlans: string[] = []

      for (const slot of mealSlots) {
        const mealTitle = mealData[slot]
        if (mealTitle && mealTitle.trim()) {
          try {
            const planData = {
              user_id: user.id,
              date: dateToSave,
              slot: slot,
              type: 'recipe' as const,
              ref_id: '',
              title: mealTitle.trim(),
              location: undefined,
              macros: undefined,
              notes: undefined
            }

            await createPlan.mutateAsync(planData)
            savedPlans.push(slot)
          } catch (error) {
            console.error(`${slot} 저장 실패:`, error)
          }
        }
      }

      if (savedPlans.length > 0) {
        // 캘린더 데이터 새로고침
        queryClient.invalidateQueries({ queryKey: ['plans-range'] })
        
        // 성공 메시지 추가
        const successMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `✅ 식단이 ${format(new Date(dateToSave), 'M월 d일')} 캘린더에 저장되었습니다! (${savedPlans.join(', ')}) 캘린더 페이지에서 확인해보세요.`,
          timestamp: new Date()
        }

        addMessage(successMessage)
      } else {
        throw new Error('저장할 식단이 없습니다')
      }
    } catch (error) {
      console.error('식단 저장 실패:', error)

      // 실패 메시지 추가
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: '❌ 식단 저장에 실패했습니다. 다시 시도해주세요.',
        timestamp: new Date()
      }

      addMessage(errorMessage)
    } finally {
      setIsSavingMeal(null)
    }
  }

  // 최근 식단 데이터 찾기 (채팅 히스토리에서)
  const findRecentMealData = (messages: ChatMessage[]): LLMParsedMeal | null => {
    // 최근 15개 메시지에서 mealData가 있는 assistant 메시지 검색
    for (let i = messages.length - 1; i >= Math.max(0, messages.length - 15); i--) {
      const msg = messages[i]
      if (msg.role === 'assistant' && msg.mealData) {
        console.log('🔍 최근 식단 데이터 발견:', msg.mealData)
        return msg.mealData
      }
    }
    
    // mealData가 없으면 메시지 내용에서 파싱 시도
    for (let i = messages.length - 1; i >= Math.max(0, messages.length - 15); i--) {
      const msg = messages[i]
      if (msg.role === 'assistant' && msg.content) {
        const parsedMeal = MealParserService.parseMealFromResponse(msg.content)
        if (parsedMeal) {
          console.log('🔍 메시지 내용에서 식단 데이터 파싱 성공:', parsedMeal)
          return parsedMeal
        }
      }
    }
    
    return null
  }

  // 스마트 식단 저장 - 사용자 메시지에서 날짜 파싱 (7일 식단표 지원)
  const handleSmartMealSave = async (userMessage: string, mealData: LLMParsedMeal, prefix: string = '') => {
    if (!user?.id) {
      return
    }

    // 백엔드 API를 통한 날짜 파싱
    let parsedDate: ParsedDateInfo | null = null

    try {
      const parseResult = await parseDateFromMessage.mutateAsync({ message: userMessage })
      if (parseResult.success && parseResult.parsed_date) {
        parsedDate = parseResult.parsed_date
      }
    } catch (error) {
      console.error('날짜 파싱 API 오류:', error)
      // 백엔드에서 폴백 처리가 되므로 여기서는 null로 유지
      parsedDate = null
    }

    if (parsedDate) {
      setIsSavingMeal('auto-save')

      try {
        // 7일 식단표인지 확인 (이전 메시지에서 7일 식단표 요청이 있었는지 확인)
        const recentMessages = messages.slice(-5) // 최근 5개 메시지 확인
        const has7DayMealPlan = recentMessages.some(msg =>
          msg.content.includes('7일') && msg.content.includes('식단') ||
          msg.content.includes('일주일') && msg.content.includes('식단')
        )

        if (has7DayMealPlan && (userMessage.includes('다음주') || userMessage.includes('담주'))) {
          // 7일 식단표를 다음주에 저장 (월요일부터 일요일까지)
          const savedDays: string[] = []
          let successCount = 0

          for (let dayOffset = 0; dayOffset < 7; dayOffset++) {
            const baseDate = new Date(parsedDate.date)
            baseDate.setDate(baseDate.getDate() + dayOffset)
            const dateString = format(baseDate, 'yyyy-MM-dd')

            // 각 식사 시간대별로 개별 plan 생성
            const mealSlots = ['breakfast', 'lunch', 'dinner', 'snack'] as const
            let daySuccessCount = 0

            for (const slot of mealSlots) {
              const mealTitle = mealData[slot]
              if (mealTitle && mealTitle.trim()) {
                try {
                  const planData = {
                    user_id: user.id,
                    date: dateString,
                    slot: slot,
                    type: 'recipe' as const,
                    ref_id: '',
                    title: mealTitle.trim(),
                    location: undefined,
                    macros: undefined,
                    notes: undefined
                  }

                  await createPlan.mutateAsync(planData)
                  daySuccessCount++
                } catch (error) {
                  console.error(`${dateString} ${slot} 저장 실패:`, error)
                }
              }
            }

            if (daySuccessCount > 0) {
              savedDays.push(format(baseDate, 'M/d'))
              successCount += daySuccessCount
            }
          }

          if (successCount > 0) {
            // 캘린더 데이터 새로고침
            queryClient.invalidateQueries({ queryKey: ['plans-range'] })
            
            const successMessage: ChatMessage = {
              id: Date.now().toString(),
              role: 'assistant',
              content: `✅ 7일 키토 식단표가 다음주에 저장되었습니다! 📅\n저장된 날짜: ${savedDays.join(', ')}\n총 ${successCount}개 식단이 등록되었습니다. 캘린더에서 확인해보세요! 🗓️`,
              timestamp: new Date()
            }
            addMessage(successMessage)
          } else {
            throw new Error('7일 식단표 저장에 실패했습니다')
          }
        } else {
          // 단일 날짜 저장 (기존 로직)
          const targetDate = parsedDate.iso_string
          const displayDate = parsedDate.display_string

          const mealSlots = ['breakfast', 'lunch', 'dinner', 'snack'] as const
          const savedPlans: string[] = []

          for (const slot of mealSlots) {
            const mealTitle = mealData[slot]
            if (mealTitle && mealTitle.trim()) {
              try {
                const planData = {
                  user_id: user.id,
                  date: targetDate,
                  slot: slot,
                  type: 'recipe' as const,
                  ref_id: '',
                  title: mealTitle.trim(),
                  location: undefined,
                  macros: undefined,
                  notes: undefined
                }

                await createPlan.mutateAsync(planData)
                savedPlans.push(slot)
              } catch (error) {
                console.error(`${slot} 저장 실패:`, error)
              }
            }
          }

          if (savedPlans.length > 0) {
            // 캘린더 데이터 새로고침
            queryClient.invalidateQueries({ queryKey: ['plans-range'] })
            
            const messagePrefix = prefix ? prefix + ' ' : ''
            const successMessage: ChatMessage = {
              id: Date.now().toString(),
              role: 'assistant',
              content: `✅ ${messagePrefix}${displayDate}에 자동으로 저장했습니다! (${savedPlans.join(', ')}) 캘린더에서 확인해보세요.`,
              timestamp: new Date()
            }
            addMessage(successMessage)
          } else {
            throw new Error('저장할 식단이 없습니다')
          }
        }
      } catch (error) {
        console.error('스마트 식단 저장 실패:', error)
        const errorMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `❌ 식단 저장에 실패했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`,
          timestamp: new Date()
        }
        addMessage(errorMessage)
      } finally {
        setIsSavingMeal(null)
      }
    }
  }

  // 백엔드 캘린더 저장 데이터 처리
  const handleBackendCalendarSave = async (saveData: any, mealData: LLMParsedMeal | null) => {
    if (!user?.id) {
      return
    }

    setIsSavingMeal('auto-save')
    
    try {
      const startDate = new Date(saveData.start_date)
      const durationDays = saveData.duration_days
      const daysData = saveData.days_data || []  // 백엔드에서 준비한 완벽한 일별 데이터
      
      console.log(`🗓️ 백엔드 캘린더 저장: ${durationDays}일치, 시작일: ${startDate.toISOString()}`)
      console.log(`🗓️ 백엔드에서 받은 days_data:`, daysData)
      
      let successCount = 0
      const savedDays: string[] = []
      
      // durationDays만큼 반복해서 저장
      for (let i = 0; i < durationDays; i++) {
        const currentDate = new Date(startDate)
        currentDate.setDate(startDate.getDate() + i)
        const dateString = currentDate.toISOString().split('T')[0]
        
        // 해당 일의 백엔드 데이터 사용, 없으면 기본값
        let dayMeals: any = {}
        if (daysData[i]) {
          dayMeals = daysData[i]
          console.log(`🗓️ ${i+1}일차 백엔드 식단 사용:`, dayMeals)
        } else {
          // fallback: 기본 식단
          dayMeals = mealData || {
            breakfast: '키토 아침 메뉴',
            lunch: '키토 점심 메뉴', 
            dinner: '키토 저녁 메뉴',
            snack: '키토 간식'
          }
        }
        
        // 각 식사 시간대별로 개별 plan 생성
        const mealSlots = ['breakfast', 'lunch', 'dinner', 'snack'] as const
        let daySuccessCount = 0

        for (const slot of mealSlots) {
          // dayMeals 구조에 맞게 mealTitle 추출
          let mealTitle = ''
          if (dayMeals[slot]) {
            if (typeof dayMeals[slot] === 'string') {
              mealTitle = dayMeals[slot]
            } else if (dayMeals[slot]?.title) {
              mealTitle = dayMeals[slot].title
            }
          }
          
          if (mealTitle && mealTitle.trim()) {
            try {
              const planData = {
                user_id: user.id,
                date: dateString,
                slot: slot,
                type: 'recipe' as const,
                ref_id: '',
                title: mealTitle.trim(),
                location: undefined,
                macros: undefined,
                notes: undefined
              }

              await createPlan.mutateAsync(planData)
              daySuccessCount++
            } catch (error) {
              console.error(`${dateString} ${slot} 저장 실패:`, error)
            }
          }
        }

        if (daySuccessCount > 0) {
          savedDays.push(format(currentDate, 'M/d'))
          successCount += daySuccessCount
        }
      }

      // 캘린더 데이터 새로고침
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })
      
      if (successCount > 0) {
        const successMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `✅ ${durationDays}일치 식단표를 캘린더에 저장했습니다! (${savedDays.join(', ')}일)`,
          timestamp: new Date()
        }
        addMessage(successMessage)
      } else {
        throw new Error('식단 저장에 실패했습니다.')
      }
      
    } catch (error) {
      console.error('백엔드 캘린더 저장 실패:', error)
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ 식단 저장에 실패했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`,
        timestamp: new Date()
      }
      addMessage(errorMessage)
    } finally {
      setIsSavingMeal(null)
    }
  }

  // 빠른 질문 메시지 전송
  const handleQuickMessage = async (quickMessage: string) => {
    if (!quickMessage.trim() || isLoading) return
    setShouldAutoScroll(true)

    // 사용자/게스트 ID 준비
    const userId = user?.id
    const guestId = isGuest ? ensureGuestId() : undefined

    // 현재 스레드가 없으면 새로 생성 (백엔드에서 처리)
    let threadId = currentThreadId

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: quickMessage.trim(),
      timestamp: new Date()
    }

    addMessage(userMessage)
    setIsLoading(true)

    try {
      const response = await sendMessage.mutateAsync({
        message: userMessage.content,
        profile: profile ? {
          allergies: profile.allergy_names,
          dislikes: profile.dislike_names,
          goals_kcal: profile.goals_kcal,
          goals_carbs_g: profile.goals_carbs_g
        } : undefined,
        location: undefined, // TODO: 위치 정보 연동
        radius_km: 5,
        thread_id: threadId || undefined,
        user_id: userId,
        guest_id: guestId
      })

      // 응답에서 thread_id 업데이트
      if (response.thread_id && response.thread_id !== threadId) {
        setCurrentThreadId(response.thread_id)
        threadId = response.thread_id
      }

      // 백엔드에서 반환하는 구조화된 meal_plan_data 사용
      let parsedMeal: LLMParsedMeal | null = null
      
      if (response.meal_plan_data && response.meal_plan_data.days && response.meal_plan_data.days.length > 0) {
        // 백엔드에서 구조화된 데이터가 있으면 첫 번째 날 데이터 사용
        const firstDay = response.meal_plan_data.days[0]
        parsedMeal = {
          breakfast: firstDay.breakfast?.title || '',
          lunch: firstDay.lunch?.title || '',
          dinner: firstDay.dinner?.title || '',
          snack: firstDay.snack?.title || ''
        }
        console.log('✅ 백엔드 meal_plan_data 사용:', parsedMeal)
      } else {
        // 백엔드 구조화 데이터가 없으면 기존 파싱 방식 사용
        parsedMeal = MealParserService.parseMealFromBackendResponse(response)
        console.log('⚠️ 기존 파싱 방식 사용:', parsedMeal)
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        results: response.results,
        timestamp: new Date(),
        mealData: parsedMeal // 파싱된 식단 데이터 추가
      }

      addMessage(assistantMessage)

      // 백엔드에서 제공하는 save_to_calendar_data가 있으면 우선 사용
      if (response.save_to_calendar_data && user?.id) {
        console.log('✅ 백엔드 save_to_calendar_data 사용:', response.save_to_calendar_data)
        setTimeout(() => {
          handleBackendCalendarSave(response.save_to_calendar_data!, parsedMeal)
        }, 1000)
      }
      // 백엔드 데이터가 없으면 기존 로직 사용
      else if (parsedMeal && user?.id) {
        const isAutoSaveRequest = (
          userMessage.content.includes('저장') ||
          userMessage.content.includes('추가') ||
          userMessage.content.includes('계획') ||
          userMessage.content.includes('등록') ||
          userMessage.content.includes('넣어')
        ) && (
          userMessage.content.includes('오늘') ||
          userMessage.content.includes('내일') ||
          userMessage.content.includes('모레') ||
          userMessage.content.includes('다음주') ||
          userMessage.content.includes('캘린더') ||
          /\d{1,2}월\s*\d{1,2}일/.test(userMessage.content) ||
          /\d{1,2}일(?![일월화수목금토])/.test(userMessage.content) ||
          /\d+일\s*[후뒤]/.test(userMessage.content)
        )

        if (isAutoSaveRequest) {
          setTimeout(() => {
            handleSmartMealSave(userMessage.content, parsedMeal)
          }, 1000) // 1초 후 자동 저장
        }
      }
      // 현재 메시지에 식단이 없지만 저장 요청이 있는 경우 이전 메시지에서 식단 데이터 찾기
      else if (!parsedMeal && user?.id) {
        const isSaveRequest = (
          userMessage.content.includes('저장') ||
          userMessage.content.includes('추가') ||
          userMessage.content.includes('계획') ||
          userMessage.content.includes('등록') ||
          userMessage.content.includes('넣어')
        )

        if (isSaveRequest) {
          // 현재 메시지를 추가한 후의 전체 메시지 목록에서 이전 식단 데이터 찾기
          const updatedMessages = [...messages, assistantMessage]
          const recentMealData = findRecentMealData(updatedMessages)

          if (recentMealData) {
            setTimeout(() => {
              handleSmartMealSave(userMessage.content, recentMealData, '이전 식단을')
            }, 1000) // 1초 후 자동 저장
          } else {
            // 이전 식단을 찾을 수 없는 경우 안내 메시지
            const noMealMessage: ChatMessage = {
              id: Date.now().toString(),
              role: 'assistant',
              content: '❌ 저장할 식단을 찾을 수 없습니다. 먼저 식단 추천을 받아주세요.',
              timestamp: new Date()
            }
            setTimeout(() => {
              addMessage(noMealMessage)
            }, 500)
          }
        }
      }

      // 스레드 목록 새로고침
      refetchThreads()
    } catch (error) {
      console.error('메시지 전송 실패:', error)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '죄송합니다. 메시지 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date()
      }
      addMessage(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] overflow-hidden">
      {/* 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-gradient">키토 코치</h1>
        <p className="text-muted-foreground mt-1">
          건강한 키토 식단을 위한 AI 어시스턴트
        </p>
      </div>

      {/* 메인 콘텐츠 영역 */}
        <div className="flex flex-1 gap-4 lg:gap-6 min-h-0 overflow-hidden mt-6">
        {/* 왼쪽 사이드바 - 데스크톱에서만 표시 */}
        <div className="hidden lg:block w-80 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl flex flex-col">
          {/* 사이드바 헤더 */}
          <div className="p-6 border-b border-gray-100">
            <Button
              onClick={createNewChat}
              disabled={isLoading}
              className={`w-full justify-center gap-3 h-14 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-300 rounded-xl ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
              variant="default"
            >
              <Add sx={{ fontSize: 20 }} />
              새 채팅 시작
            </Button>

            {/* 여백 추가 */}
            <div className="h-4"></div>

            {/* 채팅 히스토리 */}
            <div className="max-h-[60vh] overflow-y-auto">
              <div className="space-y-3">
                {chatThreads.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mx-auto mb-4">
                      <Message sx={{ fontSize: 32 }} />
                    </div>
                    <p className="text-sm font-medium mb-1">아직 채팅이 없습니다</p>
                    <p className="text-xs opacity-70">새 채팅을 시작해보세요!</p>
                  </div>
                )}

                {chatThreads.map((thread) => (
                  <div
                    key={thread.id}
                    className={`group relative p-4 rounded-xl transition-all duration-300 ${currentThreadId === thread.id
                      ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg border border-green-300'
                      : 'bg-gray-50 hover:bg-green-50 hover:shadow-md border border-gray-200 hover:border-green-200'
                      } ${isLoading ? 'cursor-not-allowed opacity-75' : 'cursor-pointer'}`}
                    onClick={() => {
                      if (!isLoading) {
                        selectThread(thread.id)
                      }
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium truncate mb-1">
                          {thread.title}
                        </h4>
                        <p className={`text-xs ${currentThreadId === thread.id ? 'text-white/70' : 'text-muted-foreground'
                          }`}>
                          {new Date(thread.last_message_at).toLocaleDateString()}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={isLoading}
                        className={`opacity-0 group-hover:opacity-100 h-7 w-7 p-0 transition-opacity duration-200 ${currentThreadId === thread.id ? 'text-white hover:bg-white/20' : 'hover:bg-muted'
                          } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation()
                          if (!isLoading) {
                            handleDeleteThread(thread.id)
                          }
                        }}
                      >
                        <Delete sx={{ fontSize: 12 }} />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 메인 채팅 영역 */}
        <div className="flex-1 flex flex-col bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl min-h-0 w-full lg:w-auto overflow-hidden">
          {!hasStartedChatting ? (
            // 채팅 시작 전 - 가운데 입력창
            <div className="flex-1 flex items-center justify-center p-8 overflow-hidden">
              <div className="w-full max-w-3xl">
                <div className="text-center mb-8 lg:mb-12">
                  <div className="w-28 h-28 lg:w-36 lg:h-36 rounded-full bg-gradient-to-br from-green-500 via-emerald-500 to-teal-500 flex items-center justify-center mx-auto mb-6 lg:mb-8 shadow-2xl ring-4 ring-green-100">
                    <span className="text-5xl lg:text-6xl">🥑</span>
                  </div>
                  <h3 className="text-3xl lg:text-3xl font-bold mb-4 lg:mb-6 bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 bg-clip-text text-transparent">
                    안녕하세요, 키토 코치입니다!
                  </h3>
                  {user ? (
                    <p className="text-gray-600 text-lg lg:text-lg leading-relaxed px-4 max-w-2xl mx-auto">
                      건강한 키토 식단을 위한 모든 것을 도와드릴게요.<br />
                      <span className="font-semibold text-green-700">레시피 추천부터 식당 찾기까지</span> 무엇이든 물어보세요!
                    </p>
                  ) : (
                    <p className="text-gray-600 text-lg lg:text-xl leading-relaxed px-4 max-w-2xl mx-auto">
                      키토 식단 추천을 받으실 수 있습니다.<br />
                      <span className="text-amber-600 font-semibold bg-amber-50 px-3 py-1 rounded-full">식단 저장 기능은 로그인 후 이용 가능합니다.</span>
                    </p>
                  )}
                </div>

                {/* 가운데 입력창 */}
                <div className="space-y-4 lg:space-y-6 px-4">
                  <div className="flex gap-2 lg:gap-3">
                    <div className="flex-1 relative">
                      <Input
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="키토 식단에 대해 무엇이든 물어보세요..."
                        className="h-14 lg:h-16 text-base lg:text-lg pl-6 lg:pl-8 pr-12 lg:pr-16 bg-white border-2 border-gray-200 focus:border-green-400 rounded-3xl shadow-lg focus:shadow-xl transition-all duration-300"
                        disabled={isLoading}
                      />
                      {isLoading && (
                        <div className="absolute right-3 lg:right-4 top-1/2 -translate-y-1/2">
                          <CircularProgress size={20} sx={{ color: 'text.secondary' }} />
                        </div>
                      )}
                    </div>
                    <Button
                      onClick={handleSendMessage}
                      disabled={!message.trim() || isLoading}
                      className="h-14 lg:h-16 px-6 lg:px-8 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold rounded-2xl hover:shadow-xl transition-all duration-300"
                    >
                      <Send className="h-5 w-5 lg:h-6 lg:w-6" />
                    </Button>
                  </div>

                  {/* 빠른 질문 버튼들 */}
                  <div className="flex flex-wrap gap-2 lg:gap-3 justify-center">
                    {[
                      "아침 키토 레시피 추천해줘",
                      "강남역 근처 키토 식당 찾아줘",
                      "7일 키토 식단표 만들어줘",
                      "키토 다이어트 방법 알려줘"
                    ].map((quickMessage) => (
                      <Button
                        key={quickMessage}
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickMessage(quickMessage)}
                        disabled={isLoading}
                        className="text-sm lg:text-base px-4 lg:px-6 py-2 lg:py-3 rounded-xl lg:rounded-2xl border-2 border-green-200 hover:bg-green-50 hover:border-green-300 hover:shadow-lg transition-all duration-300 font-medium text-green-700"
                      >
                        {quickMessage}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // 채팅 시작 후 - 일반 채팅 레이아웃
            <>
              {/* 메시지 영역 - 고정 높이와 스크롤 */}
              <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
                <div ref={scrollAreaRef} className="flex-1 p-4 lg:p-6 overflow-y-auto scroll-smooth">
                  <div className="max-w-4xl mx-auto">
                    <div className="space-y-4 lg:space-y-6">
                      {messages.map((msg: ChatMessage, index: number) => (
                        <div key={msg.id}>
                          {/* 날짜 구분선 */}
                          {shouldShowDateSeparator(index) && (
                            <div className="flex items-center justify-center my-6">
                              <div className="flex items-center gap-3 px-4 py-2 bg-muted/30 rounded-full border border-border/50">
                                <AccessTime sx={{ fontSize: 12, color: 'text.secondary' }} />
                                <span className="text-xs font-medium text-muted-foreground">
                                  {formatDateSeparator(msg.timestamp)}
                                </span>
                              </div>
                            </div>
                          )}

                          <div className={`flex items-start gap-3 lg:gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''
                            }`}>
                            {/* 아바타 */}
                            <div className={`flex-shrink-0 w-10 h-10 lg:w-12 lg:h-12 rounded-full flex items-center justify-center shadow-lg ring-2 overflow-hidden ${msg.role === 'user'
                                ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white ring-blue-200'
                                : 'bg-gradient-to-r from-green-500 to-emerald-500 text-white ring-green-200'
                              }`}>
                              {msg.role === 'user' ? (
                                // 사용자 프로필 이미지 또는 기본 아이콘
                                (() => {
                                  const profileImageUrl = profile?.profile_image_url || user?.profileImage;
                                  const userName = profile?.nickname || user?.name || '사용자';
                                  
                                  if (user && profileImageUrl) {
                                    return (
                                      <div className="relative w-full h-full">
                                        <img 
                                          src={profileImageUrl} 
                                          alt={userName} 
                                          className="w-full h-full object-cover rounded-full"
                                          onError={(e) => {
                                            // 이미지 로드 실패 시 fallback div 표시
                                            const target = e.currentTarget;
                                            target.style.display = 'none';
                                            const fallback = target.nextElementSibling as HTMLElement;
                                            if (fallback) {
                                              fallback.style.display = 'flex';
                                            }
                                          }}
                                        />
                                        <div 
                                          className="absolute inset-0 flex items-center justify-center bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full"
                                          style={{ display: 'none' }}
                                        >
                                          <Person sx={{ fontSize: { xs: 20, lg: 24 } }} />
                                        </div>
                                      </div>
                                    );
                                  } else if (user) {
                                    // 로그인했지만 프로필 이미지가 없는 경우 - 이니셜 표시
                                    const initial = userName.charAt(0).toUpperCase();
                                    return (
                                      <div className="flex items-center justify-center w-full h-full text-white font-bold text-sm lg:text-base">
                                        {initial}
                                      </div>
                                    );
                                  } else {
                                    // 게스트 사용자
                                    return <Person sx={{ fontSize: { xs: 20, lg: 24 } }} />;
                                  }
                                })()
                              ) : (
                                <span className="text-lg lg:text-xl">🥑</span>
                              )}
                            </div>

                            {/* 메시지 내용 */}
                            <div className={`flex-1 max-w-3xl ${msg.role === 'user' ? 'text-right' : ''}`}>
                              {/* 사용자 프로필 정보 표시 */}
                              {msg.role === 'user' && (
                                <div className="mb-2 text-right">
                                  <span className="text-xs lg:text-sm text-gray-600 bg-gray-50 px-3 py-1 rounded-full">
                                    {user ? 
                                      (profile?.nickname || user.name || user.email || '사용자') : 
                                      '게스트 사용자'
                                    }
                                    {profile && user && (
                                      <span className="ml-2 text-green-600">
                                        키토 목표: {profile.goals_kcal || 1500}kcal
                                        {profile.goals_carbs_g && (
                                          <span className="ml-1">/ 탄수화물: {profile.goals_carbs_g}g</span>
                                        )}
                                      </span>
                                    )}
                                    {!user && (
                                      <span className="ml-2 text-amber-600">
                                        로그인하면 개인화된 추천을 받을 수 있어요
                                      </span>
                                    )}
                                  </span>
                                </div>
                              )}
                              <div className={`inline-block p-4 lg:p-5 rounded-2xl shadow-lg ${msg.role === 'user'
                                  ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white'
                                  : 'bg-white border-2 border-gray-100'
                                }`}>
                                <p className="text-sm lg:text-base whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                              </div>

                              {/* 타임스탬프 */}
                              {shouldShowTimestamp(index) && (
                                <div className={`mt-1 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                                  <span
                                    className="text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                                    title={formatDetailedTime(msg.timestamp)}
                                  >
                                    {formatMessageTime(msg.timestamp)}
                                  </span>
                                </div>
                              )}

                              {/* 식단 저장 버튼 */}
                              {msg.role === 'assistant' && msg.mealData && (
                                <div className="mt-4 lg:mt-5 p-4 lg:p-5 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl shadow-lg">
                                  <div className="flex items-center justify-between mb-4">
                                    <h4 className="text-base font-bold text-green-800 flex items-center gap-2">
                                      <CalendarToday sx={{ fontSize: 20 }} />
                                      추천받은 식단
                                    </h4>
                                    <div className="flex flex-wrap gap-2">
                                      <Button
                                        size="sm"
                                        onClick={() => handleSaveMealToCalendar(msg.id, msg.mealData!)}
                                        disabled={isSavingMeal === msg.id || isSavingMeal === 'auto-save'}
                                        className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
                                      >
                                        {isSavingMeal === msg.id ? (
                                          <>
                                            <CircularProgress size={16} sx={{ mr: 1 }} />
                                            저장 중...
                                          </>
                                        ) : (
                                          <>
                                            <Save sx={{ fontSize: 16, mr: 1 }} />
                                            오늘에 저장
                                          </>
                                        )}
                                      </Button>
                                      
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => {
                                          const tomorrow = format(new Date(Date.now() + 86400000), 'yyyy-MM-dd')
                                          handleSaveMealToCalendar(msg.id, msg.mealData!, tomorrow)
                                        }}
                                        disabled={isSavingMeal === msg.id || isSavingMeal === 'auto-save'}
                                        className="border-2 border-green-500 text-green-700 hover:bg-green-50 font-semibold rounded-xl transition-all duration-300"
                                      >
                                        <CalendarToday sx={{ fontSize: 16, mr: 1 }} />
                                        내일에 저장
                                      </Button>

                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => {
                                          const dayAfterTomorrow = format(new Date(Date.now() + 172800000), 'yyyy-MM-dd')
                                          handleSaveMealToCalendar(msg.id, msg.mealData!, dayAfterTomorrow)
                                        }}
                                        disabled={isSavingMeal === msg.id || isSavingMeal === 'auto-save'}
                                        className="border-2 border-green-500 text-green-700 hover:bg-green-50 font-semibold rounded-xl transition-all duration-300"
                                      >
                                        <CalendarToday sx={{ fontSize: 16, mr: 1 }} />
                                        모레에 저장
                                      </Button>
                                      
                                      {isSavingMeal === 'auto-save' && (
                                        <div className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm">
                                          <CircularProgress size={12} />
                                          <span>자동 저장 중...</span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 text-sm">
                                    {msg.mealData.breakfast && (
                                      <div className="bg-white/70 p-3 rounded-xl border border-green-100">
                                        <span className="font-bold text-green-700 text-base">🌅 아침</span>
                                        <p className="text-green-600 mt-1">{msg.mealData.breakfast}</p>
                                      </div>
                                    )}
                                    {msg.mealData.lunch && (
                                      <div className="bg-white/70 p-3 rounded-xl border border-green-100">
                                        <span className="font-bold text-green-700 text-base">☀️ 점심</span>
                                        <p className="text-green-600 mt-1">{msg.mealData.lunch}</p>
                                      </div>
                                    )}
                                    {msg.mealData.dinner && (
                                      <div className="bg-white/70 p-3 rounded-xl border border-green-100">
                                        <span className="font-bold text-green-700 text-base">🌙 저녁</span>
                                        <p className="text-green-600 mt-1">{msg.mealData.dinner}</p>
                                      </div>
                                    )}
                                    {msg.mealData.snack && (
                                      <div className="bg-white/70 p-3 rounded-xl border border-green-100">
                                        <span className="font-bold text-green-700 text-base">🍎 간식</span>
                                        <p className="text-green-600 mt-1">{msg.mealData.snack}</p>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )}

                              {/* 결과 카드들 */}
                              {/* {msg.results && msg.results.length > 0 && (
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 lg:gap-4 mt-3 lg:mt-4">
                                  {msg.results.map((result, index) => (
                                    <div key={index}>
                                      {result.title && result.ingredients ? (
                                        <RecipeCard recipe={result} />
                                      ) : null}
                                    </div>
                                  ))}
                                </div>
                              )} */}

                              {/* 결과에 좌표가 포함된 장소가 있으면 지도와 카드를 가로로 표시 */}
                              {(() => {
                                const hasLocationData = msg.results && msg.results.some((r: any) => typeof r.lat === 'number' && typeof r.lng === 'number')
                                console.log(`🗺️ 지도 표시 조건 체크 - 메시지 ID: ${msg.id}`, {
                                  hasResults: !!msg.results,
                                  resultsLength: msg.results?.length || 0,
                                  hasLocationData,
                                  sampleResult: msg.results?.[0] ? {
                                    name: msg.results[0].name,
                                    lat: msg.results[0].lat,
                                    lng: msg.results[0].lng,
                                    latType: typeof msg.results[0].lat,
                                    lngType: typeof msg.results[0].lng
                                  } : null
                                })
                                return hasLocationData
                              })() && (
                                <div className="mt-4 lg:mt-5">
                                  <div className="flex flex-col lg:flex-row gap-4 lg:gap-6">
                                    {/* 지도 영역 */}
                                    <div className="flex-1">
                                      <div className="rounded-2xl overflow-hidden border border-gray-200">
                                        <div className="h-[500px] lg:h-[500px]">
                                          {(() => {
                                            const placeResults = msg.results!.filter((r: any) => typeof r.lat === 'number' && typeof r.lng === 'number')
                                            const restaurants = placeResults.map((r: any, i: number) => ({
                                              id: r.place_id || String(i),
                                              name: r.name || '',
                                              address: r.address || '',
                                              lat: r.lat,
                                              lng: r.lng,
                                            }))
                                            return (
                                              <KakaoMap
                                                key={`map-${msg.id}`}
                                                lat={userLocation?.lat}
                                                lng={userLocation?.lng}
                                                level={1}
                                                fitToBounds={true}
                                                restaurants={restaurants}
                                                activeIndex={typeof selectedPlaceIndexByMsg[msg.id] === 'number' ? selectedPlaceIndexByMsg[msg.id]! : null}
                                                specialMarker={userLocation ? { lat: userLocation.lat, lng: userLocation.lng, title: '현재 위치' } : undefined}
                                                onMarkerClick={({ index }) => {
                                                  setSelectedPlaceIndexByMsg(prev => ({ ...prev, [msg.id]: index }))
                                                }}
                                              />
                                            )
                                          })()}
                                        </div>
                                      </div>
                                    </div>

                                    {/* 장소 카드 영역 */}
                                    <div className="w-full lg:w-80 flex-shrink-0">
                                      <div className="overflow-hidden">
                                        {(() => {
                                          const placeResults = msg.results!.filter((r: any) => typeof r.lat === 'number' && typeof r.lng === 'number')
                                          const sel = selectedPlaceIndexByMsg[msg.id]
                                          if (typeof sel === 'number' && sel >= 0 && sel < placeResults.length) {
                                            const place = placeResults[sel]
                                            return <PlaceCard place={place} />
                                          }
                                          return (
                                            <div className="h-[500px] flex items-center justify-center p-6 bg-gray-50 rounded-2xl border border-gray-200">
                                              <div className="text-center text-gray-500">
                                                <p className="text-sm font-medium">지도에서 장소를 클릭해보세요</p>
                                                <p className="text-xs text-gray-400 mt-1">상세 정보를 확인할 수 있습니다</p>
                                              </div>
                                            </div>
                                          )
                                        })()}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}

                      {/* 로딩 표시 */}
                      {isLoading && (
                        <div className="flex items-start gap-3 lg:gap-4">
                          <div className="flex-shrink-0 w-8 h-8 lg:w-10 lg:h-10 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 text-white flex items-center justify-center shadow-md">
                            <span className="text-sm lg:text-lg">🥑</span>
                          </div>
                          <div className="bg-card border border-border/50 p-3 lg:p-4 rounded-2xl shadow-sm">
                            <div className="flex items-center gap-2 lg:gap-3">
                              <CircularProgress size={16} sx={{ color: 'green.500' }} />
                              <span className="text-xs lg:text-sm text-muted-foreground">키토 코치가 생각하고 있어요...</span>
                            </div>
                          </div>
                        </div>
                      )}

                      <div ref={messagesEndRef} />
                    </div>
                  </div>
                </div>
              </div>

              {/* 입력 영역 - 고정 위치 */}
              <div className="flex-shrink-0 border-t-2 border-gray-100 bg-white/90 backdrop-blur-sm p-4 lg:p-6">
                <div className="max-w-4xl mx-auto">
                  <div className="flex gap-3 lg:gap-4">
                    <div className="flex-1 relative">
                      <Input
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="키토 식단에 대해 무엇이든 물어보세요..."
                        className="h-12 lg:h-14 pl-4 lg:pl-6 pr-12 lg:pr-14 bg-white border-2 border-gray-200 focus:border-green-400 rounded-2xl shadow-lg focus:shadow-xl transition-all duration-300"
                        disabled={isLoading}
                      />
                      {isLoading && (
                        <div className="absolute right-2 lg:right-3 top-1/2 -translate-y-1/2">
                          <CircularProgress size={16} sx={{ color: 'text.secondary' }} />
                        </div>
                      )}
                    </div>
                    <Button
                      onClick={handleSendMessage}
                      disabled={!message.trim() || isLoading}
                      className="h-12 lg:h-14 px-4 lg:px-6 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300"
                    >
                      <Send className="h-4 w-4 lg:h-5 lg:w-5" />
                    </Button>
                  </div>

                  {/* 빠른 질문 버튼들 */}
                  <div className="flex flex-wrap gap-1 lg:gap-2 mt-3 lg:mt-4 justify-center">
                    {[
                      "아침 키토 레시피 추천해줘",
                      "강남역 근처 키토 식당 찾아줘",
                      "7일 키토 식단표 만들어줘",
                      "키토 다이어트 방법 알려줘"
                    ].map((quickMessage) => (
                      <Button
                        key={quickMessage}
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickMessage(quickMessage)}
                        disabled={isLoading}
                        className="text-xs lg:text-sm px-3 lg:px-4 py-1 lg:py-2 rounded-lg lg:rounded-xl border-2 border-green-200 hover:bg-green-50 hover:border-green-300 hover:shadow-md transition-all duration-300 font-medium text-green-700"
                      >
                        {quickMessage}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

