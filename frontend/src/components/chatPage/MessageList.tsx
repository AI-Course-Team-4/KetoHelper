import { CircularProgress } from '@mui/material'
import { useEffect, useRef } from 'react'
import { ChatMessage } from '@/store/chatStore'
import { ChatHistory } from '@/hooks/useApi'
import { MessageItem } from './MessageItem'

interface MessageListProps {
  messages: ChatMessage[]
  chatHistory: ChatHistory[]
  isLoggedIn: boolean
  isLoading: boolean
  loadingStep: 'thinking' | 'analyzing' | 'generating' | 'finalizing'
  scrollAreaRef: React.RefObject<HTMLDivElement>
  messagesEndRef: React.RefObject<HTMLDivElement>
  shouldAutoScroll: boolean
  setShouldAutoScroll: (should: boolean) => void
  shouldShowTimestamp: (index: number) => boolean
  shouldShowDateSeparator: (index: number) => boolean
  formatMessageTime: (timestamp: Date) => string
  formatDetailedTime: (timestamp: Date) => string
  formatDateSeparator: (timestamp: Date) => string
  user: any
  profile: any
  isSavingMeal: string | null
  userLocation: { lat: number; lng: number } | null
  selectedPlaceIndexByMsg: Record<string, number | null>
  onSaveMealToCalendar: (messageId: string, mealData: any, targetDate?: string) => void
  onPlaceMarkerClick: (messageId: string, index: number) => void
}

