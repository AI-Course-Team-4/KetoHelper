import { Button } from '@/components/ui/button'

interface QuickActionsProps {
  onQuickMessage: (message: string) => void
  isLoading: boolean
  isWelcomeScreen?: boolean
  isChatLimitReached?: boolean
  disabled?: boolean
}

export function QuickActions({ onQuickMessage, isLoading, isWelcomeScreen = false, isChatLimitReached = false, disabled = false }: QuickActionsProps) {
  const quickMessages = [
    "키토 다이어트 방법 알려줘",
    "7일 키토 식단표 만들어줘",
    "강남역 근처 키토 식당 찾아줘",
    "아침 키토 레시피 추천해줘",
  ]

  const buttonClass = isWelcomeScreen 
    ? "text-sm lg:text-base px-4 lg:px-6 py-2 lg:py-3 rounded-xl lg:rounded-2xl border-2 border-green-200 hover:bg-green-50 hover:border-green-300 hover:shadow-lg transition-all duration-300 font-medium text-green-700"
    : "text-xs lg:text-sm px-3 lg:px-4 py-1 lg:py-2 rounded-lg lg:rounded-xl border-2 border-green-200 hover:bg-green-50 hover:border-green-300 hover:shadow-md transition-all duration-300 font-medium text-green-700"

  return (
    <div className={`flex flex-wrap gap-2 lg:gap-3 ${isWelcomeScreen ? 'justify-center' : 'justify-center'}`}>
      {quickMessages.map((quickMessage) => (
        <Button
          key={quickMessage}
          variant="outline"
          size="sm"
          onClick={() => onQuickMessage(quickMessage)}
          disabled={disabled || isLoading || isChatLimitReached}
          className={buttonClass}
        >
          {quickMessage}
        </Button>
      ))}
    </div>
  )
}
