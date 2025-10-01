import { Button } from '@/components/ui/button'

interface EmptyWelcomeProps {
  onCreateNewChat: () => void
}

export function EmptyWelcome({ onCreateNewChat }: EmptyWelcomeProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 lg:p-8 text-center">
      {/* 아보카도 아이콘과 인사말 */}
      <div className="mb-8 lg:mb-12">
        <div className="w-20 h-20 lg:w-24 lg:h-24 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center mx-auto mb-4 lg:mb-6 shadow-lg">
          <span className="text-3xl lg:text-4xl">🥑</span>
        </div>
        <h2 className="text-2xl lg:text-3xl font-bold text-green-600 mb-2 lg:mb-3">
          안녕하세요, 키토 코치입니다!
        </h2>
        <p className="text-sm lg:text-base text-gray-600 mb-2">
          건강한 키토 식단을 위한 모든 것을 도와드릴게요.
        </p>
        <p className="text-sm lg:text-base text-green-600 font-medium">
          레시피 추천부터 식당 찾기까지 무엇이든 물어보세요!
        </p>
      </div>

      {/* 새 채팅 시작 버튼 */}
      <div className="mb-8 lg:mb-10">
        <Button
          onClick={onCreateNewChat}
          className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold rounded-full px-8 py-4 text-lg shadow-lg hover:shadow-xl transition-all duration-300"
        >
          새 채팅 시작
        </Button>
        <p className="text-xs lg:text-sm text-gray-500 mt-3">
          왼쪽 사이드바의 새 채팅 버튼으로도 시작할 수 있어요.
        </p>
      </div>

      {/* 면책 조항 */}
      <div className="text-[10px] lg:text-[11px] text-muted-foreground text-center">
        키토 코치는 실수 할 수 있습니다. 중요한 정보는 재차 확인하세요.
      </div>
    </div>
  )
}
