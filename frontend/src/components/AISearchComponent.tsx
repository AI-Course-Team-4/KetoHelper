import { useState, useRef, useEffect } from 'react'
import {
  Box,
  TextField,
  IconButton,
  Paper,
  Typography,
  Avatar,
  Chip,
  Button,
  Card,
  CardContent,
  Fade,
  Collapse,
  CircularProgress,
  Divider,
} from '@mui/material'
import {
  Send,
  Mic,
  Psychology,
  Restaurant,
  MenuBook,
  TipsAndUpdates,
  Person,
  AutoAwesome,
  Refresh,
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuthStore } from '@store/authStore'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: Date
  suggestions?: string[]
  relatedContent?: {
    type: 'recipe' | 'restaurant' | 'tip'
    items: any[]
  }
}

interface AISearchComponentProps {
  placeholder?: string
  onResultSelect?: (type: 'recipe' | 'restaurant', item: any) => void
  showSuggestions?: boolean
  compact?: boolean
}

const AISearchComponent = ({ 
  placeholder = "키토 다이어트에 대해 무엇이든 물어보세요! 예: '점심으로 간단한 키토 요리 추천해줘'",
  onResultSelect,
  showSuggestions = true,
  compact = false
}: AISearchComponentProps) => {
  const { user, isAuthenticated } = useAuthStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 초기 인사 메시지
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage: Message = {
        id: 'welcome',
        type: 'ai',
        content: isAuthenticated 
          ? `안녕하세요 ${user?.name || ''}님! 😊 오늘은 어떤 키토 요리나 식당을 찾아드릴까요?`
          : '안녕하세요! 키토 다이어트 AI 어시스턴트입니다. 🥑 어떤 도움이 필요하신가요?',
        timestamp: new Date(),
        suggestions: [
          '점심으로 간단한 키토 요리 추천해줘',
          '근처 키토 친화적인 식당 찾아줘',
          '아보카도를 활용한 레시피 알려줘',
          '키토 다이어트 시작하는 방법',
          '탄수화물 5g 이하 간식 추천'
        ]
      }
      setMessages([welcomeMessage])
    }
  }, [isAuthenticated, user])

  // 메시지가 추가될 때마다 스크롤 하단으로
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // AI 응답 생성 (실제로는 백엔드 API 호출)
  const generateAIResponse = async (userMessage: string): Promise<Message> => {
    // TODO: 실제 AI API 호출로 대체
    await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 1000))

    const lowerMessage = userMessage.toLowerCase()
    let content = ''
    let relatedContent: any = undefined
    let suggestions: string[] = []

    // 키워드 기반 응답 생성 (실제로는 AI가 처리)
    if (lowerMessage.includes('레시피') || lowerMessage.includes('요리') || lowerMessage.includes('식단')) {
      content = `맛있는 키토 레시피를 찾아드렸어요! 🍳\n\n개인 선호도를 고려하여 ${isAuthenticated ? '맞춤형으로' : ''} 추천해드립니다:`
      relatedContent = {
        type: 'recipe' as const,
        items: [
          {
            id: '1',
            title: '아보카도 베이컨 샐러드',
            description: '신선한 아보카도와 바삭한 베이컨의 완벽한 조화',
            cookingTime: 15,
            difficulty: '쉬움',
            nutrition: { carbs: 8, protein: 15, fat: 32 },
            image: 'https://via.placeholder.com/200x150?text=아보카도+샐러드'
          },
          {
            id: '2',
            title: '치킨 크림 스프',
            description: '부드럽고 진한 크림 스프로 포만감 만점',
            cookingTime: 30,
            difficulty: '중간',
            nutrition: { carbs: 6, protein: 28, fat: 30 },
            image: 'https://via.placeholder.com/200x150?text=치킨+스프'
          }
        ]
      }
      suggestions = [
        '이 레시피 재료 구매처 알려줘',
        '비슷한 난이도의 다른 요리 추천',
        '이 요리와 어울리는 반찬 추천'
      ]
    } else if (lowerMessage.includes('식당') || lowerMessage.includes('맛집') || lowerMessage.includes('외식')) {
      content = `키토 친화적인 식당을 찾아드렸어요! 🍽️\n\n현재 위치 기준으로 추천해드립니다:`
      relatedContent = {
        type: 'restaurant' as const,
        items: [
          {
            id: '1',
            name: '그린샐러드 카페',
            cuisine: '샐러드 전문점',
            rating: 4.5,
            distance: '0.3km',
            ketoScore: 95,
            address: '서울시 강남구 테헤란로',
            image: 'https://via.placeholder.com/200x150?text=그린샐러드'
          },
          {
            id: '2',
            name: '스테이크하우스 프리미엄',
            cuisine: '스테이크 전문점',
            rating: 4.8,
            distance: '0.8km',
            ketoScore: 90,
            address: '서울시 강남구 역삼동',
            image: 'https://via.placeholder.com/200x150?text=스테이크하우스'
          }
        ]
      }
      suggestions = [
        '이 식당 메뉴 자세히 보기',
        '예약 가능한 시간 확인',
        '다른 지역 키토 식당 찾기'
      ]
    } else if (lowerMessage.includes('시작') || lowerMessage.includes('방법') || lowerMessage.includes('어떻게')) {
      content = `키토 다이어트 시작 가이드를 준비했어요! 📚\n\n단계별로 안내해드릴게요:\n\n1️⃣ **탄수화물 제한**: 일일 탄수화물 섭취량을 20-50g으로 제한\n2️⃣ **지방 늘리기**: 전체 칼로리의 70-80%를 건강한 지방으로\n3️⃣ **적정 단백질**: 체중 1kg당 1.2-1.7g의 단백질 섭취\n4️⃣ **수분 보충**: 하루 2-3L의 물 섭취\n5️⃣ **전해질 관리**: 나트륨, 칼륨, 마그네슘 보충`
      suggestions = [
        '키토 초보자 식단표 받기',
        '키토 부작용과 대처법',
        '키토 친화적 식재료 목록'
      ]
    } else {
      content = `궁금한 내용에 대해 더 구체적으로 알려주세요! 😊\n\n다음과 같은 질문들에 도움을 드릴 수 있어요:\n• 키토 레시피 추천\n• 키토 친화적 식당 찾기\n• 키토 다이어트 방법\n• 영양 성분 분석\n• 식단 계획 수립`
      suggestions = [
        '오늘 저녁 메뉴 추천해줘',
        '키토 간식 뭐가 좋을까?',
        '키토 다이어트 효과는 언제부터?'
      ]
    }

    return {
      id: Date.now().toString(),
      type: 'ai',
      content,
      timestamp: new Date(),
      suggestions,
      relatedContent
    }
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const aiResponse = await generateAIResponse(userMessage.content)
      setMessages(prev => [...prev, aiResponse])
    } catch (error) {
      console.error('AI 응답 생성 실패:', error)
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'ai',
        content: '죄송해요, 일시적인 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion)
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSendMessage()
    }
  }

  const handleVoiceInput = () => {
    // TODO: 음성 인식 구현
    setIsListening(!isListening)
    if (!isListening) {
      // 음성 인식 시작
      setTimeout(() => setIsListening(false), 3000) // 3초 후 자동 종료
    }
  }

  return (
    <Box sx={{ height: compact ? 400 : 600, display: 'flex', flexDirection: 'column' }}>
      {/* 메시지 영역 */}
      <Box sx={{ 
        flex: 1, 
        overflowY: 'auto', 
        p: 2, 
        backgroundColor: 'grey.50',
        borderRadius: 2,
        mb: 2
      }}>
        <AnimatePresence>
          {messages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Box sx={{ 
                display: 'flex', 
                justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                mb: 2,
                alignItems: 'flex-start'
              }}>
                {message.type === 'ai' && (
                  <Avatar sx={{ 
                    mr: 1, 
                    backgroundColor: 'primary.main',
                    width: 32,
                    height: 32
                  }}>
                    <Psychology fontSize="small" />
                  </Avatar>
                )}
                
                <Box sx={{ maxWidth: '80%' }}>
                  <Paper sx={{ 
                    p: 2, 
                    backgroundColor: message.type === 'user' ? 'primary.main' : 'white',
                    color: message.type === 'user' ? 'white' : 'text.primary',
                    borderRadius: 2,
                    boxShadow: 1
                  }}>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                      {message.content}
                    </Typography>
                    
                    {/* 관련 콘텐츠 표시 */}
                    {message.relatedContent && (
                      <Box sx={{ mt: 2 }}>
                        {message.relatedContent.items.map((item, idx) => (
                          <Card 
                            key={idx} 
                            sx={{ 
                              mb: 1, 
                              cursor: 'pointer',
                              '&:hover': { boxShadow: 3 }
                            }}
                            onClick={() => onResultSelect?.(message.relatedContent!.type, item)}
                          >
                            <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                {message.relatedContent.type === 'recipe' ? (
                                  <MenuBook sx={{ mr: 1, color: 'primary.main' }} />
                                ) : (
                                  <Restaurant sx={{ mr: 1, color: 'secondary.main' }} />
                                )}
                                <Box sx={{ flex: 1 }}>
                                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                                    {item.title || item.name}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {item.description || item.cuisine}
                                  </Typography>
                                  {message.relatedContent.type === 'recipe' && (
                                    <Box sx={{ mt: 0.5 }}>
                                      <Chip label={`${item.cookingTime}분`} size="small" sx={{ mr: 0.5 }} />
                                      <Chip label={item.difficulty} size="small" />
                                    </Box>
                                  )}
                                  {message.relatedContent.type === 'restaurant' && (
                                    <Box sx={{ mt: 0.5 }}>
                                      <Chip label={`⭐ ${item.rating}`} size="small" sx={{ mr: 0.5 }} />
                                      <Chip label={`${item.distance}`} size="small" />
                                    </Box>
                                  )}
                                </Box>
                              </Box>
                            </CardContent>
                          </Card>
                        ))}
                      </Box>
                    )}
                  </Paper>
                  
                  {/* 제안 버튼들 */}
                  {message.suggestions && showSuggestions && (
                    <Fade in timeout={1000}>
                      <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {message.suggestions.map((suggestion, idx) => (
                          <Button
                            key={idx}
                            variant="outlined"
                            size="small"
                            onClick={() => handleSuggestionClick(suggestion)}
                            sx={{ 
                              fontSize: '0.75rem',
                              borderRadius: 3,
                              backgroundColor: 'background.paper',
                              '&:hover': {
                                backgroundColor: 'primary.light',
                                color: 'white'
                              }
                            }}
                          >
                            {suggestion}
                          </Button>
                        ))}
                      </Box>
                    </Fade>
                  )}
                  
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    {message.timestamp.toLocaleTimeString('ko-KR', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </Typography>
                </Box>

                {message.type === 'user' && (
                  <Avatar sx={{ 
                    ml: 1, 
                    backgroundColor: 'secondary.main',
                    width: 32,
                    height: 32
                  }}>
                    <Person fontSize="small" />
                  </Avatar>
                )}
              </Box>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {/* 로딩 표시 */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
              <Avatar sx={{ 
                mr: 1, 
                backgroundColor: 'primary.main',
                width: 32,
                height: 32
              }}>
                <Psychology fontSize="small" />
              </Avatar>
              <Paper sx={{ p: 2, backgroundColor: 'white' }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CircularProgress size={16} sx={{ mr: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    AI가 답변을 생성하고 있어요...
                  </Typography>
                </Box>
              </Paper>
            </Box>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </Box>
      
      {/* 입력 영역 */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
        <TextField
          ref={inputRef}
          fullWidth
          multiline
          maxRows={3}
          placeholder={placeholder}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          sx={{
            '& .MuiOutlinedInput-root': {
              backgroundColor: 'white',
              borderRadius: 3,
            }
          }}
        />
        
        <IconButton
          onClick={handleVoiceInput}
          color={isListening ? 'secondary' : 'default'}
          disabled={isLoading}
          sx={{ 
            backgroundColor: isListening ? 'secondary.light' : 'background.paper',
            '&:hover': {
              backgroundColor: isListening ? 'secondary.main' : 'action.hover',
            }
          }}
        >
          <Mic />
        </IconButton>
        
        <IconButton
          onClick={handleSendMessage}
          disabled={!inputValue.trim() || isLoading}
          color="primary"
          sx={{ 
            backgroundColor: 'primary.main',
            color: 'white',
            '&:hover': {
              backgroundColor: 'primary.dark',
            },
            '&.Mui-disabled': {
              backgroundColor: 'grey.300',
              color: 'grey.500'
            }
          }}
        >
          <Send />
        </IconButton>
      </Box>
    </Box>
  )
}

export default AISearchComponent

