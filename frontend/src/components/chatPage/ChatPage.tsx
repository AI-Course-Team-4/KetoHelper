import { useState, useEffect, useRef } from 'react'
import { useChatLogic } from './hooks/useChatLogic'
import { useMessageHandlers } from './hooks/useMessageHandlers'
import { useThreadHandlers } from './hooks/useThreadHandlers'
import { ThreadSidebar } from './ThreadSidebar'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { EmptyWelcome } from './EmptyWelcome'
import { ActiveWelcome } from './ActiveWelcome'
import { CircularProgress } from '@mui/material'

export function ChatPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  
  const {
    message,
    setMessage,
    isLoading,
    currentThreadId,
    isSavingMeal,
    userLocation,
    selectedPlaceIndexByMsg,
    setSelectedPlaceIndexByMsg,
    isLoadingThread,
    shouldAutoScroll,
    setShouldAutoScroll,
    messagesEndRef,
    scrollAreaRef,
    messages,
    chatHistory,
    profile,
    user,
    chatThreads,
    isLoggedIn,
    isLoadingHistory,
    isSaving,
    setIsSaving,
    refetchThreads,
    setCurrentThreadId,
    setIsLoading,
    setIsSavingMeal,
    setIsLoadingThread
  } = useChatLogic()

  const {
    handleSendMessage,
    handleKeyDown,
    handleQuickMessage,
    handleSaveMealToCalendar
  } = useMessageHandlers({
    message,
    setMessage,
    isLoading,
    setIsLoading,
    currentThreadId,
    setCurrentThreadId,
    isSaving,
    setIsSaving,
    setIsSavingMeal,
    chatHistory,
    messages,
    isLoggedIn,
    refetchThreads,
    inputRef
  })

  const {
    handleCreateNewChat,
    handleSelectThread,
    handleDeleteThread
  } = useThreadHandlers({
    currentThreadId,
    setCurrentThreadId,
    setMessage,
    setIsLoadingThread,
    refetchThreads
  })

  // 실시간 타임스탬프 갱신을 위한 상태
  const [, forceUpdate] = useState(0)

  // 1분마다 타임스탬프 갱신
  useEffect(() => {
    const interval = setInterval(() => {
      forceUpdate((prev: number) => prev + 1)
    }, 60000) // 1분마다 갱신

    return () => clearInterval(interval)
  }, [])

  // 시간 포맷팅 함수들
  const formatMessageTime = (timestamp: Date) => {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()

    if (diff < 60000) return '방금 전'
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000)
      return `${minutes}분 전`
    }
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000)
      return `${hours}시간 전`
    }
    if (diff < 604800000) {
      const days = Math.floor(diff / 86400000)
      return `${days}일 전`
    }

    return date.toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDetailedTime = (timestamp: Date) => {
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

    // 로그인 상태에 따라 올바른 배열 사용
    const messageList = isLoggedIn ? chatHistory : messages
    const currentMessage = messageList[currentIndex]
    const previousMessage = messageList[currentIndex - 1]

    if (!currentMessage || !previousMessage) return true

    // 로그인 사용자: created_at 사용, 게스트 사용자: timestamp 사용
    const currentTime = isLoggedIn
      ? new Date((currentMessage as any).created_at)
      : (currentMessage as any).timestamp instanceof Date 
        ? (currentMessage as any).timestamp 
        : new Date((currentMessage as any).timestamp)
    
    const previousTime = isLoggedIn
      ? new Date((previousMessage as any).created_at)
      : (previousMessage as any).timestamp instanceof Date 
        ? (previousMessage as any).timestamp 
        : new Date((previousMessage as any).timestamp)

    const timeDiff = currentTime.getTime() - previousTime.getTime()
    return timeDiff > 60000
  }

  const shouldShowDateSeparator = (currentIndex: number) => {
    if (currentIndex === 0) return true

    // 로그인 상태에 따라 올바른 배열 사용
    const messageList = isLoggedIn ? chatHistory : messages
    const currentMessage = messageList[currentIndex]
    const previousMessage = messageList[currentIndex - 1]

    if (!currentMessage || !previousMessage) return false

    // 로그인 사용자: created_at 사용, 게스트 사용자: timestamp 사용
    const currentTime = isLoggedIn
      ? new Date((currentMessage as any).created_at)
      : (currentMessage as any).timestamp instanceof Date 
        ? (currentMessage as any).timestamp 
        : new Date((currentMessage as any).timestamp)
    
    const previousTime = isLoggedIn
      ? new Date((previousMessage as any).created_at)
      : (previousMessage as any).timestamp instanceof Date 
        ? (previousMessage as any).timestamp 
        : new Date((previousMessage as any).timestamp)

    const currentDate = currentTime.toDateString()
    const previousDate = previousTime.toDateString()

    return currentDate !== previousDate
  }

  const formatDateSeparator = (timestamp: Date) => {
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
        {/* 왼쪽 사이드바 - 로그인 사용자만 표시 */}
        {isLoggedIn && (
          <ThreadSidebar
            chatThreads={chatThreads}
            currentThreadId={currentThreadId}
            isLoading={isLoading}
            isLoadingThread={isLoadingThread}
            onCreateNewChat={handleCreateNewChat}
            onSelectThread={handleSelectThread}
            onDeleteThread={handleDeleteThread}
          />
        )}

        {/* 메인 채팅 영역 */}
        <div className="flex-1 flex flex-col bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl min-h-0 w-full lg:w-auto overflow-hidden">
          {isLoadingThread || (isLoggedIn && isLoadingHistory) ? (
            // 스레드 로딩 중 또는 메시지 로딩 중
            <div className="flex-1 flex items-center justify-center p-8 overflow-hidden">
              <div className="text-center">
                <div className="w-16 h-16 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <CircularProgress size={32} sx={{ color: 'white' }} />
                </div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">채팅을 불러오는 중...</h3>
                <p className="text-sm text-gray-500">잠시만 기다려주세요</p>
              </div>
            </div>
          ) : isLoggedIn && chatThreads.length === 0 ? (
            // 로그인 사용자만 스레드가 없을 때 빈 웰컴
            <EmptyWelcome
              onCreateNewChat={handleCreateNewChat}
            />
          ) : messages.length === 0 ? (
            // 스레드가 있지만 메시지가 없을 때 - 활성 웰컴 스크린
            <ActiveWelcome
              message={message}
              isLoading={isLoading}
              onMessageChange={setMessage}
              onSendMessage={handleSendMessage}
              onKeyDown={handleKeyDown}
              onQuickMessage={handleQuickMessage}
            />
          ) : (
            // 채팅 시작 후 - 일반 채팅 레이아웃
            <>
              {/* 메시지 영역 */}
              <MessageList
                messages={messages}
                chatHistory={chatHistory}
                isLoggedIn={isLoggedIn}
                isLoading={isLoading}
                scrollAreaRef={scrollAreaRef}
                messagesEndRef={messagesEndRef}
                shouldAutoScroll={shouldAutoScroll}
                setShouldAutoScroll={setShouldAutoScroll}
                shouldShowTimestamp={shouldShowTimestamp}
                shouldShowDateSeparator={shouldShowDateSeparator}
                formatMessageTime={formatMessageTime}
                formatDetailedTime={formatDetailedTime}
                formatDateSeparator={formatDateSeparator}
                user={user}
                profile={profile}
                isSavingMeal={isSavingMeal}
                userLocation={userLocation}
                selectedPlaceIndexByMsg={selectedPlaceIndexByMsg}
                onSaveMealToCalendar={handleSaveMealToCalendar}
                onPlaceMarkerClick={(messageId, index) => {
                  setSelectedPlaceIndexByMsg(prev => ({ ...prev, [messageId]: index }))
                }}
              />

              {/* 입력 영역 */}
              <MessageInput
                ref={inputRef}
                message={message}
                isLoading={isLoading}
                isChatLimitReached={isLoggedIn ? chatHistory.length >= 20 : messages.length >= 20}
                onMessageChange={setMessage}
                onSendMessage={handleSendMessage}
                onKeyDown={handleKeyDown}
                onQuickMessage={handleQuickMessage}
              />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
