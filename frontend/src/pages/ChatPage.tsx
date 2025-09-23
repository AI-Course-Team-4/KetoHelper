import { useState, useRef, useEffect } from 'react'
import { Send, User, Loader2, Plus, MessageSquare, Trash2, Clock, Calendar, Save } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useChatStore, ChatMessage, LLMParsedMeal } from '@/store/chatStore'
import { useProfileStore } from '@/store/profileStore'
import { useAuthStore } from '@/store/authStore'
import { RecipeCard } from '@/components/RecipeCard'
import { PlaceCard } from '@/components/PlaceCard'
import { useSendMessage } from '@/hooks/useApi'
import { MealParserService, MealService } from '@/lib/mealService'
import { MealData } from '@/data/ketoMeals'
import { format } from 'date-fns'

// Message 타입을 ChatMessage로 대체

interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: Date
}

export function ChatPage() {
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)
  const [isSavingMeal, setIsSavingMeal] = useState<string | null>(null) // 저장 중인 메시지 ID
  
  const { messages, addMessage, clearMessages } = useChatStore()
  // hasStartedChatting을 메시지 존재 여부로 계산
  const hasStartedChatting = messages.length > 0
  const { profile } = useProfileStore()
  const { user } = useAuthStore()
  const sendMessage = useSendMessage()

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
    if (shouldAutoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }

  const handleScroll = () => {
    const scrollElement = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]')
    if (!scrollElement) return
    
    const { scrollTop, scrollHeight, clientHeight } = scrollElement
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50
    
    setShouldAutoScroll(isAtBottom)
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const scrollElement = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]')
    if (scrollElement) {
      scrollElement.addEventListener('scroll', handleScroll)
      return () => scrollElement.removeEventListener('scroll', handleScroll)
    }
  }, [hasStartedChatting])

  // 새 채팅 세션 생성
  const createNewChat = () => {
    const newSessionId = Date.now().toString()
    const newSession: ChatSession = {
      id: newSessionId,
      title: '새 채팅',
      messages: [],
      createdAt: new Date()
    }

    setChatSessions(prev => [newSession, ...prev])
    setCurrentSessionId(newSessionId)
    clearMessages()
    setMessage('')
  }

  // 채팅 세션 삭제
  const deleteChatSession = (sessionId: string) => {
    setChatSessions(prev => prev.filter(session => session.id !== sessionId))
    if (currentSessionId === sessionId) {
      setCurrentSessionId(null)
      clearMessages()
    }
  }

  // 채팅 세션 선택
  const selectChatSession = (sessionId: string) => {
    const session = chatSessions.find(s => s.id === sessionId)
    if (session) {
      setCurrentSessionId(sessionId)
      // 선택된 세션의 메시지들을 채팅 스토어에 로드
      clearMessages()
      session.messages.forEach(msg => addMessage(msg))
    }
  }

  // 현재 세션에 메시지 추가
  const addMessageToCurrentSession = (message: ChatMessage) => {
    if (currentSessionId) {
      setChatSessions(prev => prev.map(session =>
        session.id === currentSessionId
          ? { ...session, messages: [...session.messages, message] }
          : session
      ))
    }
  }

  const handleSendMessage = async () => {
    if (!message.trim() || isLoading) return

    // 현재 세션이 없으면 새 세션 생성
    let sessionId = currentSessionId
    if (!sessionId) {
      const newSessionId = Date.now().toString()
      const newSession: ChatSession = {
        id: newSessionId,
        title: '새 채팅',
        messages: [],
        createdAt: new Date()
      }

      setChatSessions(prev => [newSession, ...prev])
      setCurrentSessionId(newSessionId)
      sessionId = newSessionId
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message.trim(),
      timestamp: new Date()
    }

    addMessage(userMessage)
    addMessageToCurrentSession(userMessage)
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
        radius_km: 5
      })

      // 백엔드 응답에서 식단 데이터 파싱
      let parsedMeal = MealParserService.parseMealFromBackendResponse(response)
      
      // 테스트용: 식단 추천 관련 메시지인 경우 임시 데이터 생성
      if (!parsedMeal && (
        userMessage.content.includes('식단') || 
        userMessage.content.includes('추천') ||
        userMessage.content.includes('메뉴') ||
        userMessage.content.includes('아침') ||
        userMessage.content.includes('점심') ||
        userMessage.content.includes('저녁')
      )) {
        parsedMeal = {
          breakfast: '아보카도 토스트와 스크램블 에그',
          lunch: '그릴 치킨 샐러드 (올리브오일 드레싱)',
          dinner: '연어 스테이크와 구운 브로콜리',
          snack: '아몬드 한 줌과 치즈 큐브'
        }
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
      addMessageToCurrentSession(assistantMessage)

      // 첫 번째 메시지인 경우 세션 제목 업데이트 (사용자 메시지가 첫 번째 메시지인지 확인)
      if (sessionId) {
        setChatSessions(prev => prev.map(session => {
          if (session.id === sessionId && session.title === '새 채팅') {
            return { ...session, title: userMessage.content.slice(0, 30) + (userMessage.content.length > 30 ? '...' : '') }
          }
          return session
        }))
      }
    } catch (error) {
      console.error('메시지 전송 실패:', error)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '죄송합니다. 메시지 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date()
      }
      addMessage(errorMessage)
      addMessageToCurrentSession(errorMessage)
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

  // 식단 캘린더에 저장
  const handleSaveMealToCalendar = async (messageId: string, mealData: LLMParsedMeal, targetDate?: string) => {
    if (!user?.id) {
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: '❌ 식단 저장을 위해 로그인이 필요합니다.',
        timestamp: new Date()
      }
      addMessage(errorMessage)
      addMessageToCurrentSession(errorMessage)
      return
    }

    setIsSavingMeal(messageId)
    
    try {
      const dateToSave = targetDate || format(new Date(), 'yyyy-MM-dd')
      
      const mealToSave: MealData = {
        breakfast: mealData.breakfast || '',
        lunch: mealData.lunch || '',
        dinner: mealData.dinner || '',
        snack: mealData.snack || ''
      }
      
      const success = await MealService.saveMeal(dateToSave, mealToSave, user.id)
      
      if (success) {
        // 성공 메시지 추가
        const successMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `✅ 식단이 ${format(new Date(dateToSave), 'M월 d일')} 캘린더에 저장되었습니다! 캘린더 페이지에서 확인해보세요.`,
          timestamp: new Date()
        }
        
        addMessage(successMessage)
        addMessageToCurrentSession(successMessage)
      } else {
        throw new Error('저장 실패')
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
      addMessageToCurrentSession(errorMessage)
    } finally {
      setIsSavingMeal(null)
    }
  }

  // 빠른 질문 메시지 전송
  const handleQuickMessage = async (quickMessage: string) => {
    if (!quickMessage.trim() || isLoading) return

    // 현재 세션이 없으면 새 세션 생성
    let sessionId = currentSessionId
    if (!sessionId) {
      const newSessionId = Date.now().toString()
      const newSession: ChatSession = {
        id: newSessionId,
        title: '새 채팅',
        messages: [],
        createdAt: new Date()
      }

      setChatSessions(prev => [newSession, ...prev])
      setCurrentSessionId(newSessionId)
      sessionId = newSessionId
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: quickMessage.trim(),
      timestamp: new Date()
    }

    addMessage(userMessage)
    addMessageToCurrentSession(userMessage)
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
        radius_km: 5
      })

      // 백엔드 응답에서 식단 데이터 파싱
      let parsedMeal = MealParserService.parseMealFromBackendResponse(response)
      
      // 테스트용: 식단 추천 관련 메시지인 경우 임시 데이터 생성
      if (!parsedMeal && (
        userMessage.content.includes('식단') || 
        userMessage.content.includes('추천') ||
        userMessage.content.includes('메뉴') ||
        userMessage.content.includes('아침') ||
        userMessage.content.includes('점심') ||
        userMessage.content.includes('저녁')
      )) {
        parsedMeal = {
          breakfast: '아보카도 토스트와 스크램블 에그',
          lunch: '그릴 치킨 샐러드 (올리브오일 드레싱)',
          dinner: '연어 스테이크와 구운 브로콜리',
          snack: '아몬드 한 줌과 치즈 큐브'
        }
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
      addMessageToCurrentSession(assistantMessage)

      // 첫 번째 메시지인 경우 세션 제목 업데이트 (사용자 메시지가 첫 번째 메시지인지 확인)
      if (sessionId) {
        setChatSessions(prev => prev.map(session => {
          if (session.id === sessionId && session.title === '새 채팅') {
            return { ...session, title: userMessage.content.slice(0, 30) + (userMessage.content.length > 30 ? '...' : '') }
          }
          return session
        }))
      }
    } catch (error) {
      console.error('메시지 전송 실패:', error)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '죄송합니다. 메시지 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date()
      }
      addMessage(errorMessage)
      addMessageToCurrentSession(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-gradient-to-br from-green-50 via-white to-emerald-50">
      {/* 헤더 */}
      <div className="mb-6">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-green-500 via-emerald-500 to-teal-600 text-white">
          <div className="absolute inset-0 bg-white/10 backdrop-blur-sm" />
          <div className="relative p-6">
            <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
              <span className="text-4xl">🥑</span>
              키토 코치
            </h1>
            <p className="text-green-100 text-lg">건강한 키토 식단을 위한 AI 어시스턴트</p>
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 영역 */}
      <div className="flex flex-1 gap-4 lg:gap-6 px-4 lg:px-6 min-h-0">
        {/* 왼쪽 사이드바 - 데스크톱에서만 표시 */}
        <div className="hidden lg:block w-80 bg-white/80 backdrop-blur-sm border-0 rounded-2xl shadow-xl flex flex-col">
          {/* 사이드바 헤더 */}
          <div className="p-6 border-b border-gray-100">
            <Button 
              onClick={createNewChat}
              disabled={isLoading}
              className={`w-full justify-center gap-3 h-14 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-300 mb-4 rounded-xl ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
              variant="default"
            >
              <Plus className="h-5 w-5" />
              새 채팅 시작
            </Button>

            {/* 채팅 히스토리 */}
            <ScrollArea className="max-h-[60vh]">
              <div className="space-y-3">
                {chatSessions.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mx-auto mb-4">
                      <MessageSquare className="h-8 w-8" />
                    </div>
                    <p className="text-sm font-medium mb-1">아직 채팅이 없습니다</p>
                    <p className="text-xs opacity-70">새 채팅을 시작해보세요!</p>
                  </div>
                )}

                {chatSessions.map((session) => (
                  <div
                    key={session.id}
                    className={`group relative p-4 rounded-xl transition-all duration-300 ${currentSessionId === session.id
                      ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg border border-green-300'
                      : 'bg-gray-50 hover:bg-green-50 hover:shadow-md border border-gray-200 hover:border-green-200'
                      } ${isLoading ? 'cursor-not-allowed opacity-75' : 'cursor-pointer'}`}
                    onClick={() => {
                      if (!isLoading) {
                        selectChatSession(session.id)
                      }
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium truncate mb-1">
                          {session.title}
                        </h4>
                        <p className={`text-xs ${currentSessionId === session.id ? 'text-white/70' : 'text-muted-foreground'
                          }`}>
                          {session.createdAt.toLocaleDateString()}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={isLoading}
                        className={`opacity-0 group-hover:opacity-100 h-7 w-7 p-0 transition-opacity duration-200 ${currentSessionId === session.id ? 'text-white hover:bg-white/20' : 'hover:bg-muted'
                          } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation()
                          if (!isLoading) {
                            deleteChatSession(session.id)
                          }
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        </div>

        {/* 메인 채팅 영역 */}
        <div className="flex-1 flex flex-col bg-white/80 backdrop-blur-sm border-0 rounded-2xl shadow-xl min-h-0 w-full lg:w-auto">
          {!hasStartedChatting ? (
            // 채팅 시작 전 - 가운데 입력창
            <div className="flex-1 flex items-center justify-center p-8 overflow-hidden">
              <div className="w-full max-w-3xl">
                <div className="text-center mb-8 lg:mb-12">
                  <div className="w-28 h-28 lg:w-36 lg:h-36 rounded-full bg-gradient-to-br from-green-500 via-emerald-500 to-teal-500 flex items-center justify-center mx-auto mb-6 lg:mb-8 shadow-2xl ring-4 ring-green-100">
                    <span className="text-5xl lg:text-6xl">🥑</span>
                  </div>
                  <h3 className="text-3xl lg:text-4xl font-bold mb-4 lg:mb-6 bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 bg-clip-text text-transparent">
                    안녕하세요! 키토 코치입니다
                  </h3>
                  {user ? (
                    <p className="text-gray-600 text-lg lg:text-xl leading-relaxed px-4 max-w-2xl mx-auto">
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
                        className="h-14 lg:h-16 text-base lg:text-lg pl-6 lg:pl-8 pr-12 lg:pr-16 bg-white border-2 border-gray-200 focus:border-green-400 rounded-2xl shadow-lg focus:shadow-xl transition-all duration-300"
                        disabled={isLoading}
                      />
                      {isLoading && (
                        <div className="absolute right-3 lg:right-4 top-1/2 -translate-y-1/2">
                          <Loader2 className="h-4 w-4 lg:h-5 lg:w-5 animate-spin text-muted-foreground" />
                        </div>
                      )}
                    </div>
                    <Button 
                      onClick={handleSendMessage}
                      disabled={!message.trim() || isLoading}
                      className="h-14 lg:h-16 px-6 lg:px-8 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300"
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
              <div className="flex-1 min-h-0 flex flex-col">
                <ScrollArea ref={scrollAreaRef} className="flex-1 p-4 lg:p-6">
                  <div className="max-w-4xl mx-auto">
                    <div className="space-y-4 lg:space-y-6">
                      {messages.map((msg, index) => (
                        <div key={msg.id}>
                          {/* 날짜 구분선 */}
                          {shouldShowDateSeparator(index) && (
                            <div className="flex items-center justify-center my-6">
                              <div className="flex items-center gap-3 px-4 py-2 bg-muted/30 rounded-full border border-border/50">
                                <Clock className="h-3 w-3 text-muted-foreground" />
                                <span className="text-xs font-medium text-muted-foreground">
                                  {formatDateSeparator(msg.timestamp)}
                                </span>
                              </div>
                            </div>
                          )}

                          <div className={`flex items-start gap-3 lg:gap-4 ${
                            msg.role === 'user' ? 'flex-row-reverse' : ''
                          }`}>
                            {/* 아바타 */}
                            <div className={`flex-shrink-0 w-10 h-10 lg:w-12 lg:h-12 rounded-full flex items-center justify-center shadow-lg ring-2 ${
                              msg.role === 'user' 
                                ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white ring-blue-200' 
                                : 'bg-gradient-to-r from-green-500 to-emerald-500 text-white ring-green-200'
                            }`}>
                              {msg.role === 'user' ? <User className="h-5 w-5 lg:h-6 lg:w-6" /> : <span className="text-lg lg:text-xl">🥑</span>}
                            </div>

                            {/* 메시지 내용 */}
                            <div className={`flex-1 max-w-2xl ${msg.role === 'user' ? 'text-right' : ''}`}>
                              <div className={`inline-block p-4 lg:p-5 rounded-2xl lg:rounded-3xl shadow-lg ${
                                msg.role === 'user' 
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
                                      <Calendar className="h-5 w-5" />
                                      추천받은 식단
                                    </h4>
                                    <Button
                                      size="sm"
                                      onClick={() => handleSaveMealToCalendar(msg.id, msg.mealData!)}
                                      disabled={isSavingMeal === msg.id}
                                      className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
                                    >
                                      {isSavingMeal === msg.id ? (
                                        <>
                                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                          저장 중...
                                        </>
                                      ) : (
                                        <>
                                          <Save className="h-4 w-4 mr-2" />
                                          캘린더에 저장
                                        </>
                                      )}
                                    </Button>
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
                              {msg.results && msg.results.length > 0 && (
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 lg:gap-4 mt-3 lg:mt-4">
                                  {msg.results.map((result, index) => (
                                    <div key={index}>
                                      {result.title && result.ingredients ? (
                                        <RecipeCard recipe={result} />
                                      ) : result.name && result.address ? (
                                        <PlaceCard place={result} />
                                      ) : null}
                                    </div>
                                  ))}
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
                          <div className="bg-card border border-border/50 p-3 lg:p-4 rounded-xl lg:rounded-2xl shadow-sm">
                            <div className="flex items-center gap-2 lg:gap-3">
                              <Loader2 className="h-3 w-3 lg:h-4 lg:w-4 animate-spin text-green-500" />
                              <span className="text-xs lg:text-sm text-muted-foreground">키토 코치가 생각하고 있어요...</span>
                            </div>
                          </div>
                        </div>
                      )}

                      <div ref={messagesEndRef} />
                    </div>
                  </div>
                </ScrollArea>
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
                        className="h-12 lg:h-14 pl-4 lg:pl-6 pr-12 lg:pr-14 bg-white border-2 border-gray-200 focus:border-green-400 rounded-xl lg:rounded-2xl shadow-lg focus:shadow-xl transition-all duration-300"
                        disabled={isLoading}
                      />
                      {isLoading && (
                        <div className="absolute right-2 lg:right-3 top-1/2 -translate-y-1/2">
                          <Loader2 className="h-3 w-3 lg:h-4 lg:w-4 animate-spin text-muted-foreground" />
                        </div>
                      )}
                    </div>
                    <Button 
                      onClick={handleSendMessage}
                      disabled={!message.trim() || isLoading}
                      className="h-12 lg:h-14 px-4 lg:px-6 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-xl lg:rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300"
                    >
                      <Send className="h-4 w-4 lg:h-5 lg:w-5" />
                    </Button>
                  </div>
                  
                  {/* 빠른 질문 버튼들 */}
                  <div className="flex flex-wrap gap-1 lg:gap-2 mt-3 lg:mt-4">
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