export function MessageList({
  messages,
  chatHistory,
  isLoggedIn,
  isLoading,
  loadingStep,
  scrollAreaRef,
  messagesEndRef,
  shouldAutoScroll,
  setShouldAutoScroll,
  shouldShowTimestamp,
  shouldShowDateSeparator,
  formatMessageTime,
  formatDetailedTime,
  formatDateSeparator,
  user,
  profile,
  isSavingMeal,
  userLocation,
  selectedPlaceIndexByMsg,
  onSaveMealToCalendar,
  onPlaceMarkerClick
}: MessageListProps) {
  // 이전 메시지 길이를 추적하기 위한 ref
  const prevMessageLengthRef = useRef(0)
  
  // 자동 스크롤 유틸: 하단 고정
  const scrollToBottom = () => {
    if (!shouldAutoScroll) return
    const container = scrollAreaRef.current as HTMLDivElement | null
    if (!container) return
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
  }

  // (상단 고정 모드는 비활성화)

  // 스크롤 이벤트 핸들러
  const handleScroll = () => {
    const container = scrollAreaRef.current
    if (!container) return

    const { scrollTop, scrollHeight, clientHeight } = container
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50
    if (isAtBottom !== shouldAutoScroll) setShouldAutoScroll(isAtBottom)
  }

  // 메시지가 변경될 때마다 자동 스크롤
  useEffect(() => {
    const currentLength = messages.length // messages 길이를 사용 (게스트/로그인 통합)
    const prevLength = prevMessageLengthRef.current
    
    // 새 메시지가 추가되었을 때만 자동 스크롤 활성화
    if (currentLength > prevLength) {
      setShouldAutoScroll(true)
    }
    
    // 현재 길이를 저장
    prevMessageLengthRef.current = currentLength
    
    // 항상 하단 고정 (일반 채팅 UX)
    scrollToBottom()
  }, [messages.length])

  // messages는 이미 chatHistory 기반으로 변환되어 전달됨
  const normalizedList: ChatMessage[] = messages

  const orderedList: ChatMessage[] = normalizedList
    .slice()
    .sort((a: any, b: any) => {
      const at = a.timestamp instanceof Date ? a.timestamp.getTime() : new Date(a.timestamp).getTime()
      const bt = b.timestamp instanceof Date ? b.timestamp.getTime() : new Date(b.timestamp).getTime()
      return at - bt
    })

  const lastMessage = orderedList[orderedList.length - 1]

  // 상단 스냅 로직 제거: 기본 하단 고정 UX만 유지

  // 스크롤 이벤트 리스너 등록
  useEffect(() => {
    const container = scrollAreaRef.current
    if (container) {
      container.addEventListener('scroll', handleScroll)
      return () => container.removeEventListener('scroll', handleScroll)
    }
  }, [])

  // 앵커 기반 하단 고정 - 구조와 무관하게 보장
  useEffect(() => {
    if (!shouldAutoScroll) return
    const el = messagesEndRef.current
    if (!el) return
    el.scrollIntoView({ block: 'end', behavior: 'smooth' })
  }, [messages.length, isLoading])

  // 로딩 시작(= assistant 응답 중) 시 하단 고정 재개
  useEffect(() => {
    if (isLoading) setShouldAutoScroll(true)
  }, [isLoading])

  // 로딩 상태 디버깅
  useEffect(() => {
    if (isLoading) {
      console.log('🔄 로딩 인디케이터 표시:', { isLoading, messagesLength: messages.length, orderedListLength: orderedList.length })
    }
  }, [isLoading, messages.length, orderedList.length])

  return (
    <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
      <div ref={scrollAreaRef} className="flex-1 p-4 lg:p-6 overflow-y-auto scroll-smooth">
        <div className="max-w-4xl mx-auto">
          <div className={`space-y-4 lg:space-y-6`}>
            {orderedList.map((msg: ChatMessage, index: number) => {
              const totalMessages = messages.length // messages 길이를 사용 (게스트/로그인 통합)
              return (
                <div key={msg.id} data-msg-id={String(msg.id)} data-role={msg.role}>
                  <MessageItem
                    msg={msg}
                    index={index}
                    totalMessages={totalMessages}
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
                    onSaveMealToCalendar={onSaveMealToCalendar}
                    onPlaceMarkerClick={onPlaceMarkerClick}
                  />
                </div>
              )
            })}
            {/* 채팅 제한 알림 */}
            {chatHistory.length >= 20 && (
              <div className="flex items-start gap-3 lg:gap-4 animate-in slide-in-from-bottom-2 fade-in duration-300">
                <div className="flex-shrink-0 w-8 h-8 lg:w-10 lg:h-10 rounded-full bg-gradient-to-r from-orange-500 to-red-500 text-white flex items-center justify-center shadow-md">
                  <span className="text-sm lg:text-lg">⚠️</span>
                </div>
                <div className="flex-1 max-w-3xl">
                  <div className="inline-block p-4 lg:p-5 rounded-2xl shadow-lg bg-orange-50 border border-orange-200 text-orange-800">
                    <div className="flex items-center gap-2 lg:gap-3">
                      <span className="text-sm lg:text-base font-medium">
                        {isLoggedIn ? '채팅 제한에 도달했습니다!' : '더 많은 채팅을 이용하려면 로그인하세요!'}
                      </span>
                    </div>
                    <div className="mt-2 text-xs lg:text-sm text-orange-600">
                      {isLoggedIn ? '새 채팅을 시작하여 계속 대화하세요.' : '로그인하면 무제한으로 채팅할 수 있습니다.'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 로딩 안내(버블이 아닌 인라인): 순서에 영향 주지 않고 상태만 전달 */}
            {isLoading && lastMessage?.role === 'user' && (
              <div className="py-2 flex items-center justify-center text-muted-foreground">
                <CircularProgress size={14} sx={{ mr: 1 }} />
                <span className="text-xs">
                  {loadingStep === 'thinking' && '키토 코치가 생각하고 있어요...'}
                  {loadingStep === 'analyzing' && '사용자 정보를 분석하고 있어요...'}
                  {loadingStep === 'generating' && '맞춤형 답변을 생성하고 있어요...'}
                  {loadingStep === 'finalizing' && '답변을 마무리하고 있어요...'}
                </span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>
    </div>
  )
}
