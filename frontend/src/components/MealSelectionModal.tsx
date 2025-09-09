import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Button,
  Box,
  Typography,
  TextField,
  InputAdornment,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Chip,
  Tabs,
  Tab,
  IconButton,
  Divider,
} from '@mui/material'
import {
  Search,
  Restaurant,
  Star,
  StarBorder,
  Close,
  Add,
  AccessTime,
  LocalFireDepartment,
} from '@mui/icons-material'
import type { Recipe } from '../types/index'

interface MealSelectionModalProps {
  open: boolean
  onClose: () => void
  mealType: 'breakfast' | 'lunch' | 'dinner'
  onMealSelect: (meal: Recipe) => void
}

// 더미 데이터 - 실제로는 API에서 가져올 예정
const dummyRecipes: Recipe[] = [
  {
    id: '1',
    title: '아보카도 토스트',
    description: '키토 친화적인 아침 식사',
    imageUrl: 'https://via.placeholder.com/300x200?text=아보카도+토스트',
    cookingTime: 10,
    difficulty: '쉬움',
    servings: 1,
    ingredients: [],
    instructions: [],
    nutrition: { calories: 320, carbs: 8, protein: 12, fat: 26, fiber: 6 },
    tags: ['키토', '아침'],
    rating: 4.5,
    reviewCount: 45,
    isKetoFriendly: true,
    createdAt: '2025-01-01',
  },
  {
    id: '2',
    title: '치킨 샐러드',
    description: '신선한 채소와 그릴드 치킨',
    imageUrl: 'https://via.placeholder.com/300x200?text=치킨+샐러드',
    cookingTime: 15,
    difficulty: '쉬움',
    servings: 1,
    ingredients: [],
    instructions: [],
    nutrition: { calories: 420, carbs: 12, protein: 35, fat: 25, fiber: 8 },
    tags: ['키토', '점심'],
    rating: 4.7,
    reviewCount: 67,
    isKetoFriendly: true,
    createdAt: '2025-01-01',
  },
  {
    id: '3',
    title: '연어 스테이크',
    description: '오메가3가 풍부한 저녁 식사',
    imageUrl: 'https://via.placeholder.com/300x200?text=연어+스테이크',
    cookingTime: 25,
    difficulty: '중간',
    servings: 1,
    ingredients: [],
    instructions: [],
    nutrition: { calories: 480, carbs: 6, protein: 42, fat: 32, fiber: 2 },
    tags: ['키토', '저녁'],
    rating: 4.9,
    reviewCount: 89,
    isKetoFriendly: true,
    createdAt: '2025-01-01',
  },
  {
    id: '4',
    title: '베이컨 에그',
    description: '고단백 키토 아침',
    imageUrl: 'https://via.placeholder.com/300x200?text=베이컨+에그',
    cookingTime: 8,
    difficulty: '쉬움',
    servings: 1,
    ingredients: [],
    instructions: [],
    nutrition: { calories: 380, carbs: 2, protein: 20, fat: 32, fiber: 0 },
    tags: ['키토', '아침'],
    rating: 4.3,
    reviewCount: 32,
    isKetoFriendly: true,
    createdAt: '2025-01-01',
  },
  {
    id: '5',
    title: '새우 볶음',
    description: '고단백 저녁',
    imageUrl: 'https://via.placeholder.com/300x200?text=새우+볶음',
    cookingTime: 15,
    difficulty: '쉬움',
    servings: 1,
    ingredients: [],
    instructions: [],
    nutrition: { calories: 320, carbs: 8, protein: 35, fat: 18, fiber: 3 },
    tags: ['키토', '저녁'],
    rating: 4.4,
    reviewCount: 29,
    isKetoFriendly: true,
    createdAt: '2025-01-01',
  },
  {
    id: '6',
    title: '그릭 요거트 볼',
    description: '프로틴이 풍부한 아침',
    imageUrl: 'https://via.placeholder.com/300x200?text=그릭+요거트',
    cookingTime: 5,
    difficulty: '쉬움',
    servings: 1,
    ingredients: [],
    instructions: [],
    nutrition: { calories: 200, carbs: 6, protein: 15, fat: 12, fiber: 0 },
    tags: ['키토', '아침'],
    rating: 4.2,
    reviewCount: 41,
    isKetoFriendly: true,
    createdAt: '2025-01-01',
  },
]

// 더미 즐겨찾기 식당 데이터
const dummyFavoriteRestaurants = [
  { id: '1', name: '키토 키친', type: '키토 전문', rating: 4.8 },
  { id: '2', name: '헬시 비스트로', type: '건강식', rating: 4.6 },
  { id: '3', name: '프로틴 하우스', type: '고단백', rating: 4.7 },
]

