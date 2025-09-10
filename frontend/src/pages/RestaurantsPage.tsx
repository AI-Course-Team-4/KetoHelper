import { useState } from 'react'
import { Box, Typography, Grid, Button, TextField, InputAdornment, Alert, Paper } from '@mui/material'
import { Search, Lock } from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'
import KakaoMap from '../components/KakaoMap'
import RestaurantCard from '@components/RestaurantCard'
import type { Restaurant } from '@components/RestaurantCard'

// 지도 좌표를 포함할 수 있는 로컬 타입
type MapRestaurant = Restaurant & { lat?: number; lng?: number }

// 임시 데이터
export const mockRestaurants: MapRestaurant[] = [
  {
    id: '1',
    name: '키토 스테이크하우스',
    address: '서울시 강남구 테헤란로 123',
    phone: '02-1234-5678',
    ketoScore: 95,
    images: ['https://via.placeholder.com/300x200'],
    menu: [
      { name: '립아이 스테이크', price: 45000, carbs: 2, isKetoFriendly: true },
      { name: '연어 그릴', price: 32000, carbs: 1, isKetoFriendly: true },
    ],
    lat: 37.50000000,
    lng: 126.90000000,
  },
  {
    id: '2',
    name: '아보카도 카페',
    address: '서울시 강남구 신사동 456',
    phone: '02-2345-6789',
    ketoScore: 88,
    images: ['https://via.placeholder.com/300x200'],
    menu: [
      { name: '아보카도 샐러드', price: 15000, carbs: 8, isKetoFriendly: true },
      { name: '키토 커피', price: 6000, carbs: 2, isKetoFriendly: true },
    ],
    lat: 37.51111111,
    lng: 126.91111111,
  },
  {
    id: '3',
    name: '해산물 전문점',
    address: '서울시 강남구 압구정동 789',
    phone: '02-3456-7890',
    ketoScore: 92,
    images: ['https://via.placeholder.com/300x200'],
    menu: [
      { name: '랍스터 그라탱', price: 68000, carbs: 5, isKetoFriendly: true },
      { name: '새우 샐러드', price: 25000, carbs: 6, isKetoFriendly: true },
    ],
    lat: 37.52222222,
    lng: 126.92222222,
  },
  {
    id: '4',
    name: '저탄수 빵집',
    address: '서울시 강남구 역삼동 101',
    phone: '02-4567-8901',
    ketoScore: 85,
    images: ['https://via.placeholder.com/300x200'],
    menu: [
      { name: '아몬드 크루아상', price: 5500, carbs: 4, isKetoFriendly: true },
      { name: '치즈 머핀', price: 4800, carbs: 3, isKetoFriendly: true },
    ],
    lat: 37.53000000,
    lng: 126.93000000,
  },
  {
    id: '5',
    name: '그릭 요거트 바',
    address: '서울시 강남구 논현동 222',
    phone: '02-5678-9012',
    ketoScore: 90,
    images: ['https://via.placeholder.com/300x200'],
    menu: [
      { name: '플레인 그릭 요거트', price: 7000, carbs: 6, isKetoFriendly: true },
      { name: '코코넛 토핑 요거트', price: 8500, carbs: 5, isKetoFriendly: true },
    ],
    lat: 37.54000000,
    lng: 126.94000000,
  },
  {
    id: '6',
    name: '저당 디저트 카페',
    address: '서울시 강남구 삼성동 333',
    phone: '02-6789-0123',
    ketoScore: 87,
    images: ['https://via.placeholder.com/300x200'],
    menu: [
      { name: '슈가프리 티라미수', price: 9500, carbs: 7, isKetoFriendly: true },
      { name: '에리스리톨 브라우니', price: 8500, carbs: 4, isKetoFriendly: true },
    ],
    lat: 37.55000000,
    lng: 126.95000000,
  },
  {
    id: '7',
    name: '키토 버거 하우스',
    address: '서울시 강남구 청담동 444',
    phone: '02-7890-1234',
    ketoScore: 93,
    images: ['https://via.placeholder.com/300x200'],
    menu: [
      { name: '버터레터스 버거', price: 18000, carbs: 3, isKetoFriendly: true },
      { name: '치즈 베이컨 버거', price: 20000, carbs: 4, isKetoFriendly: true },
    ],
    lat: 37.56000000,
    lng: 126.96000000,
  },
  {
    id: '8',
    name: '올리브 오일 레스토랑',
    address: '서울시 강남구 대치동 555',
    phone: '02-8901-2345',
    ketoScore: 91,
    images: ['https://via.placeholder.com/300x200'],
    menu: [
      { name: '올리브 오일 파스타 (저탄수)', price: 22000, carbs: 9, isKetoFriendly: true },
      { name: '그릴드 치킨 샐러드', price: 19000, carbs: 5, isKetoFriendly: true },
    ],
    lat: 37.57000000,
    lng: 126.97000000,
  },
  {
    id: '9',
    name: '헬시 바베큐',
    address: '서울시 강남구 신논현로 666',
    phone: '02-9012-3456',
    ketoScore: 94,
    images: ['https://via.placeholder.com/300x200'],
    menu: [
      { name: '훈제 삼겹살', price: 28000, carbs: 1, isKetoFriendly: true },
      { name: '바베큐 폭립', price: 35000, carbs: 3, isKetoFriendly: true },
    ],
    lat: 37.58000000,
    lng: 126.98000000,
  },  
]

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
            <KakaoMap
              height="100%"
              restaurants={mockRestaurants}
              onMarkerClick={({ index }) => {
                const targetId = mockRestaurants[index]?.id
                if (!targetId) return
                const el = document.getElementById(`restaurant-card-${targetId}`)
                const container = document.getElementById('restaurant-list-container')
                if (el && container) {
                  const elRect = el.getBoundingClientRect()
                  const containerRect = container.getBoundingClientRect()
                  const offset = elRect.top - containerRect.top + container.scrollTop - 8
                  container.scrollTo({ top: offset, behavior: 'smooth' })
                }
              }}
            />
          </Box>
        </Grid>
        <Grid item xs={12} md={4}>
          {/* 추천 식당 목록 */}
          <Box>
            <Box id="restaurant-list-container" sx={{ height: { xs: 'auto', md: height }, overflowY: { xs: 'visible', md: 'auto' }, pr: { md: 1 } }}>
              <Grid container spacing={3}>
                {mockRestaurants.slice(0, isAuthenticated ? (hasSubscription ? mockRestaurants.length : 3) : 3).map((restaurant: Restaurant) => (
                  <Grid item xs={12} key={restaurant.id} id={`restaurant-card-${restaurant.id}`}>
                    <RestaurantCard
                      restaurant={restaurant}
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
