import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Card } from '@/components/ui/card'
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

export function ChatPage() {
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const { messages, addMessage } = useChatStore()
  const { profile } = useProfileStore()
  const sendMessage = useSendMessage()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!message.trim() || isLoading) return

    const userMessage: Message = {
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
    } catch (error) {
      console.error('메시지 전송 실패:', error)
      const errorMessage: Message = {
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

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* 헤더 */}
      <div className="border-b border-border pb-4 mb-6">
        <h1 className="text-2xl font-bold text-gradient">키토 코치와 대화하기</h1>
        <p className="text-muted-foreground mt-1">
          "아침에 먹을 키토 레시피 추천해줘" 또는 "강남역 근처 키토 식당 찾아줘"라고 말해보세요
        </p>
      </div>

      {/* 메시지 영역 */}
      <ScrollArea className="flex-1 pr-4">
        <div className="space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-8">
              <Bot className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">안녕하세요! 키토 코치입니다 🥑</h3>
              <p className="text-muted-foreground">
                키토 식단에 대해 궁금한 것이 있으시면 언제든 물어보세요!
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className="flex items-start space-x-3">
              {/* 아바타 */}
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                msg.role === 'user' 
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-muted text-muted-foreground'
              }`}>
                {msg.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>

              {/* 메시지 내용 */}
              <div className="flex-1 space-y-2">
                <Card className={`p-3 max-w-2xl ${
                  msg.role === 'user' 
                    ? 'bg-primary text-primary-foreground ml-8' 
                    : 'bg-muted'
                }`}>
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </Card>

                {/* 결과 카드들 */}
                {msg.results && msg.results.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
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
          ))}

          {/* 로딩 표시 */}
          {isLoading && (
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center">
                <Bot className="h-4 w-4" />
              </div>
              <Card className="p-3 bg-muted">
                <div className="flex items-center space-x-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">키토 코치가 생각하고 있어요...</span>
                </div>
              </Card>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* 입력 영역 */}
      <div className="border-t border-border pt-4 mt-4">
        <div className="flex space-x-2">
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="키토 식단에 대해 무엇이든 물어보세요..."
            className="flex-1"
            disabled={isLoading}
          />
          <Button 
            onClick={handleSendMessage}
            disabled={!message.trim() || isLoading}
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        
        {/* 빠른 질문 버튼들 */}
        <div className="flex flex-wrap gap-2 mt-3">
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
              onClick={() => setMessage(quickMessage)}
              disabled={isLoading}
              className="text-xs"
            >
              {quickMessage}
            </Button>
          ))}
        </div>
      </div>
    </div>
  )
}
