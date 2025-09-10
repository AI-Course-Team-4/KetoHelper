import { useState } from 'react'
import { Box, Typography, Grid, Button, TextField, InputAdornment, Alert, Paper } from '@mui/material'
import { Search, Lock } from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'
import KakaoMap from '../components/KakaoMap'
import RestaurantCard from '@components/RestaurantCard'
import { mockRestaurants } from '@components/RestaurantCard'

const RestaurantsPage = () => {
  const { user, isAuthenticated } = useAuthStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [favorites, setFavorites] = useState<string[]>([])

  const hasSubscription = user?.subscription?.isActive || false

  const toggleFavorite = (restaurantId: string) => {
    setFavorites(prev =>
      prev.includes(restaurantId)
        ? prev.filter(id => id !== restaurantId)
        : [...prev, restaurantId]
    )
  }

  const height = 700

  return (
    <Box>
      {/* 페이지 헤더 */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" sx={{ fontWeight: 700, mb: 2 }}>
          🍽️ 키토 친화적 식당 추천
        </Typography>
        <Typography variant="body1" color="text.secondary">
          ⭐ 근처에서 키토 다이어트에 적합한 식당을 찾아보세요.
          구독 시 개인 맞춤형 추천도 받아볼 수 있습니다.
        </Typography>
      </Box>

      {/* 검색 */}
      <Box sx={{ mb: 4 }}>
        <TextField
          fullWidth
          placeholder="식당 이름이나 지역을 검색해보세요..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
          }}
          sx={{ maxWidth: 600 }}
        />
      </Box>

      {/* 사용자 상태별 안내 */}
      {!isAuthenticated && (
        <Alert severity="info" sx={{ mb: 4 }}>
          <Typography variant="body1">
            로그인하면 개인 선호도를 반영한 맞춤형 식당 추천을 받을 수 있습니다.
          </Typography>
          <Button variant="outlined" size="small" href="/login" sx={{ mt: 1 }}>
            로그인하기
          </Button>
        </Alert>
      )}

      {isAuthenticated && !hasSubscription && (
        <Paper sx={{ p: 3, mb: 4, background: 'linear-gradient(135deg, #FF8F00 0%, #FFB74D 100%)', color: 'white' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Lock sx={{ mr: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              프리미엄으로 더 많은 식당을 찾아보세요!
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ mb: 2, opacity: 0.9 }}>
            구독하면 무제한 식당 정보와 상세한 키토 메뉴 분석을 이용할 수 있습니다.
          </Typography>
          <Button variant="contained" size="small" href="/subscription" sx={{ backgroundColor: 'white', color: 'primary.main' }}>
            프리미엄 구독하기
          </Button>
        </Paper>
      )}

      <Grid container spacing={3} sx={{ mb: 6, alignItems: 'flex-start' }}>
        <Grid item xs={12} md={8}>
          <Box sx={{ width: '100%', height: { xs: 360, md: height }, position: { md: 'sticky' as const }, top: { md: 80 } }}>
            <KakaoMap height="100%" />
          </Box>
        </Grid>
        <Grid item xs={12} md={4}>
          {/* 추천 식당 목록 */}
          <Box>
            <Box sx={{ height: { xs: 'auto', md: height }, overflowY: { xs: 'visible', md: 'auto' }, pr: { md: 1 } }}>
              <Grid container spacing={3}>
                {mockRestaurants.slice(0, isAuthenticated ? (hasSubscription ? mockRestaurants.length : 3) : 3).map((restaurant) => (
                  <Grid item xs={12} key={restaurant.id}>
                    <RestaurantCard
                      restaurant={restaurant as any}
                      isFavorite={favorites.includes(restaurant.id)}
                      onToggleFavorite={toggleFavorite}
                    />
                  </Grid>
                ))}
              </Grid>
            </Box>
          </Box>
        </Grid>
      </Grid>
    </Box>
  )
}

export default RestaurantsPage
