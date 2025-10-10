import { useCallback, useEffect } from 'react'
import { ChatMessage, LLMParsedMeal } from '@/store/chatStore'
import { useProfileStore } from '@/store/profileStore'
import { useAuthStore } from '@/store/authStore'
import { useCalendarStore, OptimisticMealData } from '@/store/calendarStore'
import { useSendMessage, useCreatePlan, useParseDateFromMessage, ParsedDateInfo, useCreateNewThread, api } from '@/hooks/useApi'
import { useQueryClient } from '@tanstack/react-query'
import { MealParserService } from '@/lib/mealService'
import { format } from 'date-fns'

interface UseMessageHandlersProps {
  message: string
  setMessage: (message: string) => void
  isLoading: boolean
  setIsLoading: (loading: boolean) => void
  setLoadingStep?: (step: 'thinking' | 'analyzing' | 'generating' | 'finalizing') => void
  currentThreadId: string | null
  setCurrentThreadId: (threadId: string | null) => void
  isSaving: boolean
  setIsSaving: (saving: boolean) => void
  setIsSavingMeal: (saving: string | null) => void
  chatHistory?: any[]
  messages: any[]
  isLoggedIn: boolean
  refetchThreads: () => void
  inputRef: React.RefObject<HTMLInputElement>
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
  isLoggedIn,
  refetchThreads,
  inputRef
}: UseMessageHandlersProps) {
  // 안전 호출용 래퍼: setLoadingStep이 제공되지 않은 경우 무시
  const safeSetLoadingStep = useCallback((step: 'thinking' | 'analyzing' | 'generating' | 'finalizing') => {
    if (typeof setLoadingStep === 'function') {
      setLoadingStep(step)
    }
  }, [setLoadingStep])
  // 스토어
  const { profile } = useProfileStore()
  const { user, ensureGuestId, isGuest } = useAuthStore()

  // 채팅창 포커스 함수
  const focusInput = useCallback(() => {
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [inputRef])

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
  
  // 헬퍼: 메시지를 캐시에 추가 (로그인: React Query, 게스트: SessionStorage)
  const addMessageToCache = useCallback((content: string, role: 'user' | 'assistant' = 'assistant') => {
    if (isLoggedIn) {
      // 로그인 사용자: React Query 캐시 사용
      const cacheKey = currentThreadId || ''
      queryClient.setQueryData(['chat-history', cacheKey, 20], (old: any[] = []) => [
        ...old,
        {
          id: Date.now().toString(),
          role,
          message: content,
          created_at: new Date().toISOString()
        }
      ])
    } else {
      // 게스트 사용자: SessionStorage 사용
      const guestId = ensureGuestId()
      if (guestId) {
        try {
          const stored = sessionStorage.getItem(`guest-chat-${guestId}`)
          const existingHistory = stored ? JSON.parse(stored) : []
          
          const newMessage = {
            id: Date.now().toString(),
            role,
            message: content,
            created_at: new Date().toISOString()
          }
          
          const updatedHistory = [...existingHistory, newMessage]
          sessionStorage.setItem(`guest-chat-${guestId}`, JSON.stringify(updatedHistory))
          console.log('🎭 게스트 메시지 SessionStorage 저장:', { role, content: content.substring(0, 30) + '...' })
          
        } catch (error) {
          console.error('🎭 SessionStorage 저장 오류:', error)
        }
      }
    }
  }, [currentThreadId, queryClient, isLoggedIn, ensureGuestId])

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
    
    setMessage('')
    setIsLoading(true)
    safeSetLoadingStep('thinking')
    console.log('🔄 로딩 단계: thinking')

    // 게스트 사용자의 경우 사용자 메시지를 즉시 SessionStorage에 저장
    if (!isLoggedIn) {
      addMessageToCache(userMessage.content, 'user')
      console.log('🎭 게스트 사용자 메시지 SessionStorage 저장:', userMessage.content)
    }

    // React Query Optimistic Update는 useApi.ts의 onMutate에서 자동으로 처리됨

    try {
      // 분석 단계
      safeSetLoadingStep('analyzing')
      console.log('🔄 로딩 단계: analyzing')
      await new Promise(resolve => setTimeout(resolve, 500)) // 0.5초 대기
      
      // 생성 단계
      safeSetLoadingStep('generating')
      console.log('🔄 로딩 단계: generating')
      
      // 🚀 식단표 생성 요청인 경우 즉시 Optimistic 데이터 추가
      console.log(`🔍 사용자 메시지 분석: "${userMessage.content}"`)
      
      const detectDays = (content: string): number | null => {
        console.log(`🔍 detectDays 함수 호출: "${content}"`)
        
        // 한글 키워드(숫자 미포함) 우선 매핑
        const weekKeywords = ['일주일', '일주', '한 주', '한주', '일주간', '1주일']
        if (weekKeywords.some(k => content.includes(k))) {
          console.log('✅ 일주일 키워드 감지 → 7일')
          return 7
        }

        // 더 간단한 패턴으로 수정
        const patterns = [
          /(\d+)일치/,
          /(\d+)일\s*식단/,
          /(\d+)일\s*키토/,
          /(\d+)일\s*계획/,
          /(\d+)일/,
          /(\d+)주치/,
          /(\d+)주\s*식단/,
          /(\d+)주\s*키토/
        ]
        
        for (const pattern of patterns) {
          const match = content.match(pattern)
          console.log(`🔍 패턴 "${pattern}" 매치 결과:`, match)
          if (match) {
            const days = parseInt(match[1])
            console.log(`🔍 추출된 숫자: ${days}`)
            if (days > 0 && days <= 365) {
              console.log(`✅ 일수 감지 성공: ${days}일`)
              return days
            }
          }
        }
        
        console.log(`❌ 일수 감지 실패`)
        return null
      }
      
      const parsedDays = detectDays(userMessage.content)
      console.log(`🚀 parsedDays 최종 결과: ${parsedDays}`)
      console.log(`🚀 유저 존재 여부: ${!!user}`)
      console.log(`🚀 유저 id: ${user?.id}`)
      
      if (parsedDays && parsedDays > 0 && user?.id) {
        console.log(`🚀 식단표 생성 요청 감지: ${parsedDays}일치 - 전역 캘린더 로딩 시작`)
        const { setCalendarLoading } = useCalendarStore.getState()
        // 전역 캘린더 로딩만 ON (자리표시자 추가는 제거)
        setCalendarLoading(true)
        setIsSaving(false)
      }
      
      // 게스트 사용자의 경우 SessionStorage 채팅 히스토리를 백엔드로 전달
      let guestChatHistory = []
      if (!isLoggedIn && guestId) {
        try {
          const stored = sessionStorage.getItem(`guest-chat-${guestId}`)
          if (stored) {
            guestChatHistory = JSON.parse(stored)
            console.log('🎭 게스트 채팅 히스토리를 백엔드로 전달:', guestChatHistory.length, '개')
          }
        } catch (error) {
          console.error('🎭 게스트 채팅 히스토리 파싱 오류:', error)
        }
      }

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
        // 게스트는 thread_id 없이, 로그인은 thread_id 사용
        thread_id: isLoggedIn ? (threadId || currentThreadId || undefined) : undefined,
        user_id: userId,
        guest_id: guestId,
        // 게스트 사용자의 경우 SessionStorage 채팅 히스토리 전달
        chat_history: !isLoggedIn ? guestChatHistory : undefined
      })
      
      // 마무리 단계
      safeSetLoadingStep('finalizing')
      console.log('🔄 로딩 단계: finalizing')
      await new Promise(resolve => setTimeout(resolve, 300)) // 0.3초 대기

      // 서버가 새 스레드를 발급했다면 최신 ID로 교체
      if (response.thread_id && response.thread_id !== threadId) {
        setCurrentThreadId(response.thread_id)
        threadId = response.thread_id
      }

      // 채팅 제한 감지: 게스트/로그인 통합 (messages 길이 기준)
      const currentMessageCount = messages?.length || 0
      const messageLimit = 20
      if (currentMessageCount >= messageLimit) {
        console.log('⚠️ 채팅 제한 도달:', { currentMessageCount, limit: messageLimit })
        
        // 채팅 제한 메시지를 AI 응답으로 표시
        const limitMessage = "죄송합니다. 게스트 사용자는 하루에 20개의 메시지까지만 보낼 수 있습니다. 더 많은 채팅을 이용하려면 로그인해주세요!"
        
        // 게스트 사용자의 경우 SessionStorage에 저장
        if (!isLoggedIn) {
          addMessageToCache(limitMessage, 'assistant')
        }
        
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

      // 게스트 사용자의 경우 AI 응답을 SessionStorage에 저장
      if (!isLoggedIn) {
        addMessageToCache(response.response || '', 'assistant')
        console.log('🎭 게스트 AI 응답 SessionStorage 저장:', (response.response || '').substring(0, 30) + '...')
      }
      
      // AI 응답은 useApi.ts의 onSuccess에서 자동으로 처리됨
      // (React Query Optimistic Updates)

      // 백엔드에서 제공하는 save_to_calendar_data가 있으면 우선 사용
      console.log('🔍 DEBUG: response.save_to_calendar_data 체크:', {
        hasSaveData: !!response.save_to_calendar_data,
        hasUserId: !!user?.id,
        isSaving,
        saveData: response.save_to_calendar_data,
        responseKeys: Object.keys(response)
      })
      console.log('🔍 DEBUG: 전체 응답 객체:', response)
      console.log('🔍 DEBUG: user?.id:', user?.id)
      console.log('🔍 DEBUG: isSaving:', isSaving)
      console.log('🔍 DEBUG: response.save_to_calendar_data:', response.save_to_calendar_data)
      console.log('🔍 DEBUG: parsedMeal:', parsedMeal)
      
      // 전역 캘린더 로딩 상태 확인
      const { isCalendarLoading } = useCalendarStore.getState()
      console.log('🔍 DEBUG: 현재 전역 캘린더 로딩 상태:', isCalendarLoading)
      if (response.save_to_calendar_data && user?.id) {
        console.log('✅ 백엔드 save_to_calendar_data 사용:', response.save_to_calendar_data)
        
        // 1) 채팅에 "접수" 메시지 먼저 출력
        addMessageToCache('📥 저장 요청을 접수했어요. 처리 중입니다 ⏳')
        
        // 2) 전역 JobStore에 간단 기준 저장(userId, startDate, durationDays)
        try {
          const { useCalendarJobStore } = await import('@/store/calendarJobStore')
          useCalendarJobStore.getState().setCriteria({
            userId: user!.id,
            startDate: response.save_to_calendar_data.start_date,
            durationDays: response.save_to_calendar_data.duration_days,
            monthKey: format(new Date(response.save_to_calendar_data.start_date), 'yyyy-MM')
          })

          // 🔮 캘린더 페이지 진입 전, 해당 월 범위를 미리 프리패치하여 첫 렌더 공백 제거
          const month = new Date(response.save_to_calendar_data.start_date)
          const startOfMonth = new Date(month.getFullYear(), month.getMonth(), 1)
          const endOfMonth = new Date(month.getFullYear(), month.getMonth() + 1, 0)

          await queryClient.prefetchQuery({
            queryKey: [
              'plans-range',
              format(startOfMonth, 'yyyy-MM-dd'),
              format(endOfMonth, 'yyyy-MM-dd'),
              user!.id
            ],
            queryFn: async () => {
              const res = await api.get('/plans/range', {
                params: {
                  start: format(startOfMonth, 'yyyy-MM-dd'),
                  end: format(endOfMonth, 'yyyy-MM-dd'),
                  user_id: user!.id
                }
              })
              return res.data
            }
          })
        } catch (_) {}
        
        if (!isSaving) {
          console.log('🚀 handleBackendCalendarSave 호출 시작')
          // 🚀 기존 임시 Optimistic 데이터를 실제 데이터로 교체
          handleBackendCalendarSave(response.save_to_calendar_data!)
        } else {
          console.log('🔒 이미 저장 중이므로 건너뜀')
        }
      } else {
        console.log('⚠️ save_to_calendar_data 또는 user.id가 없음')
        
        // 전역 캘린더 로딩 상태 해제 (백엔드 응답이 없어도)
        const { setCalendarLoading } = useCalendarStore.getState()
        setCalendarLoading(false)
        console.log('⚠️ save_to_calendar_data 없음 - 전역 캘린더 로딩 상태 해제')
        
        // 🚀 Optimistic Update가 이미 추가되었으므로, 기존 임시 데이터를 실제 데이터로 교체
        if (parsedMeal && user?.id) {
          console.log('🚀 Optimistic 데이터를 실제 데이터로 교체 시도')
          
          const { optimisticMeals, removeOptimisticMeals, addOptimisticMeals } = useCalendarStore.getState()
          if (optimisticMeals.length > 0) {
            console.log(`🧹 기존 임시 Optimistic 데이터 제거: ${optimisticMeals.length}개`)
            
            // 기존 임시 데이터 제거
            const existingMealIds = optimisticMeals.map(meal => meal.id)
            removeOptimisticMeals(existingMealIds)
            
            // 실제 데이터로 교체 (오늘 날짜 기준)
            const today = new Date()
            const dateStr = format(today, 'yyyy-MM-dd')
            const newOptimisticMeals: Omit<OptimisticMealData, 'id' | 'timestamp'>[] = []
            
            for (const slot of ['breakfast', 'lunch', 'dinner', 'snack'] as const) {
              if (parsedMeal[slot] && parsedMeal[slot].trim()) {
                newOptimisticMeals.push({
                  date: dateStr,
                  slot,
                  title: parsedMeal[slot],
                  type: 'optimistic'
                })
              }
            }
            
            if (newOptimisticMeals.length > 0) {
              addOptimisticMeals(newOptimisticMeals)
              console.log(`🚀 실제 데이터로 Optimistic 데이터 교체: ${newOptimisticMeals.length}개`)
            }
          }
        }
      }
      
      // 백엔드 데이터가 없으면 기존 로직 사용
      if (!response.save_to_calendar_data && parsedMeal && user?.id) {
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
              handleSmartMealSave(userMessage.content)
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
          // 최신 chatHistory를 queryClient에서 직접 가져오기 (dependency 문제 방지)
          const cacheKey = isLoggedIn 
            ? (threadId || currentThreadId || '')
            : `guest-${ensureGuestId()}`
          const latestChatHistory = queryClient.getQueryData<any[]>(['chat-history', cacheKey, 20]) || []
          const messagesToSearch = latestChatHistory.map((h: any) => ({
            id: h.id?.toString() || '',
            role: h.role,
            content: h.message,
            timestamp: new Date(h.created_at)
          } as ChatMessage))
          
          const recentMealData = findRecentMealData(messagesToSearch)

          if (recentMealData) {
            if (!isSaving) {
              setIsSaving(true)
              setTimeout(() => {
                handleSmartMealSave(userMessage.content)
                  .finally(() => setIsSaving(false))
              }, 1000)
            }
          }
        }
      }

      // 로그인 사용자의 경우 스레드 목록 업데이트
      if (isLoggedIn && response.thread_id) {
        console.log('🔄 스레드 목록 업데이트 중...')
        refetchThreads()
      }

      // general 응답이어도 저장 요청이 있으면 처리 (예전 로직 복원)
      if (user?.id && !isSaving) {
        const isSaveRequest = (
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

        if (isSaveRequest) {
          console.log('🔄 저장 요청 감지 - 이전 메시지에서 식단 데이터 찾기')
          // 최신 chatHistory를 queryClient에서 직접 가져오기
          const cacheKey = isLoggedIn 
            ? (threadId || currentThreadId || '')
            : `guest-${ensureGuestId()}`
          const latestChatHistory = queryClient.getQueryData<any[]>(['chat-history', cacheKey, 20]) || []
          const messagesToSearch = latestChatHistory.map((h: any) => ({
            id: h.id?.toString() || '',
            role: h.role,
            content: h.message,
            timestamp: new Date(h.created_at)
          } as ChatMessage))
          
          const recentMealData = findRecentMealData(messagesToSearch)

          if (recentMealData) {
            console.log('✅ 이전 메시지에서 식단 데이터 발견 - 저장 시작')
            setIsSaving(true)
            setTimeout(() => {
              handleSmartMealSave(userMessage.content)
                .finally(() => setIsSaving(false))
            }, 1000)
          } else {
            console.log('❌ 저장할 식단 데이터를 찾을 수 없음')
          }
        }
      }

      // React Query Optimistic Updates가 자동으로 처리
    } catch (error: any) {
      const status = error?.response?.status
      console.error('메시지 전송 실패:', { status, error })
      // 게스트/서버 오류: 말풍선 추가하지 않고 로깅만
      // (필요 시 토스트로 안내)
    } finally {
      setIsLoading(false)
      
      // 전역 캘린더 로딩 상태 확실히 해제 (안전장치)
      const { setCalendarLoading } = useCalendarStore.getState()
      setCalendarLoading(false)
      console.log('🛡️ finally 블록에서 전역 캘린더 로딩 상태 해제 (안전장치)')
      
      // 로딩 완료 후 채팅창에 포커스
      setTimeout(() => {
        focusInput()
      }, 100)
    }
  }, [message, isLoading, currentThreadId, user, isGuest, ensureGuestId, setMessage, setIsLoading, sendMessage, profile, isSaving, setIsSaving, createPlan, parseDateFromMessage, queryClient, isLoggedIn, addMessageToCache, refetchThreads, focusInput])

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

    setIsLoading(true)
    safeSetLoadingStep('thinking')
    console.log('🔄 QuickMessage 로딩 단계: thinking')

    // 게스트 사용자의 경우 사용자 메시지를 즉시 SessionStorage에 저장
    if (!isLoggedIn) {
      addMessageToCache(userMessage.content, 'user')
      console.log('🎭 게스트 퀵 메시지 SessionStorage 저장:', userMessage.content)
    }

    // React Query Optimistic Update는 useApi.ts의 onMutate에서 자동으로 처리됨

    try {
      // 분석 단계
      safeSetLoadingStep('analyzing')
      console.log('🔄 QuickMessage 로딩 단계: analyzing')
      await new Promise(resolve => setTimeout(resolve, 500)) // 0.5초 대기
      
      // 생성 단계
      safeSetLoadingStep('generating')
      console.log('🔄 QuickMessage 로딩 단계: generating')
      
      // 게스트 사용자의 경우 SessionStorage 채팅 히스토리를 백엔드로 전달
      let guestChatHistory = []
      if (!isLoggedIn && guestId) {
        try {
          const stored = sessionStorage.getItem(`guest-chat-${guestId}`)
          if (stored) {
            guestChatHistory = JSON.parse(stored)
            console.log('🎭 퀵메시지 게스트 채팅 히스토리를 백엔드로 전달:', guestChatHistory.length, '개')
          }
        } catch (error) {
          console.error('🎭 퀵메시지 게스트 채팅 히스토리 파싱 오류:', error)
        }
      }

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
        // 게스트는 thread_id 없이, 로그인은 thread_id 사용
        thread_id: isLoggedIn ? (currentThreadId && currentThreadId.startsWith('temp-thread-') ? undefined : (currentThreadId || undefined)) : undefined,
        user_id: userId,
        guest_id: guestId,
        // 게스트 사용자의 경우 SessionStorage 채팅 히스토리 전달
        chat_history: !isLoggedIn ? guestChatHistory : undefined
      })
      
      // 마무리 단계
      safeSetLoadingStep('finalizing')
      console.log('🔄 QuickMessage 로딩 단계: finalizing')
      await new Promise(resolve => setTimeout(resolve, 300)) // 0.3초 대기

      if (response.thread_id && response.thread_id !== threadId) {
        setCurrentThreadId(response.thread_id)
        threadId = response.thread_id
      }

      // 로그인 사용자의 경우 스레드 목록 업데이트
      if (isLoggedIn && response.thread_id) {
        console.log('🔄 퀵메시지 스레드 목록 업데이트 중...')
        refetchThreads()
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

      // 게스트 사용자의 경우 AI 응답을 SessionStorage에 저장
      if (!isLoggedIn) {
        addMessageToCache(response.response || '', 'assistant')
        console.log('🎭 게스트 퀵 메시지 AI 응답 SessionStorage 저장:', (response.response || '').substring(0, 30) + '...')
      }
      
      // AI 응답은 useApi.ts의 onSuccess에서 자동으로 처리됨
      // (React Query Optimistic Updates - 로그인/게스트 구분 없음)

      // 백엔드에서 제공하는 save_to_calendar_data가 있으면 우선 사용
      if (response.save_to_calendar_data && user?.id) {
        console.log('✅ 백엔드 save_to_calendar_data 사용:', response.save_to_calendar_data)
        if (!isSaving) {
          setIsSaving(true)
          handleBackendCalendarSave(response.save_to_calendar_data!)
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
              handleSmartMealSave(userMessage.content)
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
          // 최신 chatHistory를 queryClient에서 직접 가져오기 (dependency 문제 방지)
          const cacheKey = isLoggedIn 
            ? (threadId || currentThreadId || '')
            : `guest-${ensureGuestId()}`
          const latestChatHistory = queryClient.getQueryData<any[]>(['chat-history', cacheKey, 20]) || []
          const messagesToSearch = latestChatHistory.map((h: any) => ({
            id: h.id?.toString() || '',
            role: h.role,
            content: h.message,
            timestamp: new Date(h.created_at)
          } as ChatMessage))
          
          const recentMealData = findRecentMealData(messagesToSearch)

          if (recentMealData) {
            if (!isSaving) {
              setIsSaving(true)
              setTimeout(() => {
                handleSmartMealSave(userMessage.content)
                  .finally(() => setIsSaving(false))
              }, 1000)
            }
          }
        }
      }

      // React Query Optimistic Updates가 자동으로 처리
    } catch (error: any) {
      const status = error?.response?.status
      console.error('메시지 전송 실패:', { status, error })
      // 게스트/서버 오류: 말풍선 추가하지 않고 로깅만
    } finally {
      setIsLoading(false)
      // 로딩 완료 후 채팅창에 포커스
      setTimeout(() => {
        focusInput()
      }, 100)
    }
  }, [isLoading, user, isGuest, ensureGuestId, setIsLoading, sendMessage, profile, isSaving, setIsSaving, createPlan, parseDateFromMessage, queryClient, isLoggedIn, currentThreadId, setCurrentThreadId, addMessageToCache, refetchThreads, focusInput])

  // 식단 저장 핸들러
  const handleSaveMealToCalendar = useCallback(async (messageId: string, mealData: LLMParsedMeal, targetDate?: string) => {
    if (!user?.id) {
      addMessageToCache('❌ 식단 저장을 위해 로그인이 필요합니다.')
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
        
        addMessageToCache(`✅ 식단이 ${format(new Date(dateToSave), 'M월 d일')} 캘린더에 저장되었습니다! (${savedPlans.join(', ')}) 캘린더 페이지에서 확인해보세요.`)
      } else {
        throw new Error('저장할 식단이 없습니다')
      }
    } catch (error) {
      console.error('식단 저장 실패:', error)
      addMessageToCache('❌ 식단 저장에 실패했습니다. 다시 시도해주세요.')
    } finally {
      setIsSavingMeal(null)
    }
  }, [user, addMessageToCache, setIsSavingMeal, createPlan, queryClient])

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
  const handleSmartMealSave = useCallback(async (userMessage: string) => {
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
        // 최신 chatHistory 가져오기 (dependency 문제 방지)
        const cacheKey = isLoggedIn 
          ? (currentThreadId || '')
          : `guest-${ensureGuestId()}`
        const latestChatHistory = queryClient.getQueryData<any[]>(['chat-history', cacheKey, 20]) || []
        const recentMessages = latestChatHistory.slice(-5).map((h: any) => ({ content: h.message }))
        
        // 동적 일수 감지 (숫자 변수화 - 무제한 확장 가능)
        const detectMealPlanDays = (messages: any[]) => {
          for (const msg of messages) {
            const content = msg.content || ''
            
            // 숫자 + 일 패턴 감지 (N일치, N일)
            const dayPatterns = [
              /(\d+)일치/,           // 3일치, 7일치
              /(\d+)일\s*식단/,      // 3일 식단, 7일 식단
              /(\d+)일\s*키토/,      // 3일 키토, 7일 키토
              /(\d+)일\s*계획/       // 3일 계획, 7일 계획
            ]
            
            for (const pattern of dayPatterns) {
              const match = content.match(pattern)
              if (match) {
                const days = parseInt(match[1])
                if (days > 0 && days <= 365) { // 1일~365일 제한
                  return days
                }
              }
            }
            
            // 한글 숫자 패턴 감지 (확장 가능)
            const koreanNumbers = {
              '이틀': 2, '삼일': 3, '사일': 4, '오일': 5, '육일': 6, '칠일': 7,
              '팔일': 8, '구일': 9, '십일': 10, '이십일': 20, '삼십일': 30,
              '사십일': 40, '오십일': 50, '육십일': 60, '칠십일': 70,
              '팔십일': 80, '구십일': 90, '백일': 100
            }
            
            for (const [kor, num] of Object.entries(koreanNumbers)) {
              if (content.includes(`${kor}치`) && content.includes('식단')) {
                return num
              }
            }
            
            // 주 단위 패턴 감지 (N주치 = N*7일)
            const weekPatterns = [
              /(\d+)주치/,           // 1주치, 2주치
              /(\d+)주\s*식단/,      // 1주 식단, 2주 식단
              /(\d+)주\s*키토/       // 1주 키토, 2주 키토
            ]
            
            for (const pattern of weekPatterns) {
              const match = content.match(pattern)
              if (match) {
                const weeks = parseInt(match[1])
                if (weeks > 0 && weeks <= 52) { // 1주~52주 제한
                  return weeks * 7
                }
              }
            }
          }
          return null
        }
        
        // 현재 메시지도 포함하여 일수 감지
        const allMessages = [...recentMessages, { content: userMessage }]
        const mealPlanDays = detectMealPlanDays(allMessages)
        const hasMultiDayMealPlan = mealPlanDays && mealPlanDays > 1

        if (hasMultiDayMealPlan) {
          // 멀티데이 데이터는 백엔드에서만 처리 (즉시 저장 제거)
          console.log(`✅ ${mealPlanDays}일치 식단표 감지 - 백엔드 처리로 넘김`)
          return
        } else {
          // 1일치 데이터도 백엔드에서만 처리 (즉시 저장 제거)
          console.log('✅ 1일치 식단표 감지 - 백엔드 처리로 넘김')
          return
        }
      } catch (error) {
        console.error('스마트 식단 저장 실패:', error)
        addMessageToCache(`❌ 식단 저장에 실패했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`)
      } finally {
        setIsSavingMeal(null)
        setIsSaving(false)
      }
    }
  }, [user, isSaving, setIsSaving, setIsSavingMeal, parseDateFromMessage, createPlan, queryClient, addMessageToCache])

  // 백엔드 캘린더 저장 (백엔드에서 이미 저장됨 - 캐시만 무효화)
  const handleBackendCalendarSave = useCallback(async (saveData: any) => {
    if (!user?.id) return

    if (isSaving) {
      console.log('🔒 이미 저장 중입니다. 중복 저장을 방지합니다.')
      return
    }

    const { setSaveCompleted, addOptimisticMeals, removeOptimisticMeals, optimisticMeals, setCalendarLoading } = useCalendarStore.getState()
    // Optimistic Update를 위한 로딩 상태 설정
    setIsSavingMeal('auto-save')
    
    try {
      const startDate = new Date(saveData.start_date)
      const daysData = saveData.days_data || []
      // 백엔드가 1로 내려오는 경우가 있어 실제 days_data 길이로 보정
      let durationDays = saveData.duration_days
      const computedDays = Array.isArray(daysData) ? daysData.length : durationDays
      if (computedDays && computedDays > 0) {
        durationDays = computedDays
      }

      console.log(`🗓️ 백엔드에서 이미 저장 완료됨: ${durationDays}일치, 시작일: ${startDate.toISOString()}`)
      console.log(`🗓️ 백엔드에서 받은 days_data:`, daysData)

      // 🧹 기존 임시 Optimistic 데이터 제거 (실제 데이터로 교체하기 위해)
      if (optimisticMeals.length > 0) {
        console.log(`🧹 기존 임시 Optimistic 데이터 제거: ${optimisticMeals.length}개`)
        const existingMealIds = optimisticMeals.map(meal => meal.id)
        removeOptimisticMeals(existingMealIds)
      }

      // 🚀 실제 데이터로 Optimistic 데이터 추가 (UI 즉시 업데이트)
      const newOptimisticMeals: OptimisticMealData[] = []
      for (let i = 0; i < durationDays; i++) {
        const currentDate = new Date(startDate)
        currentDate.setDate(startDate.getDate() + i)
        const dateStr = format(currentDate, 'yyyy-MM-dd')
        
        const dayMeals = daysData[i] || {}
        
        for (const slot of ['breakfast', 'lunch', 'dinner', 'snack'] as const) {
          let mealTitle = ''
          if (dayMeals[slot]) {
            if (typeof dayMeals[slot] === 'string') {
              mealTitle = dayMeals[slot]
            } else if (dayMeals[slot]?.title) {
              mealTitle = dayMeals[slot].title
            }
          }
          
          // 유효한 식단만 Optimistic으로 추가
          if (mealTitle && 
              mealTitle !== 'null' && 
              mealTitle !== 'undefined' && 
              mealTitle !== 'None' &&
              !mealTitle.includes('추천 식단이 없') &&
              !mealTitle.includes('추천 불가')) {
            newOptimisticMeals.push({
              date: dateStr,
              slot,
              title: mealTitle,
              type: 'optimistic',
              id: `optimistic-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              timestamp: Date.now()
            })
          }
        }
      }
      
      // 즉시 UI에 표시
      addOptimisticMeals(newOptimisticMeals)
      console.log(`🚀 실제 데이터로 Optimistic 데이터 추가: ${newOptimisticMeals.length}개`)
      
      // 🚀 즉시 성공 메시지 표시 (Optimistic Update)
      let validMealCount = 0
      const bannedSubstrings = ['추천 식단이 없', '추천 불가']
      
      for (let i = 0; i < durationDays; i++) {
        const dayMeals = daysData[i] || {}
        
        for (const slot of ['breakfast', 'lunch', 'dinner', 'snack'] as const) {
          let mealTitle = ''
          if (dayMeals[slot]) {
            if (typeof dayMeals[slot] === 'string') {
              mealTitle = dayMeals[slot]
            } else if (dayMeals[slot]?.title) {
              mealTitle = dayMeals[slot].title
            }
          }
          
          // 유효한 식단인지 확인 (금지 문구가 없고 비어있지 않음)
          if (mealTitle && 
              mealTitle !== 'null' && 
              mealTitle !== 'undefined' && 
              mealTitle !== 'None' &&
              !bannedSubstrings.some(bs => mealTitle.includes(bs))) {
            validMealCount++
          }
        }
      }

      // 🎉 즉시 성공 메시지 표시
      let successMessage = `✅ ${durationDays}일치 식단표가 캘린더에 성공적으로 저장되었습니다! (${validMealCount}개 식단)`
      
      // 제외된 슬롯이 있으면 안내 메시지 추가
      const totalSlots = durationDays * 4 // 4개 슬롯 (아침, 점심, 저녁, 간식)
      const excludedSlots = totalSlots - validMealCount
      if (excludedSlots > 0) {
        successMessage += `\n\n📝 참고: ${excludedSlots}개 슬롯은 제약 조건으로 인해 추천되지 않았습니다.`
      }
      
      addMessageToCache(successMessage)
      console.log('🎉 즉시 성공 메시지 표시:', successMessage)

      // 🚀 백그라운드에서 비동기로 캐시 무효화 (UI 블로킹 없음)
      setTimeout(async () => {
        try {
          console.log('🔄 백그라운드에서 캐시 무효화 시작...')
          
          // 모든 캘린더 관련 쿼리 무효화
          queryClient.invalidateQueries({ queryKey: ['plans-range'] })
          queryClient.invalidateQueries({ queryKey: ['plans'] })
          queryClient.invalidateQueries({ queryKey: ['meal-log'] })
          
          // 강제로 데이터 다시 가져오기
          await queryClient.refetchQueries({ queryKey: ['plans-range'] })
          
          // 캘린더 저장 완료 이벤트 발생
          window.dispatchEvent(new CustomEvent('calendar-saved'))
          
          // 전역 상태 업데이트 (로딩 상태도 해제)
          setSaveCompleted({
            durationDays,
            validMealCount,
            startDate: saveData.start_date
          })
          
          // 전역 캘린더 로딩 상태 해제
          setCalendarLoading(false)
          console.log('✅ 전역 캘린더 로딩 상태 해제됨')
          
          // ⚠️ Optimistic 데이터는 즉시 지우지 않고 유지
          // useCalendarData가 API 데이터가 들어오면 자동으로 가려줍니다.
          console.log('✅ 백그라운드 캐시 무효화 완료 (Optimistic 데이터는 유지)')
        } catch (error) {
          console.error('❌ 백그라운드 캐시 무효화 실패:', error)
        }
      }, 500) // 500ms 후 백그라운드 실행
      
      console.log('✅ 백엔드 캘린더 저장 완료 (캐시 무효화):', { durationDays, validMealCount })
      
    } catch (error) {
      console.error('백엔드 캘린더 저장 처리 실패:', error)
      addMessageToCache(`❌ 식단 저장 처리에 실패했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`)
    } finally {
      setIsSavingMeal(null)
      // Optimistic Update 완료 후 로딩 상태 해제
      setIsSaving(false)
    }
  }, [user, isSaving, setIsSaving, setIsSavingMeal, queryClient, addMessageToCache])

  return {
    handleSendMessage,
    handleKeyDown,
    handleQuickMessage,
    handleSaveMealToCalendar,
    handlePlaceMarkerClick
  }
}
