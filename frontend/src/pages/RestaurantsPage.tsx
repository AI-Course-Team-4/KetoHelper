import { useState } from 'react'
import { Box, Typography, Grid, Button, Alert, Paper, Card, CardContent, Chip, Avatar, Container } from '@mui/material'
import { Lock, Psychology, Restaurant, LocationOn, Search, AutoAwesome } from '@mui/icons-material'
import { motion } from 'framer-motion'
import { useAuthStore } from '@store/authStore'
import KakaoMap from '../components/KakaoMap'
import RestaurantCard from '@components/RestaurantCard'
import AISearchComponent from '../components/AISearchComponent'
import { mockRestaurants } from '@components/RestaurantCard'

const RestaurantsPage = () => {
  const { user, isAuthenticated } = useAuthStore()
  const [favorites, setFavorites] = useState<string[]>([])
  const [aiRecommendedRestaurants, setAiRecommendedRestaurants] = useState<any[]>([])

  const hasSubscription = user?.subscription?.isActive || false

  const quickPrompts = [
    {
      text: '강남 근처에서 키토 친화적인 식당 찾아줘',
      icon: <LocationOn />,
      category: '지역별'
    },
    {
      text: '스테이크 전문점 중에 키토 메뉴가 많은 곳',
      icon: <Restaurant />,
      category: '음식 종류'
    },
    {
      text: '점심시간에 갈 수 있는 가까운 키토 식당',
      icon: <Search />,
      category: '시간별'
    },
    {
      text: '분위기 좋고 키토 옵션이 다양한 레스토랑',
      icon: <AutoAwesome />,
      category: '분위기'
    }
  ]

  const toggleFavorite = (restaurantId: string) => {
    setFavorites(prev =>
      prev.includes(restaurantId)
        ? prev.filter(id => id !== restaurantId)
        : [...prev, restaurantId]
    )
  }

  const handleRestaurantSelect = (type: 'recipe' | 'restaurant', item: any) => {
    if (type === 'restaurant') {
      // AI가 추천한 식당을 추천 목록에 추가
      setAiRecommendedRestaurants(prev => {
        const exists = prev.find(r => r.id === item.id)
        if (!exists) {
          return [item, ...prev.slice(0, 4)] // 최대 5개까지 유지
        }
        return prev
      })
      console.log('Selected restaurant:', item)
    }
  }

  const height = 800

  return (
    <Container maxWidth={false} sx={{ py: 1, px: { xs: 1, sm: 2, md: 3, lg: 4 } }}>
      {/* AI 헤더 섹션 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Box
          sx={{
            background: 'linear-gradient(135deg, #FF8F00 0%, #FFB74D 30%, #2E7D32 100%)',
            color: 'white',
            py: { xs: 1.5, md: 2 },
            px: 2,
            borderRadius: 3,
            mb: 2,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={8}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ 
                    backgroundColor: 'rgba(255,255,255,0.2)', 
                    mr: 2, 
                    width: 40, 
                    height: 40,
                    backdropFilter: 'blur(10px)'
                  }}>
                    <Psychology sx={{ fontSize: 20 }} />
                  </Avatar>
                  <Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                      🍽️ AI 맛집 어시스턴트
                    </Typography>
                    <Chip 
                      label="위치 기반 추천" 
                      size="small"
                      sx={{ 
                        backgroundColor: 'rgba(255,255,255,0.2)',
                        color: 'white',
                        backdropFilter: 'blur(10px)'
                      }} 
                    />
                  </Box>
                </Box>
                <Typography variant="body1" sx={{ mb: 1, opacity: 0.9, fontWeight: 400 }}>
                  "강남에서 키토 친화적인 식당 찾아줘"처럼 자연스럽게 물어보세요
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  AI가 위치, 메뉴, 리뷰를 종합해서 완벽한 키토 맛집을 추천해드립니다
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ display: { xs: 'none', md: 'block' }, textAlign: 'center' }}>
                  <Typography variant="h2" sx={{ fontSize: '2.5rem', opacity: 0.3 }}>
                    🗺️
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </Box>
      </motion.div>

      {/* 근처 키토 맛집 - 완전히 왼쪽으로 분리 */}
      <Box sx={{ display: 'flex', gap: 2 }}>
        {/* 근처 키토 맛집 영역 - 왼쪽 고정 */}
        <Box sx={{ width: { xs: '100%', lg: '300px' }, flexShrink: 0 }}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Card sx={{ 
              borderRadius: 3, 
              boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
              border: '1px solid',
              borderColor: 'secondary.light',
              height: 'fit-content'
            }}>
              <Box sx={{ 
                background: 'linear-gradient(90deg, #FF8F00 0%, #FFB74D 100%)',
                color: 'white',
                p: 1.5,
                display: 'flex',
                alignItems: 'center'
              }}>
                <LocationOn sx={{ mr: 1 }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  📍 근처 키토 맛집
                </Typography>
              </Box>
              <CardContent sx={{ p: 1.5 }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  {mockRestaurants.slice(0, isAuthenticated ? (hasSubscription ? 5 : 3) : 3).map((restaurant) => (
                    <RestaurantCard
                      key={restaurant.id}
                      restaurant={restaurant as any}
                      isFavorite={favorites.includes(restaurant.id)}
                      onToggleFavorite={toggleFavorite}
                    />
                  ))}
                </Box>
                
                {/* 더 보기 안내 */}
                {mockRestaurants.length > 3 && (
                  <Box sx={{ mt: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {isAuthenticated 
                        ? hasSubscription 
                          ? '모든 맛집을 확인하고 있습니다'
                          : `${mockRestaurants.length - 3}개 맛집 더 보기`
                        : `${mockRestaurants.length - 3}개 맛집 더 보기`
                      }
                    </Typography>
                    {!hasSubscription && (
                      <Button 
                        variant="outlined" 
                        size="small"
                        href={isAuthenticated ? "/subscription" : "/login"}
                      >
                        {isAuthenticated ? "프리미엄 구독" : "로그인하기"}
                      </Button>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </Box>

        {/* 오른쪽 영역 - 지도와 AI 어시스턴트 나란히 */}
        <Box sx={{ flex: 1 }}>
          <Grid container spacing={2}>
            {/* 지도 영역 */}
            <Grid item xs={12} lg={7}>
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: 0.4 }}
              >
                <Card sx={{ 
                  borderRadius: 4, 
                  overflow: 'hidden',
                  boxShadow: '0 12px 40px rgba(0,0,0,0.1)',
                  border: '2px solid',
                  borderColor: 'secondary.light'
                }}>
                  <Box sx={{ 
                    background: 'linear-gradient(90deg, #FF8F00 0%, #FFB74D 100%)',
                    color: 'white',
                    p: 1.5,
                    display: 'flex',
                    alignItems: 'center'
                  }}>
                    <LocationOn sx={{ mr: 1 }} />
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      키토 맛집 지도
                    </Typography>
                    <Chip 
                      label="실시간 업데이트" 
                      size="small" 
                      sx={{ 
                        ml: 'auto',
                        backgroundColor: 'rgba(255,255,255,0.2)',
                        color: 'white'
                      }} 
                    />
                  </Box>
                  <Box sx={{ height: { xs: 400, md: height } }}>
                    <KakaoMap height="100%" />
                  </Box>
                </Card>
              </motion.div>
            </Grid>

            {/* AI 어시스턴트 채팅 영역 */}
            <Grid item xs={12} lg={5}>
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.6 }}
              >
                <Card sx={{ 
                  borderRadius: 3, 
                  boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                  border: '1px solid',
                  borderColor: 'secondary.light',
                  overflow: 'hidden',
                  height: '100%'
                }}>
                  <Box sx={{ 
                    background: 'linear-gradient(90deg, #FF8F00 0%, #FFB74D 100%)',
                    color: 'white',
                    p: 1,
                    display: 'flex',
                    alignItems: 'center'
                  }}>
                    <Psychology sx={{ mr: 1, fontSize: 20 }} />
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      AI 어시스턴트
                    </Typography>
                    <Chip 
                      label="GPS 연동" 
                      size="small" 
                      sx={{ 
                        ml: 'auto',
                        backgroundColor: 'rgba(255,255,255,0.2)',
                        color: 'white',
                        fontSize: '0.7rem'
                      }} 
                    />
                  </Box>
                  <CardContent sx={{ p: 0 }}>
                    <AISearchComponent 
                      placeholder="키토 맛집에 대해 물어보세요!"
                      onResultSelect={handleRestaurantSelect}
                      showSuggestions={true}
                      compact={true}
                    />
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>

            {/* 하단 영역 - 인기 질문들 */}
            <Grid item xs={12}>
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.8 }}
              >
                <Card sx={{ borderRadius: 3 }}>
                  <CardContent sx={{ p: 1.5 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1.5 }}>
                      💡 인기 질문들
                    </Typography>
                    <Grid container spacing={1}>
                      {quickPrompts.map((prompt, index) => (
                        <Grid item xs={12} sm={6} key={index}>
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={prompt.icon}
                            sx={{
                              justifyContent: 'flex-start',
                              textAlign: 'left',
                              py: 1,
                              px: 1.5,
                              borderRadius: 2,
                              fontSize: '0.75rem',
                              width: '100%',
                              '&:hover': {
                                backgroundColor: 'secondary.light',
                                color: 'white',
                                borderColor: 'secondary.main'
                              }
                            }}
                            onClick={() => {
                              console.log('Quick prompt clicked:', prompt.text)
                            }}
                          >
                            <Box sx={{ flex: 1 }}>
                              <Typography variant="caption" sx={{ textAlign: 'left', lineHeight: 1.2 }}>
                                {prompt.text}
                              </Typography>
                            </Box>
                          </Button>
                        </Grid>
                      ))}
                    </Grid>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>

            {/* AI 추천 식당 및 사용자 상태별 안내 */}
            <Grid item xs={12}>
              <Grid container spacing={2}>
                {/* AI 추천 식당 */}
                {aiRecommendedRestaurants.length > 0 && (
                  <Grid item xs={12} md={6}>
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.6, delay: 1.0 }}
                    >
                      <Card sx={{ borderRadius: 3, height: '100%' }}>
                        <CardContent sx={{ p: 1.5 }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1.5 }}>
                            🤖 AI 추천 맛집
                          </Typography>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            {aiRecommendedRestaurants.slice(0, 2).map((restaurant) => (
                              <Button
                                key={restaurant.id}
                                variant="outlined"
                                size="small"
                                onClick={() => handleRestaurantSelect('restaurant', restaurant)}
                                sx={{
                                  justifyContent: 'flex-start',
                                  textAlign: 'left',
                                  py: 1,
                                  px: 1.5,
                                  borderRadius: 2,
                                  fontSize: '0.75rem',
                                  '&:hover': {
                                    backgroundColor: 'primary.light',
                                    color: 'white',
                                    borderColor: 'primary.main'
                                  }
                                }}
                              >
                                <Box sx={{ flex: 1 }}>
                                  <Typography variant="caption" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                                    {restaurant.name}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.65rem' }}>
                                    {restaurant.distance} · ⭐ {restaurant.rating}
                                  </Typography>
                                </Box>
                              </Button>
                            ))}
                          </Box>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                )}

                {/* 사용자 상태별 안내 */}
                <Grid item xs={12} md={6}>
                  {!isAuthenticated && (
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.6, delay: 1.2 }}
                    >
                      <Alert severity="info" sx={{ borderRadius: 3, p: 1, height: '100%' }}>
                        <Typography variant="caption">
                          로그인하면 위치 기반 개인 맞춤 맛집 추천을 받을 수 있습니다.
                        </Typography>
                        <Button variant="outlined" size="small" href="/login" sx={{ mt: 1, fontSize: '0.7rem' }}>
                          로그인하기
                        </Button>
                      </Alert>
                    </motion.div>
                  )}

                  {isAuthenticated && !hasSubscription && (
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.6, delay: 1.2 }}
                    >
                      <Paper sx={{ 
                        p: 1.5, 
                        background: 'linear-gradient(135deg, #FF8F00 0%, #FFB74D 100%)', 
                        color: 'white',
                        borderRadius: 3,
                        height: '100%'
                      }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Lock sx={{ mr: 1, fontSize: 18 }} />
                          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                            AI 프리미엄 기능
                          </Typography>
                        </Box>
                        <Typography variant="caption" sx={{ mb: 1.5, opacity: 0.9 }}>
                          무제한 맛집 검색, 실시간 대기시간, 개인 맞춤 추천
                        </Typography>
                        <Button variant="contained" size="small" href="/subscription" sx={{ backgroundColor: 'white', color: 'primary.main', fontSize: '0.7rem' }}>
                          프리미엄 구독하기
                        </Button>
                      </Paper>
                    </motion.div>
                  )}
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        </Box>
      </Box>
    </Container>
  )
}

export default RestaurantsPage
