import { Box, Typography, Button, Grid, Card, CardContent, Container, Paper, Chip, Avatar } from '@mui/material'
import { Link } from 'react-router-dom'
import { Restaurant, MenuBook, Settings, TrendingUp, Psychology, AutoAwesome, Lightbulb } from '@mui/icons-material'
import { motion } from 'framer-motion'
import { useAuthStore } from '@store/authStore'
import AISearchComponent from '@components/AISearchComponent'

const HomePage = () => {
  const { isAuthenticated, user } = useAuthStore()
  const displayName = user?.name || user?.id || ''

  const quickPrompts = [
    {
      text: '점심으로 간단한 키토 요리 추천해줘',
      icon: <MenuBook />,
      category: '레시피'
    },
    {
      text: '근처 키토 친화적인 식당 찾아줘',
      icon: <Restaurant />,
      category: '식당'
    },
    {
      text: '키토 다이어트 시작하는 방법 알려줘',
      icon: <Lightbulb />,
      category: '가이드'
    },
    {
      text: '아보카도를 활용한 레시피 추천',
      icon: <AutoAwesome />,
      category: '재료별'
    }
  ]

  const handleResultSelect = (type: 'recipe' | 'restaurant', item: any) => {
    if (type === 'recipe') {
      // 레시피 상세 페이지로 이동 또는 모달 열기
      console.log('Recipe selected:', item)
    } else {
      // 식당 상세 페이지로 이동
      console.log('Restaurant selected:', item)
    }
  }

  return (
    <Box>
      {/* AI 히어로 섹션 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Box
          sx={{
            background: 'linear-gradient(135deg, #2E7D32 0%, #4CAF50 20%, #FF8F00 100%)',
            color: 'white',
            py: { xs: 6, md: 8 },
            px: 3,
            borderRadius: 3,
            mb: 4,
            position: 'relative',
            overflow: 'hidden',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.1"%3E%3Ccircle cx="30" cy="30" r="4"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
            }
          }}
        >
          <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
            <Grid container spacing={4} alignItems="center">
              <Grid item xs={12} md={6}>
                <Box sx={{ textAlign: { xs: 'center', md: 'left' } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, justifyContent: { xs: 'center', md: 'flex-start' } }}>
                    <Avatar sx={{ 
                      backgroundColor: 'rgba(255,255,255,0.2)', 
                      mr: 2, 
                      width: 60, 
                      height: 60,
                      backdropFilter: 'blur(10px)'
                    }}>
                      <Psychology sx={{ fontSize: 32 }} />
                    </Avatar>
                    <Box>
                      <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                        KetoHelper AI
                      </Typography>
                      <Chip 
                        label="🤖 AI 어시스턴트" 
                        sx={{ 
                          backgroundColor: 'rgba(255,255,255,0.2)',
                          color: 'white',
                          backdropFilter: 'blur(10px)'
                        }} 
                      />
                    </Box>
                  </Box>
                  <Typography variant="h5" sx={{ mb: 3, opacity: 0.9, fontWeight: 500 }}>
                    자연어로 질문하고 AI가 추천하는
                    <br />
                    <strong>스마트한 키토 라이프</strong>
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 4, fontSize: '1.1rem', opacity: 0.8, lineHeight: 1.6 }}>
                    복잡한 메뉴 탐색은 그만! 이제 "점심으로 간단한 키토 요리 추천해줘"처럼
                    <br />
                    자연스럽게 대화하면서 맞춤형 추천을 받아보세요.
                  </Typography>
                  
                  {!isAuthenticated ? (
                    <Button
                      variant="contained"
                      size="large"
                      component={Link}
                      to="/login"
                      sx={{
                        backgroundColor: 'white',
                        color: 'primary.main',
                        px: 4,
                        py: 1.5,
                        fontSize: '1.1rem',
                        fontWeight: 600,
                        borderRadius: 3,
                        boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                        '&:hover': {
                          backgroundColor: 'grey.100',
                          transform: 'translateY(-2px)',
                          boxShadow: '0 12px 40px rgba(0,0,0,0.15)',
                        },
                      }}
                    >
                      ✨ AI와 대화 시작하기
                    </Button>
                  ) : (
                    <Typography variant="h6" sx={{ 
                      backgroundColor: 'rgba(255,255,255,0.2)',
                      px: 3,
                      py: 1,
                      borderRadius: 3,
                      display: 'inline-block',
                      backdropFilter: 'blur(10px)'
                    }}>
                      👋 안녕하세요, {displayName}님!
                    </Typography>
                  )}
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ display: { xs: 'none', md: 'block' } }}>
                  <Paper sx={{ 
                    p: 3, 
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: 3
                  }}>
                    <Typography variant="h6" sx={{ mb: 2, color: 'white' }}>
                      💬 자연어 대화 예시
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {quickPrompts.map((prompt, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 + 0.5 }}
                        >
                          <Box sx={{
                            display: 'flex',
                            alignItems: 'center',
                            p: 2,
                            backgroundColor: 'rgba(255,255,255,0.1)',
                            borderRadius: 2,
                            color: 'white'
                          }}>
                            {prompt.icon}
                            <Typography variant="body2" sx={{ ml: 1, flex: 1 }}>
                              "{prompt.text}"
                            </Typography>
                            <Chip 
                              label={prompt.category} 
                              size="small" 
                              sx={{ 
                                backgroundColor: 'rgba(255,255,255,0.2)',
                                color: 'white',
                                fontSize: '0.7rem'
                              }} 
                            />
                          </Box>
                        </motion.div>
                      ))}
                    </Box>
                  </Paper>
                </Box>
              </Grid>
            </Grid>
          </Container>
        </Box>
      </motion.div>

      {/* AI 어시스턴트 메인 섹션 */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            {/* AI 검색 컴포넌트 */}
            <Grid item xs={12} lg={8}>
              <Card sx={{ 
                borderRadius: 4, 
                boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                border: '1px solid',
                borderColor: 'primary.light',
                overflow: 'hidden'
              }}>
                <Box sx={{ 
                  background: 'linear-gradient(90deg, #2E7D32 0%, #4CAF50 100%)',
                  color: 'white',
                  p: 2,
                  display: 'flex',
                  alignItems: 'center'
                }}>
                  <Psychology sx={{ mr: 1 }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    AI 키토 어시스턴트
                  </Typography>
                  <Chip 
                    label="LIVE" 
                    size="small" 
                    sx={{ 
                      ml: 'auto',
                      backgroundColor: 'error.main',
                      color: 'white',
                      animation: 'pulse 2s infinite'
                    }} 
                  />
                </Box>
                <CardContent sx={{ p: 0 }}>
                  <AISearchComponent 
                    onResultSelect={handleResultSelect}
                    showSuggestions={true}
                  />
                </CardContent>
              </Card>
            </Grid>

            {/* 사이드 정보 패널 */}
            <Grid item xs={12} lg={4}>
              {isAuthenticated && user && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: 0.5 }}
                >
                  <Card sx={{ mb: 3, borderRadius: 3 }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                        📊 나의 키토 현황
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'primary.light', borderRadius: 2 }}>
                            <TrendingUp sx={{ fontSize: 24, color: 'white', mb: 1 }} />
                            <Typography variant="body2" sx={{ color: 'white', fontWeight: 600 }}>
                              진행률
                            </Typography>
                            <Typography variant="h6" sx={{ color: 'white', fontWeight: 700 }}>
                              75%
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'secondary.light', borderRadius: 2 }}>
                            <MenuBook sx={{ fontSize: 24, color: 'white', mb: 1 }} />
                            <Typography variant="body2" sx={{ color: 'white', fontWeight: 600 }}>
                              레시피
                            </Typography>
                            <Typography variant="h6" sx={{ color: 'white', fontWeight: 700 }}>
                              12개
                            </Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </motion.div>
              )}

              {/* 빠른 질문 제안 */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.7 }}
              >
                <Card sx={{ borderRadius: 3 }}>
                  <CardContent>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                      💡 인기 질문들
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {quickPrompts.map((prompt, index) => (
                        <Button
                          key={index}
                          variant="outlined"
                          size="small"
                          startIcon={prompt.icon}
                          sx={{
                            justifyContent: 'flex-start',
                            textAlign: 'left',
                            py: 1.5,
                            px: 2,
                            borderRadius: 2,
                            '&:hover': {
                              backgroundColor: 'primary.light',
                              color: 'white',
                              borderColor: 'primary.main'
                            }
                          }}
                          onClick={() => {
                            // AI 검색창에 질문 입력 (실제 구현 시 props로 전달)
                            console.log('Quick prompt clicked:', prompt.text)
                          }}
                        >
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="body2" sx={{ fontSize: '0.85rem' }}>
                              {prompt.text}
                            </Typography>
                            <Chip 
                              label={prompt.category} 
                              size="small" 
                              sx={{ mt: 0.5, height: 20, fontSize: '0.7rem' }} 
                            />
                          </Box>
                        </Button>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </motion.div>

              {/* 키토 팁 카드 */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.9 }}
              >
                <Card sx={{ mt: 3, borderRadius: 3, background: 'linear-gradient(135deg, #E8F5E8 0%, #F1F8E9 100%)' }}>
                  <CardContent>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
                      🌟 오늘의 키토 팁
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 2, lineHeight: 1.6 }}>
                      물을 충분히 드세요! 키토 다이어트 중에는 탈수가 쉽게 일어날 수 있어요. 
                      하루 2-3L의 물을 마시는 것을 권장합니다.
                    </Typography>
                    <Button 
                      size="small" 
                      variant="contained" 
                      sx={{ fontSize: '0.75rem' }}
                    >
                      더 많은 팁 보기
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          </Grid>
        </Container>
      </motion.div>

      {/* AI 기능 소개 섹션 */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 1.1 }}
      >
        <Container maxWidth="lg" sx={{ mt: 8, mb: 4 }}>
          <Card sx={{ 
            borderRadius: 4, 
            overflow: 'hidden',
            background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)'
          }}>
            <CardContent sx={{ p: 6 }}>
              <Box sx={{ textAlign: 'center', mb: 4 }}>
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
                  🤖 AI가 만든 스마트한 키토 경험
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ fontSize: '1.1rem' }}>
                  복잡한 영양 계산과 메뉴 선택을 AI가 대신 처리해드립니다
                </Typography>
              </Box>
              
              <Grid container spacing={4}>
                <Grid item xs={12} md={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Avatar sx={{ 
                      width: 80, 
                      height: 80, 
                      mx: 'auto', 
                      mb: 2,
                      backgroundColor: 'primary.main',
                      fontSize: '2rem'
                    }}>
                      🧠
                    </Avatar>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                      자연어 이해
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      "점심으로 간단한 요리"처럼 일상 언어로 질문하면 
                      AI가 정확히 이해하고 맞춤 추천을 제공합니다.
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Avatar sx={{ 
                      width: 80, 
                      height: 80, 
                      mx: 'auto', 
                      mb: 2,
                      backgroundColor: 'secondary.main',
                      fontSize: '2rem'
                    }}>
                      🎯
                    </Avatar>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                      개인화 추천
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      사용자의 선호도, 알레르기, 목표를 학습하여 
                      점점 더 정확한 맞춤형 추천을 제공합니다.
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Avatar sx={{ 
                      width: 80, 
                      height: 80, 
                      mx: 'auto', 
                      mb: 2,
                      backgroundColor: 'success.main',
                      fontSize: '2rem'
                    }}>
                      ⚡
                    </Avatar>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                      실시간 응답
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      영양 성분 계산부터 식당 추천까지 
                      모든 정보를 즉시 제공합니다.
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              <Box sx={{ textAlign: 'center', mt: 4 }}>
                <Button 
                  variant="contained" 
                  size="large"
                  sx={{ 
                    borderRadius: 3,
                    px: 4,
                    py: 1.5,
                    fontSize: '1rem',
                    fontWeight: 600
                  }}
                >
                  💬 지금 AI와 대화해보기
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Container>
      </motion.div>
    </Box>
  )
}

export default HomePage
