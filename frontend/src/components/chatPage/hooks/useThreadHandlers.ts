import { useCallback } from 'react'
import { useCreateNewThread, useDeleteThread } from '@/hooks/useApi'
import { useAuthStore } from '@/store/authStore'
import { useQueryClient } from '@tanstack/react-query'

interface UseThreadHandlersProps {
  currentThreadId: string | null
  setCurrentThreadId: (threadId: string | null) => void
  setMessage: (message: string) => void
  setIsLoadingThread: (loading: boolean) => void
  refetchThreads: () => void
}

export function useThreadHandlers({
  currentThreadId,
  setCurrentThreadId,
  setMessage,
  setIsLoadingThread,
  refetchThreads
}: UseThreadHandlersProps) {
  const { user, ensureGuestId } = useAuthStore()
  const createNewThread = useCreateNewThread()
  const deleteThread = useDeleteThread()
  const queryClient = useQueryClient()

  // 새 채팅 세션 생성
  const handleCreateNewChat = useCallback(async () => {
    try {
      if (user?.id) {
        // 로그인 사용자: 실제 스레드를 생성하여 사이드바에 표시되도록 함
        const newThread = await createNewThread.mutateAsync({
          userId: user.id,
          guestId: undefined
        })
        
        setCurrentThreadId(newThread.id)
        setMessage('')
        
        refetchThreads()
        
        console.log('🆕 로그인 사용자 새 채팅 스레드 생성 및 선택:', newThread.id)
      } else {
        // 게스트 사용자: 스레드 생성 없이 바로 채팅 시작 가능하도록 설정
        setCurrentThreadId(null) // 게스트는 currentThreadId를 null로 유지
        setMessage('')
        
        console.log('🆕 게스트 사용자 새 채팅 시작 (스레드 없음)')
      }
    } catch (error) {
      console.error('❌ 새 채팅 시작 실패:', error)
      setCurrentThreadId(null)
      setMessage('')
    }
  }, [createNewThread, user, ensureGuestId, setCurrentThreadId, setMessage])

  // 스레드 선택
  const handleSelectThread = useCallback((threadId: string) => {
    if (currentThreadId === threadId) {
      console.log('🔄 같은 스레드 재선택 - 아무 작업 없음:', threadId)
      return
    }
    
    setIsLoadingThread(true)
    setCurrentThreadId(threadId)
    setMessage('')
    console.log('🔄 스레드 전환:', threadId)
  }, [currentThreadId, setIsLoadingThread, setCurrentThreadId, setMessage])

  // 스레드 삭제
  const handleDeleteThread = useCallback(async (threadId: string) => {
    const confirmDelete = window.confirm(
      '🗑️ 채팅 삭제\n\n정말로 이 대화를 삭제하시겠습니까?\n삭제된 대화는 복구할 수 없습니다.'
    )
    
    if (!confirmDelete) {
      return
    }

    try {
      console.log('🗑️ 스레드 삭제 시작:', { threadId, currentThreadId })
      await deleteThread.mutateAsync(threadId)
      
      if (currentThreadId === threadId) {
        console.log('🗑️ 현재 스레드 삭제 - currentThreadId를 null로 설정')
        setCurrentThreadId(null)
        setMessage('')
        setIsLoadingThread(false) // 로딩 상태 해제
        
        // React Query 캐시에서 해당 스레드의 채팅 히스토리 제거
        queryClient.removeQueries({ queryKey: ['chat-history', threadId, 20] })
        console.log('🗑️ React Query 캐시에서 채팅 히스토리 제거:', threadId)
        
        console.log('🗑️ 스레드 삭제 후 상태:', { currentThreadId: null })
      } else {
        console.log('🗑️ 다른 스레드 삭제 - currentThreadId 유지:', currentThreadId)
      }
      
      // 스레드 목록 새로고침
      refetchThreads()
      
      console.log('🗑️ 스레드 삭제 완료:', threadId)
    } catch (error) {
      console.error('❌ 스레드 삭제 실패:', error)
      alert('⚠️ 채팅 삭제 실패\n\n스레드 삭제에 실패했습니다.\n잠시 후 다시 시도해주세요.')
    }
  }, [deleteThread, currentThreadId, setCurrentThreadId, setMessage])

  return {
    handleCreateNewChat,
    handleSelectThread,
    handleDeleteThread
  }
}
