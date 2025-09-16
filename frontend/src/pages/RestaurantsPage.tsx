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

  const height = 700

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
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
            py: { xs: 4, md: 6 },
            px: 4,
            borderRadius: 4,
            mb: 4,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} md={8}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ 
                    backgroundColor: 'rgba(255,255,255,0.2)', 
                    mr: 2, 
                    width: 56, 
                    height: 56,
                    backdropFilter: 'blur(10px)'
                  }}>
                    <Psychology sx={{ fontSize: 28 }} />
                  </Avatar>
                  <Box>
                    <Typography variant="h3" sx={{ fontWeight: 800, mb: 0.5 }}>
                      🍽️ AI 맛집 어시스턴트
                    </Typography>
                    <Chip 
                      label="위치 기반 추천" 
                      sx={{ 
                        backgroundColor: 'rgba(255,255,255,0.2)',
                        color: 'white',
                        backdropFilter: 'blur(10px)'
                      }} 
                    />
                  </Box>
                </Box>
                <Typography variant="h6" sx={{ mb: 2, opacity: 0.9, fontWeight: 400 }}>
                  "강남에서 키토 친화적인 식당 찾아줘"처럼 자연스럽게 물어보세요
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.8 }}>
                  AI가 위치, 메뉴, 리뷰를 종합해서 완벽한 키토 맛집을 추천해드립니다
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ display: { xs: 'none', md: 'block' }, textAlign: 'center' }}>
                  <Typography variant="h1" sx={{ fontSize: '4rem', opacity: 0.3 }}>
                    🗺️
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </Box>
      </motion.div>

      <Grid container spacing={4}>
        {/* 지도 영역 */}
        <Grid item xs={12} lg={7}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
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
                p: 2,
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

        {/* AI 대화 및 추천 영역 */}
        <Grid item xs={12} lg={5}>
          {/* AI 검색 컴포넌트 */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <Card sx={{ 
              mb: 3, 
              borderRadius: 4, 
              boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
              border: '1px solid',
              borderColor: 'secondary.light',
              overflow: 'hidden'
            }}>
              <Box sx={{ 
                background: 'linear-gradient(90deg, #FF8F00 0%, #FFB74D 100%)',
                color: 'white',
                p: 2,
                display: 'flex',
                alignItems: 'center'
              }}>
                <Psychology sx={{ mr: 1 }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  맛집 AI 어시스턴트
                </Typography>
                <Chip 
                  label="GPS 연동" 
                  size="small" 
                  sx={{ 
                    ml: 'auto',
                    backgroundColor: 'rgba(255,255,255,0.2)',
                    color: 'white'
                  }} 
                />
              </Box>
              <CardContent sx={{ p: 0 }}>
                <AISearchComponent 
                  placeholder="키토 친화적인 맛집에 대해 무엇이든 물어보세요! 예: '강남역 근처 키토 메뉴가 많은 식당'"
                  onResultSelect={handleRestaurantSelect}
                  showSuggestions={true}
                  compact={true}
                />
              </CardContent>
            </Card>
          </motion.div>

          {/* 빠른 질문 제안 */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <Card sx={{ mb: 3, borderRadius: 3 }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  💡 인기 질문들
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
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
                        <Typography variant="body2" sx={{ fontSize: '0.8rem', textAlign: 'left' }}>
                          {prompt.text}
                        </Typography>
                        <Chip 
                          label={prompt.category} 
                          size="small" 
                          sx={{ mt: 0.5, height: 18, fontSize: '0.65rem' }} 
                        />
                      </Box>
                    </Button>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </motion.div>

          {/* AI 추천 식당 */}
          {aiRecommendedRestaurants.length > 0 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.8 }}
            >
              <Card sx={{ mb: 3, borderRadius: 3 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                    🤖 AI가 추천한 맛집
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {aiRecommendedRestaurants.slice(0, 3).map((restaurant) => (
                      <Button
                        key={restaurant.id}
                        variant="outlined"
                        size="small"
                        onClick={() => handleRestaurantSelect('restaurant', restaurant)}
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
                      >
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="body2" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
                            {restaurant.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {restaurant.distance} · ⭐ {restaurant.rating}
                          </Typography>
                        </Box>
                      </Button>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* 실제 식당 목록 */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 1.0 }}
          >
            <Card sx={{ borderRadius: 3 }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  📍 근처 키토 맛집
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
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

          {/* 사용자 상태별 안내 */}
          {!isAuthenticated && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 1.2 }}
            >
              <Alert severity="info" sx={{ mt: 3, borderRadius: 3 }}>
                <Typography variant="body2">
                  로그인하면 위치 기반 개인 맞춤 맛집 추천을 받을 수 있습니다.
                </Typography>
                <Button variant="outlined" size="small" href="/login" sx={{ mt: 1 }}>
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
                p: 3, 
                mt: 3, 
                background: 'linear-gradient(135deg, #FF8F00 0%, #FFB74D 100%)', 
                color: 'white',
                borderRadius: 3
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Lock sx={{ mr: 1 }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    AI 프리미엄 맛집 기능
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ mb: 2, opacity: 0.9 }}>
                  무제한 맛집 검색, 실시간 대기시간, 개인 맞춤 추천
                </Typography>
                <Button variant="contained" size="small" href="/subscription" sx={{ backgroundColor: 'white', color: 'primary.main' }}>
                  프리미엄 구독하기
                </Button>
              </Paper>
            </motion.div>
          )}
        </Grid>
      </Grid>
    </Container>
  )
}

export default RestaurantsPage
