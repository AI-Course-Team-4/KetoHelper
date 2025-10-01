import { useState, useEffect, useRef } from 'react'

interface UseTypingAnimationProps {
  text: string
  speed?: number
  isEnabled?: boolean
  onTypingUpdate?: () => void
  messageId?: string
  isNewMessage?: boolean // 새 메시지인지 여부
}

export function useTypingAnimation({ 
  text, 
  speed = 30, 
  isEnabled = true,
  onTypingUpdate,
  messageId,
  isNewMessage = false
}: UseTypingAnimationProps) {
  const [displayedText, setDisplayedText] = useState(text || '')
  const [isTyping, setIsTyping] = useState(false)
  const lastMessageIdRef = useRef<string | undefined>()
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    console.log('🔍 useTypingAnimation:', { 
      isEnabled, 
      text: text?.substring(0, 50) + '...', 
      messageId, 
      lastMessageId: lastMessageIdRef.current,
      isNewMessage
    })

    // 텍스트가 없으면 빈 문자열로 설정
    if (!text) {
      setDisplayedText('')
      setIsTyping(false)
      return
    }

    // 타이핑 애니메이션이 비활성화되었거나 새 메시지가 아니면 즉시 표시
    if (!isEnabled || !isNewMessage) {
      console.log('📝 즉시 표시:', { messageId, textLength: text.length, isEnabled, isNewMessage })
      setDisplayedText(text)
      setIsTyping(false)
      return
    }

    // 메시지 ID가 변경되었을 때만 타이핑 애니메이션 시작
    if (lastMessageIdRef.current !== messageId) {
      console.log('🚀 타이핑 애니메이션 시작:', { messageId, textLength: text.length })
      lastMessageIdRef.current = messageId
      
      // 기존 인터벌 정리
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }

      // 즉시 빈 텍스트로 시작
      setDisplayedText('')
      setIsTyping(true)

      let currentIndex = 0
      intervalRef.current = setInterval(() => {
        if (currentIndex < text.length) {
          setDisplayedText(text.slice(0, currentIndex + 1))
          currentIndex++
          // 타이핑 중에도 스크롤 유지를 위해 콜백 호출
          onTypingUpdate?.()
        } else {
          setIsTyping(false)
          if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
          }
        }
      }, speed)
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [text, speed, isEnabled, onTypingUpdate, messageId, isNewMessage])

  return { displayedText, isTyping }
}
