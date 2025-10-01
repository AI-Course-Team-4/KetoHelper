import { Message, Delete, Add } from '@mui/icons-material'
import { Button } from '@/components/ui/button'
import { ChatThread } from '@/hooks/useApi'

interface ThreadSidebarProps {
  chatThreads: ChatThread[]
  currentThreadId: string | null
  isLoading: boolean
  isLoadingThread: boolean
  onCreateNewChat: () => void
  onSelectThread: (threadId: string) => void
  onDeleteThread: (threadId: string) => void
}

export function ThreadSidebar({
  chatThreads,
  currentThreadId,
  isLoading,
  isLoadingThread,
  onCreateNewChat,
  onSelectThread,
  onDeleteThread
}: ThreadSidebarProps) {
  return (
    <div className="hidden lg:block w-80 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl flex flex-col">
      {/* 사이드바 헤더 */}
      <div className="p-6 border-b border-gray-100">
        <Button
          onClick={onCreateNewChat}
          disabled={isLoading}
          className={`w-full justify-center gap-3 h-14 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-300 rounded-xl ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          variant="default"
        >
          <Add sx={{ fontSize: 20 }} />
          새 채팅 시작
        </Button>

        {/* 여백 추가 */}
        <div className="h-4"></div>

        {/* 채팅 히스토리 */}
        <div className="max-h-[60vh] overflow-y-auto">
          <div className="space-y-3">
            {chatThreads.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mx-auto mb-4">
                  <Message sx={{ fontSize: 32 }} />
                </div>
                <p className="text-sm font-medium mb-1">아직 채팅이 없습니다</p>
                <p className="text-xs opacity-70">새 채팅을 시작해보세요!</p>
              </div>
            )}

            {chatThreads.map((thread: ChatThread) => (
              <div
                key={thread.id}
                className={`group relative p-4 rounded-xl transition-all duration-300 ${currentThreadId === thread.id
                  ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg border border-green-300'
                  : 'bg-gray-50 hover:bg-green-50 hover:shadow-md border border-gray-200 hover:border-green-200'
                  } ${isLoading || isLoadingThread ? 'cursor-not-allowed opacity-75' : 'cursor-pointer'}`}
                onClick={() => {
                  if (!isLoading && !isLoadingThread) {
                    onSelectThread(thread.id)
                  }
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium truncate mb-1">
                      {thread.title}
                    </h4>
                    <p className={`text-xs ${currentThreadId === thread.id ? 'text-white/70' : 'text-muted-foreground'
                      }`}>
                      {new Date(thread.last_message_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={isLoading || isLoadingThread}
                    className={`opacity-0 group-hover:opacity-100 h-8 w-8 p-0 transition-all duration-200 ${currentThreadId === thread.id 
                      ? 'text-red-200 bg-red-500/20 border border-red-300/50 hover:bg-red-500/80 hover:text-white hover:border-red-400 hover:shadow-lg' 
                      : 'hover:bg-red-50 hover:text-red-600 border border-transparent hover:border-red-200 hover:shadow-md'
                      } ${isLoading || isLoadingThread ? 'opacity-50 cursor-not-allowed' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation()
                      if (!isLoading && !isLoadingThread) {
                        onDeleteThread(thread.id)
                      }
                    }}
                  >
                    <Delete sx={{ fontSize: 14 }} />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
