import { useState } from 'react'
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardMedia, 
  CardContent, 
  Chip,
  Button,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Paper
} from '@mui/material'
import { Search, AccessTime, TrendingUp, Psychology, Lock } from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'

const MealsPage = () => {
  const { user, isAuthenticated } = useAuthStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [mealType, setMealType] = useState('')
  const [difficulty, setDifficulty] = useState('')

  const hasSubscription = user?.subscription?.isActive || false

  // 임시 데이터 (실제로는 API에서 가져옴)
  const mockRecipes = [
    {
      id: '1',
      title: '아보카도 베이컨 샐러드',
      description: '신선한 아보카도와 바삭한 베이컨이 만나는 완벽한 키토 샐러드',
      imageUrl: 'https://via.placeholder.com/300x200',
      cookingTime: 15,
      difficulty: 'easy',
      nutrition: { calories: 380, carbs: 8, protein: 15, fat: 32 },
      rating: 4.5,
      isKetoFriendly: true,
    },
    {
      id: '2',
      title: '치킨 크림 스프',
      description: '부드럽고 진한 크림 스프로 포만감을 주는 키토 요리',
      imageUrl: 'https://via.placeholder.com/300x200',
      cookingTime: 30,
      difficulty: 'medium',
      nutrition: { calories: 420, carbs: 6, protein: 28, fat: 30 },
      rating: 4.8,
      isKetoFriendly: true,
    },
    {
      id: '3',
      title: '연어 스테이크',
      description: '오메가3이 풍부한 연어로 만든 고급 키토 요리',
      imageUrl: 'https://via.placeholder.com/300x200',
      cookingTime: 20,
      difficulty: 'medium',
      nutrition: { calories: 450, carbs: 4, protein: 35, fat: 32 },
      rating: 4.7,
      isKetoFriendly: true,
    },
  ]

  return (
    <Box>
      {/* 페이지 헤더 */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" sx={{ fontWeight: 700, mb: 2 }}>
          🍳 키토 식단 추천
        </Typography>
        <Typography variant="body1" color="text.secondary">
          AI가 추천하는 맞춤형 키토 레시피를 확인하고, 건강한 식단을 계획해보세요.
        </Typography>
      </Box>

      {/* 검색 및 필터 */}
      <Box sx={{ mb: 4 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="레시피 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>식사 시간</InputLabel>
              <Select
                value={mealType}
                label="식사 시간"
                onChange={(e) => setMealType(e.target.value)}
              >
                <MenuItem value="">전체</MenuItem>
                <MenuItem value="breakfast">아침</MenuItem>
                <MenuItem value="lunch">점심</MenuItem>
                <MenuItem value="dinner">저녁</MenuItem>
                <MenuItem value="snack">간식</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>난이도</InputLabel>
              <Select
                value={difficulty}
                label="난이도"
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <MenuItem value="">전체</MenuItem>
                <MenuItem value="easy">쉬움</MenuItem>
                <MenuItem value="medium">보통</MenuItem>
                <MenuItem value="hard">어려움</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Box>

      {/* 사용자 상태별 안내 */}
      {!isAuthenticated && (
        <Alert severity="info" sx={{ mb: 4 }}>
          <Typography variant="body1">
            로그인하면 개인 선호도를 반영한 맞춤형 레시피 추천을 받을 수 있습니다.
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
              프리미엄으로 더 많은 레시피를 만나보세요!
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ mb: 2, opacity: 0.9 }}>
            구독하면 무제한 레시피와 개인 맞춤 식단 캘린더를 이용할 수 있습니다.
          </Typography>
          <Button variant="contained" size="small" href="/subscription" sx={{ backgroundColor: 'white', color: 'primary.main' }}>
            프리미엄 구독하기
          </Button>
        </Paper>
      )}

      {/* AI 추천 섹션 */}
      <Box sx={{ mb: 6 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          {isAuthenticated ? <Psychology sx={{ mr: 1, color: 'primary.main' }} /> : <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />}
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            {isAuthenticated ? (hasSubscription ? 'AI 프리미엄 추천' : 'AI 기본 추천') : '인기 키토 레시피'}
          </Typography>
        </Box>
        
        {isAuthenticated && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {hasSubscription 
              ? '🎯 회원님의 선호도와 목표를 고려한 맞춤형 추천입니다'
              : '⭐ 기본 추천 - 구독하면 개인 맞춤 추천을 받을 수 있습니다'
            }
          </Typography>
        )}
        
        <Grid container spacing={3}>
          {mockRecipes.slice(0, isAuthenticated ? (hasSubscription ? mockRecipes.length : 3) : 3).map((recipe) => (
            <Grid item xs={12} sm={6} md={4} key={recipe.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
              >
                <CardMedia
                  component="img"
                  height="200"
                  image={recipe.imageUrl}
                  alt={recipe.title}
                />
                <CardContent sx={{ flexGrow: 1, p: 3 }}>
                  {/* 키토 친화 뱃지 */}
                  {recipe.isKetoFriendly && (
                    <Chip
                      label="키토 친화적"
                      size="small"
                      color="primary"
                      sx={{ mb: 2 }}
                    />
                  )}
                  
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                    {recipe.title}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {recipe.description}
                  </Typography>
                  
                  {/* 조리 시간 및 난이도 */}
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <AccessTime sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
                      {recipe.cookingTime}분
                    </Typography>
                    <Chip
                      label={recipe.difficulty === 'easy' ? '쉬움' : recipe.difficulty === 'medium' ? '보통' : '어려움'}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                  
                  {/* 영양 정보 */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      칼로리: {recipe.nutrition.calories}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      탄수화물: {recipe.nutrition.carbs}g
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      단백질: {recipe.nutrition.protein}g
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      지방: {recipe.nutrition.fat}g
                    </Typography>
                  </Box>
                  
                  <Button
                    fullWidth
                    variant="contained"
                    color="primary"
                  >
                    레시피 보기
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* 더 많은 레시피 로드 버튼 */}
      <Box sx={{ textAlign: 'center' }}>
        <Button variant="outlined" size="large">
          더 많은 레시피 보기
        </Button>
      </Box>
    </Box>
  )
}

export default MealsPage
