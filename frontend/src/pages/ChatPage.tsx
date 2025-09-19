import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, Plus, MessageSquare, Trash2, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useChatStore } from '@/store/chatStore'
import { useProfileStore } from '@/store/profileStore'
import { RecipeCard } from '@/components/RecipeCard'
import { PlaceCard } from '@/components/PlaceCard'
import { useSendMessage } from '@/hooks/useApi'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  results?: any[]
  timestamp: Date
}

interface ChatSession {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
}

export function ChatPage() {
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [hasStartedChatting, setHasStartedChatting] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)
  
  const { messages, addMessage, clearMessages } = useChatStore()
  const { profile } = useProfileStore()
  const sendMessage = useSendMessage()

  // 시간 포맷팅 함수들
  const formatMessageTime = (timestamp: Date) => {
    const now = new Date()
    const diff = now.getTime() - timestamp.getTime()
    
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
    return timestamp.toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDetailedTime = (timestamp: Date) => {
    return timestamp.toLocaleString('ko-KR', {
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
    
    const timeDiff = currentMessage.timestamp.getTime() - previousMessage.timestamp.getTime()
    
    // 5분 이상 차이나면 타임스탬프 표시
    return timeDiff > 300000
  }

  const shouldShowDateSeparator = (currentIndex: number) => {
    if (currentIndex === 0) return true
    
    const currentMessage = messages[currentIndex]
    const previousMessage = messages[currentIndex - 1]
    
    if (!currentMessage || !previousMessage) return false
    
    const currentDate = currentMessage.timestamp.toDateString()
    const previousDate = previousMessage.timestamp.toDateString()
    
    return currentDate !== previousDate
  }

  const formatDateSeparator = (timestamp: Date) => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 86400000)
    const messageDate = new Date(timestamp.getFullYear(), timestamp.getMonth(), timestamp.getDate())
    
    if (messageDate.getTime() === today.getTime()) {
      return '오늘'
    } else if (messageDate.getTime() === yesterday.getTime()) {
      return '어제'
    } else {
      return timestamp.toLocaleDateString('ko-KR', {
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
    setHasStartedChatting(false)
  }

  // 채팅 세션 삭제
  const deleteChatSession = (sessionId: string) => {
    setChatSessions(prev => prev.filter(session => session.id !== sessionId))
    if (currentSessionId === sessionId) {
      setCurrentSessionId(null)
      clearMessages()
      setHasStartedChatting(false) // 초기 화면으로 돌아가기
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
      setHasStartedChatting(session.messages.length > 0)
    }
  }

  // 현재 세션에 메시지 추가
  const addMessageToCurrentSession = (message: Message) => {
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

    // 채팅 시작 상태로 변경
    setHasStartedChatting(true)

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

    const userMessage: Message = {
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
        profile,
        location: undefined, // TODO: 위치 정보 연동
        radius_km: 5
      })

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        results: response.results,
        timestamp: new Date()
      }

      addMessage(assistantMessage)
      addMessageToCurrentSession(assistantMessage)

      // 첫 번째 메시지인 경우 세션 제목 업데이트
      if (sessionId && messages.length === 0) {
        setChatSessions(prev => prev.map(session =>
          session.id === sessionId
            ? { ...session, title: userMessage.content.slice(0, 30) + (userMessage.content.length > 30 ? '...' : '') }
            : session
        ))
      }
    } catch (error) {
      console.error('메시지 전송 실패:', error)
      const errorMessage: Message = {
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

  // 빠른 질문 메시지 전송
  const handleQuickMessage = async (quickMessage: string) => {
    if (!quickMessage.trim() || isLoading) return

    // 채팅 시작 상태로 변경
    setHasStartedChatting(true)

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

    const userMessage: Message = {
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
        profile,
        location: undefined, // TODO: 위치 정보 연동
        radius_km: 5
      })

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        results: response.results,
        timestamp: new Date()
      }

      addMessage(assistantMessage)
      addMessageToCurrentSession(assistantMessage)

      // 첫 번째 메시지인 경우 세션 제목 업데이트
      if (sessionId && messages.length === 0) {
        setChatSessions(prev => prev.map(session =>
          session.id === sessionId
            ? { ...session, title: userMessage.content.slice(0, 30) + (userMessage.content.length > 30 ? '...' : '') }
            : session
        ))
      }
    } catch (error) {
      console.error('메시지 전송 실패:', error)
      const errorMessage: Message = {
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
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-gradient-to-br from-background to-muted/20">
      {/* 헤더 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gradient">키토 코치</h1>
        <p className="text-muted-foreground mt-1">건강한 키토 식단을 위한 AI 어시스턴트</p>
      </div>

      {/* 메인 콘텐츠 영역 */}
      <div className="flex flex-1 gap-4 lg:gap-6 px-4 lg:px-6 min-h-0">
        {/* 왼쪽 사이드바 - 데스크톱에서만 표시 */}
        <div className="hidden lg:block w-80 bg-card/50 backdrop-blur-sm border border-border/50 rounded-xl shadow-sm flex flex-col">
          {/* 사이드바 헤더 */}
          <div className="p-6 border-b border-border/50">
            <Button 
              onClick={createNewChat}
              className="w-full justify-center gap-3 h-12 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-200 mb-4"
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
                    className={`group relative p-4 rounded-xl cursor-pointer transition-all duration-200 ${currentSessionId === session.id
                      ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg'
                      : 'hover:bg-muted/50 hover:shadow-md'
                      }`}
                    onClick={() => selectChatSession(session.id)}
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
                        className={`opacity-0 group-hover:opacity-100 h-7 w-7 p-0 transition-opacity duration-200 ${currentSessionId === session.id ? 'text-white hover:bg-white/20' : 'hover:bg-muted'
                          }`}
                        onClick={(e) => {
                          e.stopPropagation()
                          deleteChatSession(session.id)
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
        <div className="flex-1 flex flex-col bg-card/30 backdrop-blur-sm border border-border/50 rounded-xl shadow-sm min-h-0 w-full lg:w-auto">
          {!hasStartedChatting ? (
            // 채팅 시작 전 - 가운데 입력창
            <div className="flex-1 flex items-center justify-center p-8 overflow-hidden">
              <div className="w-full max-w-3xl">
                <div className="text-center mb-8 lg:mb-12">
                  <div className="w-24 h-24 lg:w-32 lg:h-32 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center mx-auto mb-4 lg:mb-6 shadow-lg">
                    <Bot className="h-12 w-12 lg:h-16 lg:w-16 text-white" />
                  </div>
                  <h3 className="text-2xl lg:text-3xl font-bold mb-3 lg:mb-4 bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                    안녕하세요! 키토 코치입니다
                  </h3>
                  <p className="text-muted-foreground text-lg lg:text-xl leading-relaxed px-4">
                    건강한 키토 식단을 위한 모든 것을 도와드릴게요.<br />
                    레시피 추천부터 식당 찾기까지 무엇이든 물어보세요!
                  </p>
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
                        className="h-12 lg:h-14 text-base lg:text-lg pl-4 lg:pl-6 pr-12 lg:pr-16 bg-background/80 border-border/50 rounded-xl lg:rounded-2xl shadow-lg focus:shadow-xl transition-all duration-200"
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
                      className="h-12 lg:h-14 px-4 lg:px-8 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-medium rounded-xl lg:rounded-2xl shadow-lg hover:shadow-xl transition-all duration-200"
                    >
                      <Send className="h-4 w-4 lg:h-5 lg:w-5" />
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
                        className="text-xs lg:text-sm px-3 lg:px-4 py-1 lg:py-2 rounded-lg lg:rounded-xl border-border/50 hover:bg-muted/50 hover:shadow-md transition-all duration-200"
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
                            <div className={`flex-shrink-0 w-8 h-8 lg:w-10 lg:h-10 rounded-full flex items-center justify-center shadow-md ${
                              msg.role === 'user' 
                                ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white' 
                                : 'bg-gradient-to-r from-green-500 to-emerald-500 text-white'
                            }`}>
                              {msg.role === 'user' ? <User className="h-4 w-4 lg:h-5 lg:w-5" /> : <span className="text-sm lg:text-lg">🥑</span>}
                            </div>

                            {/* 메시지 내용 */}
                            <div className={`flex-1 max-w-2xl ${msg.role === 'user' ? 'text-right' : ''}`}>
                              <div className={`inline-block p-3 lg:p-4 rounded-xl lg:rounded-2xl shadow-sm ${
                                msg.role === 'user' 
                                  ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white' 
                                  : 'bg-card border border-border/50'
                              }`}>
                                <p className="text-sm lg:text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
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
              <div className="flex-shrink-0 border-t border-border/50 bg-background/50 backdrop-blur-sm p-4 lg:p-6">
                <div className="max-w-4xl mx-auto">
                  <div className="flex gap-2 lg:gap-3">
                    <div className="flex-1 relative">
                      <Input
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="키토 식단에 대해 무엇이든 물어보세요..."
                        className="h-10 lg:h-12 pl-3 lg:pl-4 pr-10 lg:pr-12 bg-background/80 border-border/50 rounded-lg lg:rounded-xl shadow-sm focus:shadow-md transition-all duration-200"
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
                      className="h-10 lg:h-12 px-4 lg:px-6 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-lg lg:rounded-xl shadow-sm hover:shadow-md transition-all duration-200"
                    >
                      <Send className="h-3 w-3 lg:h-4 lg:w-4" />
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
                        className="text-xs px-2 lg:px-3 py-1 rounded-md lg:rounded-lg border-border/50 hover:bg-muted/50 hover:shadow-sm transition-all duration-200"
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
