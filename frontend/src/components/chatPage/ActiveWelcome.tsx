import { Send } from '@mui/icons-material'
import { CircularProgress } from '@mui/material'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { QuickActions } from './QuickActions'

interface ActiveWelcomeProps {
  message: string
  isLoading: boolean
  onMessageChange: (value: string) => void
  onSendMessage: () => void
  onKeyDown: (e: React.KeyboardEvent) => void
  onQuickMessage: (message: string) => void
}

export function ActiveWelcome({
  message,
  isLoading,
  onMessageChange,
  onSendMessage,
  onKeyDown,
  onQuickMessage
}: ActiveWelcomeProps) {
  return (
    <div className="flex-1 flex flex-col">
      {/* 웰컴 메시지 영역 */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-8">
        <div className="text-center">
          <div className="w-16 h-16 lg:w-20 lg:h-20 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center mx-auto mb-4 lg:mb-6 shadow-lg">
            <span className="text-2xl lg:text-3xl">🥑</span>
          </div>
          <h3 className="text-xl lg:text-2xl font-bold text-green-600 mb-2">
            안녕하세요, 키토 코치입니다!
          </h3>
          <p className="text-sm lg:text-base text-gray-600">
            무엇을 도와드릴까요?
          </p>
        </div>
      </div>

      {/* 채팅 입력 영역 */}
      <div className="p-4 lg:p-6 border-t border-gray-100">
        <div className="max-w-4xl mx-auto space-y-3 lg:space-y-4">
          <div className="flex gap-2 lg:gap-3">
            <div className="flex-1 relative">
              <Input
                value={message}
                onChange={(e) => onMessageChange(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="키토 식단에 대해 무엇이든 물어보세요..."
                className="h-12 lg:h-14 text-base lg:text-lg pl-4 lg:pl-6 pr-12 lg:pr-16 bg-white border-2 border-gray-200 focus:border-green-400 rounded-2xl shadow-lg focus:shadow-xl transition-all duration-300"
                disabled={isLoading}
              />
              {isLoading && (
                <div className="absolute right-3 lg:right-4 top-1/2 -translate-y-1/2">
                  <CircularProgress size={20} sx={{ color: 'text.secondary' }} />
                </div>
              )}
            </div>
            <Button
              onClick={onSendMessage}
              disabled={!message.trim() || isLoading}
              className="h-12 lg:h-14 px-4 lg:px-6 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold rounded-2xl hover:shadow-xl transition-all duration-300"
            >
              <Send className="h-5 w-5 lg:h-6 lg:w-6" />
            </Button>
          </div>

          {/* 빠른 질문 버튼들 */}
          <QuickActions
            onQuickMessage={onQuickMessage}
            isLoading={isLoading}
            isWelcomeScreen={true}
          />

          {/* 면책 조항 */}
          <div className="text-[10px] lg:text-[11px] text-muted-foreground text-center">
            키토 코치는 실수 할 수 있습니다. 중요한 정보는 재차 확인하세요.
          </div>
        </div>
      </div>
    </div>
  )
}
