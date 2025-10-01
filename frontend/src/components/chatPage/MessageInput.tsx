import { Send } from '@mui/icons-material'
import { CircularProgress } from '@mui/material'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { QuickActions } from './QuickActions'

interface MessageInputProps {
  message: string
  isLoading: boolean
  isChatLimitReached: boolean
  onMessageChange: (value: string) => void
  onSendMessage: () => void
  onKeyDown: (e: React.KeyboardEvent) => void
  onQuickMessage: (message: string) => void
}

export function MessageInput({
  message,
  isLoading,
  isChatLimitReached,
  onMessageChange,
  onSendMessage,
  onKeyDown,
  onQuickMessage
}: MessageInputProps) {
  return (
    <div className="flex-shrink-0 border-t-2 border-gray-100 bg-white/90 backdrop-blur-sm p-4 lg:p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex gap-3 lg:gap-4">
          <div className="flex-1 relative">
            <Input
              value={message}
              onChange={(e) => onMessageChange(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={isChatLimitReached ? "채팅 제한에 도달했습니다. 새 채팅을 시작하세요." : "키토 식단에 대해 무엇이든 물어보세요..."}
              className="h-12 lg:h-14 pl-4 lg:pl-6 pr-12 lg:pr-14 bg-white border-2 border-gray-200 focus:border-green-400 rounded-2xl shadow-lg focus:shadow-xl transition-all duration-300"
              disabled={isLoading || isChatLimitReached}
            />
            {isLoading && (
              <div className="absolute right-2 lg:right-3 top-1/2 -translate-y-1/2">
                <CircularProgress size={16} sx={{ color: 'text.secondary' }} />
              </div>
            )}
          </div>
          <Button
            onClick={onSendMessage}
            disabled={!message.trim() || isLoading || isChatLimitReached}
            className="h-12 lg:h-14 px-4 lg:px-6 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300"
          >
            <Send className="h-4 w-4 lg:h-5 lg:w-5" />
          </Button>
        </div>
        <div className="mt-2 lg:mt-2 text-[10px] lg:text-[11px] text-muted-foreground text-center">키토 코치는 실수 할 수 있습니다. 중요한 정보는 재차 확인하세요.</div>
        {/* 빠른 질문 버튼들 */}
        <div className="mt-3 lg:mt-3">
          <QuickActions
            onQuickMessage={onQuickMessage}
            isLoading={isLoading}
            isWelcomeScreen={false}
            isChatLimitReached={isChatLimitReached}
          />
        </div>
      </div>
    </div>
  )
}
