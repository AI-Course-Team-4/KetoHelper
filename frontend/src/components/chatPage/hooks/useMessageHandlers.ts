import { useCallback, useEffect } from 'react'
import { ChatMessage, LLMParsedMeal } from '@/store/chatStore'
import { useProfileStore } from '@/store/profileStore'
import { useAuthStore } from '@/store/authStore'
import { useSendMessage, useCreatePlan, useParseDateFromMessage, ParsedDateInfo, useCreateNewThread } from '@/hooks/useApi'
import { useQueryClient } from '@tanstack/react-query'
import { MealParserService } from '@/lib/mealService'
import { format } from 'date-fns'

interface UseMessageHandlersProps {
  message: string
  setMessage: (message: string) => void
  isLoading: boolean
  setIsLoading: (loading: boolean) => void
  setLoadingStep: (step: 'thinking' | 'analyzing' | 'generating' | 'finalizing') => void
  currentThreadId: string | null
  setCurrentThreadId: (threadId: string | null) => void
  isSaving: boolean
  setIsSaving: (saving: boolean) => void
  setIsSavingMeal: (saving: string | null) => void
  messages: ChatMessage[]
  addMessage: (message: ChatMessage) => void
  refetchThreads: () => void
  refetchHistory: () => void
  isLoggedIn: boolean
}

