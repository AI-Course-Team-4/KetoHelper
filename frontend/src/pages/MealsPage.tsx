import { useState, useEffect } from 'react'
import { 
  Box, 
  Typography, 
  Grid, 
  Button,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Paper,
  CircularProgress,
} from '@mui/material'
import { 
  Search, 
  TrendingUp, 
  Psychology, 
  Lock, 
} from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'
import RecipeDetailModal from '../components/RecipeDetailModal'
import RecipeCard from '../components/RecipeCard'
import type { Recipe } from '../types/index'

// TODO: 백엔드 연동 시 사용 - API 서비스 import
// import { recipeService } from '../services/recipeService'
// import { searchService } from '../services/searchService'

// TODO: 백엔드 연동 시 사용 - 검색 API 서비스 구조
// interface SearchService {
//   searchRecipes(query: string, filters: SearchFilters): Promise<Recipe[]>
//   getRecommendedRecipes(userId?: string): Promise<Recipe[]>
//   getPopularRecipes(): Promise<Recipe[]>
// }
//
// interface SearchFilters {
//   mealType?: string
//   difficulty?: string
//   maxCookingTime?: number
//   isKetoFriendly?: boolean
//   page?: number
//   limit?: number
// }

const MealsPage = () => {
  const { user, isAuthenticated } = useAuthStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [mealType, setMealType] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [filteredRecipes, setFilteredRecipes] = useState<Recipe[]>([])
  const [favoriteRecipes, setFavoriteRecipes] = useState<Set<string>>(new Set())
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null)
  const [recipeDetailOpen, setRecipeDetailOpen] = useState(false)
  const [isSearching, setIsSearching] = useState(false)

  const hasSubscription = user?.subscription?.isActive || false

  // 확장된 더미 데이터
  const mockRecipes: Recipe[] = [
    {
      id: '1',
      title: '아보카도 베이컨 샐러드',
      description: '신선한 아보카도와 바삭한 베이컨이 만나는 완벽한 키토 샐러드',
      imageUrl: 'https://via.placeholder.com/300x200?text=아보카도+베이컨+샐러드',
      cookingTime: 15,
      difficulty: '쉬움',
      servings: 2,
      ingredients: [
        { name: '아보카도', amount: 2, unit: '개', carbs: 4 },
        { name: '베이컨', amount: 4, unit: '줄', carbs: 0 },
        { name: '상추', amount: 100, unit: 'g', carbs: 2 },
        { name: '올리브오일', amount: 2, unit: '큰술', carbs: 0 }
      ],
      instructions: ['베이컨을 바삭하게 구워주세요', '아보카도를 적당한 크기로 자르세요', '모든 재료를 섞어주세요'],
      nutrition: { calories: 380, carbs: 8, protein: 15, fat: 32, fiber: 12 },
      tags: ['키토', '샐러드', '아침', '점심'],
      rating: 4.5,
      reviewCount: 128,
      isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
    {
      id: '2',
      title: '치킨 크림 스프',
      description: '부드럽고 진한 크림 스프로 포만감을 주는 키토 요리',
      imageUrl: 'https://via.placeholder.com/300x200?text=치킨+크림+스프',
      cookingTime: 30,
      difficulty: '중간',
      servings: 4,
      ingredients: [
        { name: '닭가슴살', amount: 300, unit: 'g', carbs: 0 },
        { name: '크림', amount: 200, unit: 'ml', carbs: 4 },
        { name: '양파', amount: 1, unit: '개', carbs: 8 },
        { name: '마늘', amount: 3, unit: '쪽', carbs: 1 }
      ],
      instructions: ['닭가슴살을 삶아주세요', '양파와 마늘을 볶아주세요', '크림을 넣고 끓여주세요'],
      nutrition: { calories: 420, carbs: 6, protein: 28, fat: 30, fiber: 2 },
      tags: ['키토', '스프', '저녁', '겨울'],
      rating: 4.8,
      reviewCount: 89,
      isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
    {
      id: '3',
      title: '연어 스테이크',
      description: '오메가3이 풍부한 연어로 만든 고급 키토 요리',
      imageUrl: 'https://via.placeholder.com/300x200?text=연어+스테이크',
      cookingTime: 20,
      difficulty: '중간',
      servings: 2,
      ingredients: [
        { name: '연어 필렛', amount: 400, unit: 'g', carbs: 0 },
        { name: '올리브오일', amount: 3, unit: '큰술', carbs: 0 },
        { name: '레몬', amount: 1, unit: '개', carbs: 3 },
        { name: '허브 솔트', amount: 1, unit: '작은술', carbs: 0 }
      ],
      instructions: ['연어에 허브 솔트를 뿌려주세요', '팬에 올리브오일을 두르고 구워주세요', '레몬즙을 뿌려 완성하세요'],
      nutrition: { calories: 450, carbs: 4, protein: 35, fat: 32, fiber: 1 },
      tags: ['키토', '생선', '저녁', '고급'],
      rating: 4.7,
      reviewCount: 156,
      isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
    {
      id: '4',
      title: '버터 커피',
      description: '키토 다이어터의 필수 아침 음료',
      imageUrl: 'https://via.placeholder.com/300x200?text=버터+커피',
      cookingTime: 5,
      difficulty: '쉬움',
      servings: 1,
      ingredients: [
        { name: '커피', amount: 1, unit: '컵', carbs: 1 },
        { name: '무염버터', amount: 1, unit: '큰술', carbs: 0 },
        { name: 'MCT 오일', amount: 1, unit: '큰술', carbs: 0 }
      ],
      instructions: ['진한 커피를 내려주세요', '버터와 MCT 오일을 넣어주세요', '블렌더로 잘 섞어주세요'],
      nutrition: { calories: 230, carbs: 1, protein: 1, fat: 25, fiber: 0 },
      tags: ['키토', '음료', '아침', '간단'],
      rating: 4.2,
      reviewCount: 234,
      isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
    {
      id: '5',
      title: '치즈 오믈렛',
      description: '푸짐한 치즈가 들어간 고단백 오믈렛',
      imageUrl: 'https://via.placeholder.com/300x200?text=치즈+오믈렛',
      cookingTime: 10,
      difficulty: '쉬움',
      servings: 1,
      ingredients: [
        { name: '계란', amount: 3, unit: '개', carbs: 1 },
        { name: '체다치즈', amount: 50, unit: 'g', carbs: 1 },
        { name: '버터', amount: 1, unit: '큰술', carbs: 0 },
        { name: '소금, 후추', amount: 1, unit: '꼬집', carbs: 0 }
      ],
      instructions: ['계란을 잘 풀어주세요', '팬에 버터를 녹이고 계란을 부어주세요', '치즈를 넣고 접어주세요'],
      nutrition: { calories: 380, carbs: 3, protein: 25, fat: 28, fiber: 0 },
      tags: ['키토', '계란', '아침', '단백질'],
      rating: 4.6,
      reviewCount: 98,
      isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
    {
      id: '6',
      title: '브로콜리 베이컨 볶음',
      description: '아삭한 브로콜리와 고소한 베이컨의 조화',
      imageUrl: 'https://via.placeholder.com/300x200?text=브로콜리+베이컨',
      cookingTime: 12,
      difficulty: '쉬움',
      servings: 2,
      ingredients: [
        { name: '브로콜리', amount: 300, unit: 'g', carbs: 6 },
        { name: '베이컨', amount: 6, unit: '줄', carbs: 0 },
        { name: '마늘', amount: 2, unit: '쪽', carbs: 1 },
        { name: '올리브오일', amount: 2, unit: '큰술', carbs: 0 }
      ],
      instructions: ['브로콜리를 손질해주세요', '베이컨을 먼저 볶아주세요', '브로콜리와 마늘을 넣고 볶아주세요'],
      nutrition: { calories: 280, carbs: 8, protein: 18, fat: 20, fiber: 5 },
      tags: ['키토', '채소', '점심', '저녁'],
      rating: 4.4,
      reviewCount: 67,
      isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
    {
      id: '7',
      title: '아몬드 크러스트 치킨',
      description: '바삭한 아몬드 크러스트로 감싼 육즙 가득한 치킨',
      imageUrl: 'https://via.placeholder.com/300x200?text=아몬드+치킨',
      cookingTime: 35,
      difficulty: '어려움',
      servings: 4,
      ingredients: [
        { name: '닭다리', amount: 4, unit: '개', carbs: 0 },
        { name: '아몬드 가루', amount: 100, unit: 'g', carbs: 4 },
        { name: '파르메산 치즈', amount: 50, unit: 'g', carbs: 1 },
        { name: '계란', amount: 1, unit: '개', carbs: 0 }
      ],
      instructions: ['치킨에 양념을 해주세요', '아몬드 가루와 치즈를 섞어주세요', '오븐에서 구워주세요'],
      nutrition: { calories: 520, carbs: 6, protein: 42, fat: 35, fiber: 3 },
      tags: ['키토', '치킨', '저녁', '오븐'],
      rating: 4.9,
      reviewCount: 145,
      isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
    {
      id: '8',
      title: '그릭 요거트 베리 볼',
      description: '프로틴이 풍부한 그릭 요거트와 신선한 베리',
      imageUrl: 'https://via.placeholder.com/300x200?text=요거트+베리볼',
      cookingTime: 5,
      difficulty: '쉬움',
      servings: 1,
      ingredients: [
        { name: '그릭 요거트', amount: 200, unit: 'g', carbs: 8 },
        { name: '블루베리', amount: 50, unit: 'g', carbs: 7 },
        { name: '아몬드 조각', amount: 20, unit: 'g', carbs: 1 },
        { name: '스테비아', amount: 1, unit: '작은술', carbs: 0 }
      ],
      instructions: ['그릭 요거트를 볼에 담아주세요', '베리와 아몬드를 올려주세요', '스테비아로 단맛을 조절하세요'],
      nutrition: { calories: 220, carbs: 12, protein: 20, fat: 8, fiber: 4 },
      tags: ['키토', '요거트', '간식', '베리'],
      rating: 4.3,
      reviewCount: 78,
      isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
  ]

  // 검색 및 필터링 함수
  const searchRecipes = async (query: string) => {
    setIsSearching(true)
    
    // TODO: 백엔드 연동 시 사용 - 실제 검색 API 호출
    // try {
    //   const searchFilters = {
    //     mealType: mealType || undefined,
    //     difficulty: difficulty || undefined,
    //     isKetoFriendly: true,
    //   }
    //   const results = await searchService.searchRecipes(query, searchFilters)
    //   setFilteredRecipes(results)
    //   console.log('검색 결과:', results)
    // } catch (error) {
    //   console.error('검색 중 오류가 발생했습니다:', error)
    //   setFilteredRecipes([])
    // }
    
    // 현재는 더미 데이터 필터링
    setTimeout(() => {
      let filtered = mockRecipes
      
      if (query.trim()) {
        filtered = filtered.filter(recipe =>
          recipe.title.toLowerCase().includes(query.toLowerCase()) ||
          recipe.description.toLowerCase().includes(query.toLowerCase()) ||
          recipe.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()))
        )
      }
      
      if (mealType) {
        filtered = filtered.filter(recipe =>
          recipe.tags.includes(mealType === 'breakfast' ? '아침' : 
                              mealType === 'lunch' ? '점심' : 
                              mealType === 'dinner' ? '저녁' : 
                              mealType === 'snack' ? '간식' : mealType)
        )
      }
      
      if (difficulty) {
        filtered = filtered.filter(recipe => recipe.difficulty === difficulty)
      }
      
      setFilteredRecipes(filtered)
      setIsSearching(false)
    }, 800) // 검색 지연 시뮬레이션
  }

  // 즐겨찾기 토글 함수
  const handleToggleFavorite = (recipeId: string) => {
    setFavoriteRecipes(prev => {
      const newFavorites = new Set(prev)
      if (newFavorites.has(recipeId)) {
        newFavorites.delete(recipeId)
      } else {
        newFavorites.add(recipeId)
      }
      return newFavorites
    })
    
    // TODO: 백엔드 연동 시 사용 - 즐겨찾기 상태 저장
    // try {
    //   await recipeService.toggleFavorite(recipeId)
    //   console.log('즐겨찾기 상태가 업데이트되었습니다.')
    // } catch (error) {
    //   console.error('즐겨찾기 업데이트 중 오류가 발생했습니다:', error)
    // }
  }

  // 레시피 클릭 핸들러
  const handleRecipeClick = (recipe: Recipe) => {
    setSelectedRecipe(recipe)
    setRecipeDetailOpen(true)
  }

  // 캘린더에 추가 핸들러
  const handleAddToCalendar = () => {
    if (!selectedRecipe) return
    
    // TODO: 백엔드 연동 시 사용 - 캘린더에 추가
    // try {
    //   await mealPlanService.addToCalendar(selectedRecipe.id, selectedDate, selectedMealType)
    //   alert('캘린더에 추가되었습니다!')
    // } catch (error) {
    //   console.error('캘린더 추가 중 오류가 발생했습니다:', error)
    //   alert('캘린더 추가 중 오류가 발생했습니다.')
    // }
    
    alert(`"${selectedRecipe.title}"이(가) 캘린더에 추가되었습니다!`)
    setRecipeDetailOpen(false)
  }

  // 검색 입력 핸들러
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const query = event.target.value
    setSearchQuery(query)
  }

  // 검색 실행 (엔터 키 또는 버튼 클릭)
  const handleSearchSubmit = () => {
    searchRecipes(searchQuery)
  }

  // 키보드 이벤트 핸들러
  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearchSubmit()
    }
  }

  // 초기 데이터 로딩
  useEffect(() => {
    setFilteredRecipes(mockRecipes)
    
    // TODO: 백엔드 연동 시 사용 - 추천 레시피 로딩
    // const loadRecommendedRecipes = async () => {
    //   try {
    //     const recipes = isAuthenticated 
    //       ? await searchService.getRecommendedRecipes(user?.id)
    //       : await searchService.getPopularRecipes()
    //     setFilteredRecipes(recipes)
    //   } catch (error) {
    //     console.error('레시피 로딩 중 오류가 발생했습니다:', error)
    //     setFilteredRecipes(mockRecipes)
    //   }
    // }
    // loadRecommendedRecipes()
  }, [])

  // 필터 변경 시 검색 재실행
  useEffect(() => {
    if (searchQuery || mealType || difficulty) {
      searchRecipes(searchQuery)
    } else {
      setFilteredRecipes(mockRecipes)
    }
  }, [mealType, difficulty])

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
              placeholder="레시피 검색... (예: 아보카도, 치킨, 간단한 요리)"
              value={searchQuery}
              onChange={handleSearchChange}
              onKeyPress={handleKeyPress}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <Button 
                      variant="contained" 
                      size="small"
                      onClick={handleSearchSubmit}
                      disabled={isSearching}
                    >
                      {isSearching ? <CircularProgress size={16} /> : '검색'}
                    </Button>
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
                <MenuItem value="쉬움">쉬움</MenuItem>
                <MenuItem value="중간">중간</MenuItem>
                <MenuItem value="어려움">어려움</MenuItem>
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
        
        {isSearching ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
            <Typography variant="body1" sx={{ ml: 2 }}>
              레시피를 검색하고 있습니다...
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={3}>
            {filteredRecipes.slice(0, isAuthenticated ? (hasSubscription ? filteredRecipes.length : 6) : 6).map((recipe) => (
              <Grid item xs={12} sm={6} md={4} key={recipe.id}>
                <RecipeCard
                  recipe={recipe}
                  variant="default"
                  isFavorite={favoriteRecipes.has(recipe.id)}
                  onRecipeClick={handleRecipeClick}
                  onFavoriteToggle={handleToggleFavorite}
                  showActions={true}
                  actionLabel="레시피 보기"
                />
              </Grid>
            ))}
          </Grid>
        )}
      </Box>

      {/* 검색 결과가 없을 때 */}
      {!isSearching && filteredRecipes.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
            😔 검색 결과가 없습니다
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            다른 키워드로 검색해보시거나 필터를 조정해보세요.
          </Typography>
          <Button 
            variant="outlined" 
            onClick={() => {
              setSearchQuery('')
              setMealType('')
              setDifficulty('')
              setFilteredRecipes(mockRecipes)
            }}
          >
            전체 레시피 보기
          </Button>
        </Box>
      )}

      {/* 더 많은 레시피 로드 버튼 */}
      {!isSearching && filteredRecipes.length > 6 && (
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Button variant="outlined" size="large">
            더 많은 레시피 보기 ({filteredRecipes.length - 6}개 더)
          </Button>
        </Box>
      )}

      {/* 레시피 상세 모달 */}
      <RecipeDetailModal
        open={recipeDetailOpen}
        onClose={() => setRecipeDetailOpen(false)}
        recipe={selectedRecipe}
        isFavorite={selectedRecipe ? favoriteRecipes.has(selectedRecipe.id) : false}
        onToggleFavorite={() => {
          if (selectedRecipe) {
            handleToggleFavorite(selectedRecipe.id)
          }
        }}
        onAddToCalendar={handleAddToCalendar}
      />
    </Box>
  )
}

export default MealsPage
