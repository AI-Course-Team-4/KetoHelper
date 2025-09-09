import { useState } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Button,
  TextField,
  InputAdornment,
  Rating,
  IconButton,
  Alert,
  Paper
} from '@mui/material'
import { Search, LocationOn, Phone, Favorite, FavoriteBorder, Lock, Psychology, TrendingUp } from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'
import KakaoMap from '../components/KakaoMap'

const RestaurantsPage = () => {
  const { user, isAuthenticated } = useAuthStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [favorites, setFavorites] = useState<string[]>([])

  const hasSubscription = user?.subscription?.isActive || false

  // 임시 데이터
  const mockRestaurants = [
    {
      id: '1',
      name: '키토 스테이크하우스',
      address: '서울시 강남구 테헤란로 123',
      phone: '02-1234-5678',
      category: '스테이크',
      priceRange: 3,
      rating: 4.5,
      reviewCount: 128,
      ketoScore: 95,
      distance: 0.8,
      images: ['https://via.placeholder.com/300x200'],
      menu: [
        { name: '립아이 스테이크', price: 45000, carbs: 2, isKetoFriendly: true },
        { name: '연어 그릴', price: 32000, carbs: 1, isKetoFriendly: true },
      ],
    },
    {
      id: '2',
      name: '아보카도 카페',
      address: '서울시 강남구 신사동 456',
      phone: '02-2345-6789',
      category: '카페',
      priceRange: 2,
      rating: 4.3,
      reviewCount: 89,
      ketoScore: 88,
      distance: 1.2,
      images: ['https://via.placeholder.com/300x200'],
      menu: [
        { name: '아보카도 샐러드', price: 15000, carbs: 8, isKetoFriendly: true },
        { name: '키토 커피', price: 6000, carbs: 2, isKetoFriendly: true },
      ],
    },
    {
      id: '3',
      name: '해산물 전문점',
      address: '서울시 강남구 압구정동 789',
      phone: '02-3456-7890',
      category: '해산물',
      priceRange: 3,
      rating: 4.7,
      reviewCount: 203,
      ketoScore: 92,
      distance: 2.1,
      images: ['https://via.placeholder.com/300x200'],
      menu: [
        { name: '랍스터 그라탱', price: 68000, carbs: 5, isKetoFriendly: true },
        { name: '새우 샐러드', price: 25000, carbs: 6, isKetoFriendly: true },
      ],
    },
  ]

  const toggleFavorite = (restaurantId: string) => {
    setFavorites(prev =>
      prev.includes(restaurantId)
        ? prev.filter(id => id !== restaurantId)
        : [...prev, restaurantId]
    )
  }

  const getPriceRangeText = (range: number) => {
    return '₩'.repeat(range)
  }

  const getKetoScoreColor = (score: number) => {
    if (score >= 90) return 'success'
    if (score >= 70) return 'warning'
    return 'error'
  }

  return (
    <Box>
      {/* 페이지 헤더 */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" sx={{ fontWeight: 700, mb: 2 }}>
          🍽️ 키토 친화적 식당
        </Typography>
        <Typography variant="body1" color="text.secondary">
          근처의 키토 다이어트에 적합한 식당을 찾아보세요.
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

      <div style={{ width: "100%", height: "500px" }}>
        <KakaoMap lat={37.5665} lng={126.9780} level={3} />
      </div>

      {/* 추천 식당 목록 */}
      <Box sx={{ mb: 6 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          {isAuthenticated ? <Psychology sx={{ mr: 1, color: 'primary.main' }} /> : <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />}
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            {isAuthenticated ? (hasSubscription ? 'AI 프리미엄 추천 식당' : 'AI 기본 추천 식당') : '인기 키토 식당'}
          </Typography>
        </Box>

        {isAuthenticated && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {hasSubscription
              ? '🎯 회원님의 위치와 선호도를 고려한 맞춤형 추천입니다'
              : '⭐ 기본 추천 - 구독하면 개인 맞춤 추천을 받을 수 있습니다'
            }
          </Typography>
        )}

        <Grid container spacing={3}>
          {mockRestaurants.slice(0, isAuthenticated ? (hasSubscription ? mockRestaurants.length : 3) : 3).map((restaurant) => (
            <Grid item xs={12} md={6} lg={4} key={restaurant.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 4,
                  },
                }}
              >
                <Box sx={{ position: 'relative' }}>
                  <Box
                    component="img"
                    src={restaurant.images[0]}
                    alt={restaurant.name}
                    sx={{
                      width: '100%',
                      height: 200,
                      objectFit: 'cover',
                    }}
                  />

                  {/* 즐겨찾기 버튼 */}
                  <IconButton
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleFavorite(restaurant.id)
                    }}
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      backgroundColor: 'rgba(255, 255, 255, 0.9)',
                      '&:hover': {
                        backgroundColor: 'rgba(255, 255, 255, 1)',
                      },
                    }}
                  >
                    {favorites.includes(restaurant.id) ? (
                      <Favorite color="error" />
                    ) : (
                      <FavoriteBorder />
                    )}
                  </IconButton>

                  {/* 키토 점수 뱃지 */}
                  <Chip
                    label={`키토 점수 ${restaurant.ketoScore}`}
                    color={getKetoScoreColor(restaurant.ketoScore) as any}
                    size="small"
                    sx={{
                      position: 'absolute',
                      bottom: 8,
                      left: 8,
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    }}
                  />
                </Box>

                <CardContent sx={{ flexGrow: 1, p: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {restaurant.name}
                    </Typography>
                    <Typography variant="body2" color="primary.main" sx={{ fontWeight: 600 }}>
                      {getPriceRangeText(restaurant.priceRange)}
                    </Typography>
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {restaurant.category}
                  </Typography>

                  {/* 주소 및 거리 */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <LocationOn sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      {restaurant.address} • {restaurant.distance}km
                    </Typography>
                  </Box>

                  {/* 연락처 */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Phone sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      {restaurant.phone}
                    </Typography>
                  </Box>

                  {/* 평점 */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Rating value={restaurant.rating} precision={0.1} size="small" readOnly />
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                      {restaurant.rating} ({restaurant.reviewCount}개 리뷰)
                    </Typography>
                  </Box>

                  {/* 대표 메뉴 */}
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                    추천 키토 메뉴
                  </Typography>
                  {restaurant.menu.slice(0, 2).map((menuItem, index) => (
                    <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">
                        {menuItem.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        ₩{menuItem.price.toLocaleString()}
                      </Typography>
                    </Box>
                  ))}

                  <Button
                    fullWidth
                    variant="contained"
                    color="primary"
                    sx={{ mt: 2 }}
                  >
                    상세 정보 보기
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* 더 많은 식당 로드 버튼 */}
      <Box sx={{ textAlign: 'center' }}>
        <Button variant="outlined" size="large">
          더 많은 식당 보기
        </Button>
      </Box>
    </Box>
  )
}

export default RestaurantsPage