export function useMessageHandlers({
  message,
  setMessage,
  isLoading,
  setIsLoading,
  setLoadingStep,
  currentThreadId,
  setCurrentThreadId,
  isSaving,
  setIsSaving,
  setIsSavingMeal,
  messages,
  addMessage,
  refetchThreads,
  refetchHistory,
  isLoggedIn
}: UseMessageHandlersProps) {
  // 스토어
  const { profile } = useProfileStore()
  const { user, ensureGuestId, isGuest } = useAuthStore()

  // 배포 환경 디버깅을 위한 세션 스토리지 모니터링 (백업 없이)
  useEffect(() => {
    console.log('🔍 useMessageHandlers useEffect 실행:', { 
      isGuest, 
      user: !!user, 
      isLoggedIn,
      timestamp: new Date().toISOString()
    })

    if (isGuest) {
      console.log('✅ 게스트 사용자로 판단됨 - 세션 스토리지 모니터링 시작')
      
      const checkSessionStorage = () => {
        const sessionData = sessionStorage.getItem('keto-coach-chat-guest')
        console.log('🔍 세션 스토리지 상태 체크 (백업 없음):', {
          currentURL: window.location.href,
          hasSessionData: !!sessionData,
          isGuest,
          sessionDataLength: sessionData ? JSON.parse(sessionData).state?.messages?.length : 0,
          timestamp: new Date().toISOString()
        })
      }

      // 페이지 로드 시 체크
      checkSessionStorage()

      // 페이지 포커스 시 체크 (다른 페이지에서 돌아올 때)
      window.addEventListener('focus', checkSessionStorage)

      return () => {
        window.removeEventListener('focus', checkSessionStorage)
      }
    } else {
      console.log('❌ 게스트 사용자가 아님 - 세션 스토리지 모니터링 건너뜀')
    }
  }, [isGuest, user, isLoggedIn])

  // 백업 로직 비활성화 - 순수 세션 스토리지만으로 테스트
  // useEffect(() => {
  //   if (isGuest && messages.length > 0) {
  //     const recentMessages = messages.slice(-20)
  //     const chatData = {
  //       state: { 
  //         messages: recentMessages, 
  //         currentSessionId: currentThreadId, 
  //         isLoading: false 
  //       },
  //       version: 0
  //     }
  //     localStorage.setItem('keto-coach-chat-guest-backup', JSON.stringify(chatData))
  //     console.log('💾 배포 환경 백업 저장:', { messageCount: recentMessages.length })
  //   }
  // }, [messages, currentThreadId, isGuest])

  // API 훅들
  const sendMessage = useSendMessage()
  const createNewThread = useCreateNewThread()
  const createPlan = useCreatePlan()
  const parseDateFromMessage = useParseDateFromMessage()
  const queryClient = useQueryClient()

  // 메시지 전송 핸들러
  const handleSendMessage = useCallback(async () => {
    if (!message.trim() || isLoading) {
      return
    }
    
    // 전역 이벤트 의존 제거: 이 핸들러 내부에서만 isLoading 관리

    const userId = user?.id
    const guestId = isGuest ? ensureGuestId() : undefined
    let threadId = currentThreadId

    const now = Date.now()
    const userMessage: ChatMessage = {
      id: now.toString(),
      role: 'user',
      content: message.trim(),
      timestamp: new Date(now)
    }

    // 새 채팅인 경우 스레드를 먼저 생성 (로그인 사용자만)
    if (!currentThreadId && isLoggedIn) {
      try {
        const created = await createNewThread.mutateAsync({ userId: userId, guestId: undefined })
        if (created?.id) {
          threadId = created.id
          setCurrentThreadId(created.id)
        }
      } catch (e) {
        console.error('스레드 생성 실패:', e)
      }
    }
    
    // 로컬 스토어 사용 중단 - React Query Optimistic Updates만 사용
    
    setMessage('')
    setIsLoading(true)
    setLoadingStep('thinking')
    console.log('🔄 로딩 단계: thinking')

    // 1) 낙관적 추가 (로그인/게스트 분기)
    if (isLoggedIn) {
      const cacheKey: any[] = ['chat-history', threadId || currentThreadId, 20]
      // 유저 메시지만 즉시 추가 (로딩 말풍선 미표시)
      queryClient.setQueryData(cacheKey, (old: any[] = []) => [
        ...old,
        {
          id: userMessage.id,
          role: 'user',
          message: userMessage.content,
          created_at: new Date(now).toISOString()
        }
      ])
    } else {
      // 게스트 사용자만 로컬 스토어에 사용자 메시지 추가
      addMessage(userMessage)
    }

    try {
      // 분석 단계
      setLoadingStep('analyzing')
      console.log('🔄 로딩 단계: analyzing')
      await new Promise(resolve => setTimeout(resolve, 500)) // 0.5초 대기
      
      // 생성 단계
      setLoadingStep('generating')
      console.log('🔄 로딩 단계: generating')
      
      const response = await sendMessage.mutateAsync({
        message: userMessage.content,
        profile: profile ? {
          allergies: profile.allergy_names,
          dislikes: profile.dislike_names,
          goals_kcal: profile.goals_kcal,
          goals_carbs_g: profile.goals_carbs_g
        } : undefined,
        location: undefined,
        radius_km: 5,
        // 이미 없으면 방금 생성된 threadId 사용
        thread_id: (threadId || currentThreadId || undefined),
        user_id: userId,
        guest_id: guestId
      })
      
      // 마무리 단계
      setLoadingStep('finalizing')
      console.log('🔄 로딩 단계: finalizing')
      await new Promise(resolve => setTimeout(resolve, 300)) // 0.3초 대기

      // 서버가 새 스레드를 발급했다면 최신 ID로 교체
      if (response.thread_id && response.thread_id !== threadId) {
        setCurrentThreadId(response.thread_id)
        threadId = response.thread_id
      }

      // 채팅 제한 감지 (로그인: 20개, 게스트: 10개)
      // 로그인 사용자는 React Query 캐시의 히스토리 길이를 사용
      const cachedHistory = isLoggedIn
        ? (queryClient.getQueryData<any[]>(['chat-history', threadId || currentThreadId, 20]) || [])
        : []
      const currentMessageCount = isLoggedIn ? cachedHistory.length : messages.length
      const messageLimit = isLoggedIn ? 20 : 10
      if (currentMessageCount >= messageLimit) { // 제한에 도달
        console.log('⚠️ 채팅 제한 도달:', { currentMessageCount, limit: messageLimit, isLoggedIn })
        setIsLoading(false)
        return
      }

      // 백엔드에서 반환하는 구조화된 meal_plan_data 사용
      let parsedMeal: LLMParsedMeal | null = null
      
      if (response.meal_plan_data && response.meal_plan_data.days && response.meal_plan_data.days.length > 0) {
        const firstDay = response.meal_plan_data.days[0]
        parsedMeal = {
          breakfast: firstDay.breakfast?.title || '',
          lunch: firstDay.lunch?.title || '',
          dinner: firstDay.dinner?.title || '',
          snack: firstDay.snack?.title || ''
        }
        console.log('✅ 백엔드 meal_plan_data 사용:', parsedMeal)
      } else {
        parsedMeal = MealParserService.parseMealFromBackendResponse(response)
        console.log('⚠️ 기존 파싱 방식 사용:', parsedMeal)
      }

      // 3) 응답 도착: assistant 메시지 추가 (게스트 사용자만)
      if (!isLoggedIn) {
        // 게스트 사용자만 로컬 스토어에 AI 응답 추가
        addMessage({
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.response,
          results: response.results,
          timestamp: new Date(),
          mealData: parsedMeal
        })
      }
      
      // 로그인 사용자는 React Query가 자동으로 처리

      // 백엔드에서 제공하는 save_to_calendar_data가 있으면 우선 사용
      if (response.save_to_calendar_data && user?.id) {
        console.log('✅ 백엔드 save_to_calendar_data 사용:', response.save_to_calendar_data)
        if (!isSaving) {
          setIsSaving(true)
          handleBackendCalendarSave(response.save_to_calendar_data!, parsedMeal)
            .finally(() => setIsSaving(false))
        }
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
          if (!isSaving) {
            setIsSaving(true)
            setTimeout(() => {
              handleSmartMealSave(userMessage.content, parsedMeal)
                .finally(() => setIsSaving(false))
            }, 1000)
          }
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
          const updatedMessages = messages
          const recentMealData = findRecentMealData(updatedMessages)

          if (recentMealData) {
            if (!isSaving) {
              setIsSaving(true)
              setTimeout(() => {
                handleSmartMealSave(userMessage.content, recentMealData, '이전 식단을')
                  .finally(() => setIsSaving(false))
              }, 1000)
            }
          } else {
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
      
      // React Query Optimistic Updates가 자동으로 처리
    } catch (error: any) {
      const status = error?.response?.status
      console.error('메시지 전송 실패:', { status, error })
      // 게스트/서버 오류: 말풍선 추가하지 않고 로깅만
      // (필요 시 토스트로 안내)
    } finally {
      setIsLoading(false)
    }
  }, [message, isLoading, currentThreadId, user, isGuest, ensureGuestId, addMessage, setMessage, setIsLoading, sendMessage, profile, isSaving, setIsSaving, messages, createPlan, parseDateFromMessage, queryClient, refetchThreads, isLoggedIn, refetchHistory])

  // 키보드 이벤트 핸들러
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }, [handleSendMessage])

  // 빠른 질문 메시지 핸들러
  const handleQuickMessage = useCallback(async (quickMessage: string) => {
    if (!quickMessage.trim() || isLoading) return

    const userId = user?.id
    const guestId = isGuest ? ensureGuestId() : undefined
    let threadId = currentThreadId

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: quickMessage.trim(),
      timestamp: new Date()
    }

    // 모든 사용자: React Query Optimistic Updates 사용
    
    // 새 채팅인 경우 처리 (로그인/게스트 분기)
    if (!currentThreadId) {
      if (isLoggedIn) {
        // 로그인 사용자: 임시 스레드 ID 설정
        const tempThreadId = `temp-thread-${Date.now()}`
        setCurrentThreadId(tempThreadId)
      }
      // 게스트 사용자: currentThreadId는 null로 유지
    }
    
    // 게스트 사용자만 로컬 스토어에 사용자 메시지 추가
    if (!isLoggedIn) {
      addMessage(userMessage)
    }
    
    setIsLoading(true)
    setLoadingStep('thinking')
    console.log('🔄 QuickMessage 로딩 단계: thinking')

    try {
      // 분석 단계
      setLoadingStep('analyzing')
      console.log('🔄 QuickMessage 로딩 단계: analyzing')
      await new Promise(resolve => setTimeout(resolve, 500)) // 0.5초 대기
      
      // 생성 단계
      setLoadingStep('generating')
      console.log('🔄 QuickMessage 로딩 단계: generating')
      
      const response = await sendMessage.mutateAsync({
        message: userMessage.content,
        profile: profile ? {
          allergies: profile.allergy_names,
          dislikes: profile.dislike_names,
          goals_kcal: profile.goals_kcal,
          goals_carbs_g: profile.goals_carbs_g
        } : undefined,
        location: undefined,
        radius_km: 5,
        thread_id: currentThreadId && currentThreadId.startsWith('temp-thread-') ? undefined : (currentThreadId || undefined),
        user_id: userId,
        guest_id: guestId
      })
      
      // 마무리 단계
      setLoadingStep('finalizing')
      console.log('🔄 QuickMessage 로딩 단계: finalizing')
      await new Promise(resolve => setTimeout(resolve, 300)) // 0.3초 대기

      if (response.thread_id && response.thread_id !== threadId) {
        setCurrentThreadId(response.thread_id)
        threadId = response.thread_id
      }

      let parsedMeal: LLMParsedMeal | null = null
      
      if (response.meal_plan_data && response.meal_plan_data.days && response.meal_plan_data.days.length > 0) {
        const firstDay = response.meal_plan_data.days[0]
        parsedMeal = {
          breakfast: firstDay.breakfast?.title || '',
          lunch: firstDay.lunch?.title || '',
          dinner: firstDay.dinner?.title || '',
          snack: firstDay.snack?.title || ''
        }
        console.log('✅ 백엔드 meal_plan_data 사용:', parsedMeal)
      } else {
        parsedMeal = MealParserService.parseMealFromBackendResponse(response)
        console.log('⚠️ 기존 파싱 방식 사용:', parsedMeal)
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        results: response.results,
        timestamp: new Date(),
        mealData: parsedMeal
      }

      // 게스트 사용자만 로컬 스토어에 AI 응답 추가
      if (!isLoggedIn) {
        addMessage(assistantMessage)
      }
      
      // 로그인 사용자는 React Query가 자동으로 처리

      // 백엔드에서 제공하는 save_to_calendar_data가 있으면 우선 사용
      if (response.save_to_calendar_data && user?.id) {
        console.log('✅ 백엔드 save_to_calendar_data 사용:', response.save_to_calendar_data)
        if (!isSaving) {
          setIsSaving(true)
          handleBackendCalendarSave(response.save_to_calendar_data!, parsedMeal)
            .finally(() => setIsSaving(false))
        }
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
          if (!isSaving) {
            setIsSaving(true)
            setTimeout(() => {
              handleSmartMealSave(userMessage.content, parsedMeal)
                .finally(() => setIsSaving(false))
            }, 1000)
          }
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
          const updatedMessages = [...messages, assistantMessage]
          const recentMealData = findRecentMealData(updatedMessages)

          if (recentMealData) {
            if (!isSaving) {
              setIsSaving(true)
              setTimeout(() => {
                handleSmartMealSave(userMessage.content, recentMealData, '이전 식단을')
                  .finally(() => setIsSaving(false))
              }, 1000)
            }
          } else {
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
      
      // React Query Optimistic Updates가 자동으로 처리
    } catch (error: any) {
      const status = error?.response?.status
      console.error('메시지 전송 실패:', { status, error })
      // 게스트/서버 오류: 말풍선 추가하지 않고 로깅만
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, user, isGuest, ensureGuestId, addMessage, setIsLoading, sendMessage, profile, isSaving, setIsSaving, messages, createPlan, parseDateFromMessage, queryClient, refetchThreads, isLoggedIn, refetchHistory, currentThreadId, setCurrentThreadId])

  // 식단 저장 핸들러
  const handleSaveMealToCalendar = useCallback(async (messageId: string, mealData: LLMParsedMeal, targetDate?: string) => {
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
        queryClient.invalidateQueries({ queryKey: ['plans-range'] })
        
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
  }, [user, addMessage, setIsSavingMeal, createPlan, queryClient])

  // 장소 마커 클릭 핸들러
  const handlePlaceMarkerClick = useCallback((_messageId: string, _index: number) => {
    // 이 함수는 useChatLogic에서 selectedPlaceIndexByMsg 상태를 관리하므로
    // 실제 구현은 메인 컴포넌트에서 처리
  }, [])

  // 최근 식단 데이터 찾기
  const findRecentMealData = useCallback((messages: ChatMessage[]): LLMParsedMeal | null => {
    console.log('🔍 findRecentMealData 호출, 메시지 수:', messages.length)
    
    // 1. mealData 속성에서 직접 찾기
    for (let i = messages.length - 1; i >= Math.max(0, messages.length - 15); i--) {
      const msg = messages[i]
      console.log(`🔍 메시지 ${i} 확인:`, { 
        role: msg.role, 
        hasMealData: !!msg.mealData,
        contentPreview: msg.content?.substring(0, 50) + '...'
      })
      
      if (msg.role === 'assistant' && msg.mealData) {
        console.log('✅ mealData 속성에서 식단 데이터 발견:', msg.mealData)
        return msg.mealData
      }
    }
    
    // 2. 메시지 내용을 파싱해서 찾기
    for (let i = messages.length - 1; i >= Math.max(0, messages.length - 15); i--) {
      const msg = messages[i]
      if (msg.role === 'assistant' && msg.content) {
        console.log(`🔍 메시지 ${i} 내용 파싱 시도:`, msg.content.substring(0, 100) + '...')
        const parsedMeal = MealParserService.parseMealFromResponse(msg.content)
        if (parsedMeal) {
          console.log('✅ 메시지 내용에서 식단 데이터 파싱 성공:', parsedMeal)
          return parsedMeal
        } else {
          console.log('❌ 메시지 내용에서 식단 데이터 파싱 실패')
        }
      }
    }
    
    console.log('❌ 최근 15개 메시지에서 식단 데이터를 찾을 수 없음')
    return null
  }, [])

  // 스마트 식단 저장
  const handleSmartMealSave = useCallback(async (userMessage: string, mealData: LLMParsedMeal, prefix: string = '') => {
    if (!user?.id) return

    if (isSaving) {
      console.log('🔒 이미 저장 중입니다. 중복 저장을 방지합니다.')
      return
    }

    let parsedDate: ParsedDateInfo | null = null

    try {
      const parseResult = await parseDateFromMessage.mutateAsync({ message: userMessage })
      if (parseResult.success && parseResult.parsed_date) {
        parsedDate = parseResult.parsed_date
      }
    } catch (error) {
      console.error('날짜 파싱 API 오류:', error)
      parsedDate = null
    }

    if (parsedDate) {
      setIsSaving(true)
      setIsSavingMeal('auto-save')

      try {
        const recentMessages = messages.slice(-5)
        const has7DayMealPlan = recentMessages.some(msg =>
          msg.content.includes('7일') && msg.content.includes('식단') ||
          msg.content.includes('일주일') && msg.content.includes('식단')
        )

        if (has7DayMealPlan && (userMessage.includes('다음주') || userMessage.includes('담주'))) {
          const savedDays: string[] = []
          let successCount = 0

          for (let dayOffset = 0; dayOffset < 7; dayOffset++) {
            const baseDate = new Date(parsedDate.date)
            baseDate.setDate(baseDate.getDate() + dayOffset)
            const dateString = format(baseDate, 'yyyy-MM-dd')

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
        setIsSaving(false)
      }
    }
  }, [user, isSaving, setIsSaving, setIsSavingMeal, parseDateFromMessage, messages, createPlan, queryClient, addMessage])

  // 백엔드 캘린더 저장
  const handleBackendCalendarSave = useCallback(async (saveData: any, mealData: LLMParsedMeal | null) => {
    if (!user?.id) return

    if (isSaving) {
      console.log('🔒 이미 저장 중입니다. 중복 저장을 방지합니다.')
      return
    }

    setIsSaving(true)
    setIsSavingMeal('auto-save')
    
    try {
      const startDate = new Date(saveData.start_date)
      const durationDays = saveData.duration_days
      const daysData = saveData.days_data || []
      
      console.log(`🗓️ 백엔드 캘린더 저장: ${durationDays}일치, 시작일: ${startDate.toISOString()}`)
      console.log(`🗓️ 백엔드에서 받은 days_data:`, daysData)
      
      let successCount = 0
      const savedDays: string[] = []
      
      for (let i = 0; i < durationDays; i++) {
        const currentDate = new Date(startDate)
        currentDate.setDate(startDate.getDate() + i)
        const dateString = currentDate.toISOString().split('T')[0]
        
        let dayMeals: any = {}
        if (daysData[i]) {
          dayMeals = daysData[i]
          console.log(`🗓️ ${i+1}일차 백엔드 식단 사용:`, dayMeals)
        } else {
          dayMeals = mealData || {
            breakfast: '키토 아침 메뉴',
            lunch: '키토 점심 메뉴', 
            dinner: '키토 저녁 메뉴',
            snack: '키토 간식'
          }
        }
        
        const mealSlots = ['breakfast', 'lunch', 'dinner', 'snack'] as const
        let daySuccessCount = 0

        for (const slot of mealSlots) {
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
      setIsSaving(false)
    }
  }, [user, isSaving, setIsSaving, setIsSavingMeal, createPlan, queryClient, addMessage])

  return {
    handleSendMessage,
    handleKeyDown,
    handleQuickMessage,
    handleSaveMealToCalendar,
    handlePlaceMarkerClick
  }
}