const MealSelectionModal = ({ open, onClose, mealType, onMealSelect }: MealSelectionModalProps) => {
  const [tabValue, setTabValue] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [filteredRecipes, setFilteredRecipes] = useState(dummyRecipes)
  const [favoriteRecipes, setFavoriteRecipes] = useState<Set<string>>(new Set())

  const mealTypeMap = {
    breakfast: '아침',
    lunch: '점심',
    dinner: '저녁'
  } as const

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    if (query.trim() === '') {
      setFilteredRecipes(dummyRecipes)
    } else {
      const filtered = dummyRecipes.filter(recipe =>
        recipe.title.toLowerCase().includes(query.toLowerCase()) ||
        recipe.description.toLowerCase().includes(query.toLowerCase()) ||
        recipe.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
      )
      setFilteredRecipes(filtered)
    }
  }

  const handleAddToCalendar = (meal: Recipe, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation() // 카드 클릭 이벤트 방지
    }
    onMealSelect(meal)
    onClose()
  }

  const handleToggleFavorite = (recipeId: string, event: React.MouseEvent) => {
    event.stopPropagation() // 카드 클릭 이벤트 방지
    setFavoriteRecipes(prev => {
      const newFavorites = new Set(prev)
      if (newFavorites.has(recipeId)) {
        newFavorites.delete(recipeId)
      } else {
        newFavorites.add(recipeId)
      }
      return newFavorites
    })
    
    // TODO: API 호출로 즐겨찾기 상태 서버에 저장
    console.log(`Recipe ${recipeId} favorite status changed`)
  }

  const loadFavoriteRestaurants = () => {
    // TODO: 실제로는 API를 호출하여 즐겨찾기 식당의 메뉴를 가져옴
    console.log('즐겨찾기 식당 메뉴 로딩...')
    // 예시: API 호출
    // const favoriteMenus = await restaurantService.getFavoriteRestaurantMenus()
    // setFilteredRecipes(favoriteMenus)
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '80vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            {mealTypeMap[mealType]} 식단 선택
          </Typography>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        <Box sx={{ p: 3 }}>
          {/* 검색 및 즐겨찾기 버튼 */}
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <TextField
              fullWidth
              placeholder="식단 검색..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
            <Button
              variant="outlined"
              startIcon={<Star />}
              onClick={loadFavoriteRestaurants}
              sx={{ whiteSpace: 'nowrap' }}
            >
              즐겨찾기 식당
            </Button>
          </Box>

          {/* 탭 */}
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
            <Tab label="추천 식단" />
            <Tab label="즐겨찾기 식당" />
          </Tabs>

          {/* 추천 식단 탭 */}
          {tabValue === 0 && (
            <Grid container spacing={2}>
              {filteredRecipes.map((recipe) => (
                <Grid item xs={12} sm={6} md={4} key={recipe.id}>
                  <Card
                    sx={{
                      height: '100%',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 3,
                      },
                      transition: 'all 0.2s ease-in-out',
                    }}
                  >
                    <CardMedia
                      component="img"
                      height="140"
                      image={recipe.imageUrl}
                      alt={recipe.title}
                    />
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                          {recipe.title}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <IconButton 
                            size="small" 
                            onClick={(e) => handleToggleFavorite(recipe.id, e)}
                            sx={{ color: favoriteRecipes.has(recipe.id) ? 'warning.main' : 'text.secondary' }}
                          >
                            {favoriteRecipes.has(recipe.id) ? (
                              <Star sx={{ fontSize: 16 }} />
                            ) : (
                              <StarBorder sx={{ fontSize: 16 }} />
                            )}
                          </IconButton>
                          <IconButton 
                            size="small" 
                            sx={{ backgroundColor: 'primary.main', color: 'white' }}
                            onClick={(e) => handleAddToCalendar(recipe, e)}
                          >
                            <Add sx={{ fontSize: 16 }} />
                          </IconButton>
                        </Box>
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {recipe.description}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <AccessTime sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                          <Typography variant="caption">{recipe.cookingTime}분</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <LocalFireDepartment sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                          <Typography variant="caption">{recipe.nutrition.calories}kcal</Typography>
                        </Box>
                      </Box>
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          {recipe.tags.slice(0, 2).map((tag) => (
                            <Chip key={tag} label={tag} size="small" variant="outlined" />
                          ))}
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Star sx={{ fontSize: 16, color: 'warning.main', mr: 0.5 }} />
                          <Typography variant="caption">{recipe.rating}</Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}

          {/* 즐겨찾기 식당 탭 */}
          {tabValue === 1 && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                즐겨찾기 식당
              </Typography>
              {dummyFavoriteRestaurants.map((restaurant) => (
                <Card key={restaurant.id} sx={{ mb: 2, cursor: 'pointer' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Restaurant sx={{ mr: 2, color: 'primary.main' }} />
                        <Box>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {restaurant.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {restaurant.type}
                          </Typography>
                        </Box>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Star sx={{ fontSize: 16, color: 'warning.main', mr: 0.5 }} />
                        <Typography variant="body2">{restaurant.rating}</Typography>
                        <Button variant="outlined" size="small" sx={{ ml: 2 }}>
                          메뉴 보기
                        </Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))}
              <Divider sx={{ my: 2 }} />
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                {/* TODO: 백엔드 연동 시 실제 즐겨찾기 식당 데이터를 표시 */}
                백엔드 연동 후 실제 즐겨찾기 식당 메뉴가 표시됩니다.
              </Typography>
            </Box>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  )
}

export default MealSelectionModal
