import { useState } from 'react'
import { 
  Box, 
  Typography, 
  Grid, 
  Button,
  Alert,
  Paper,
  Card,
  CardContent,
  Chip,
  Avatar,
  Container,
} from '@mui/material'
import { 
  Psychology, 
  Lock, 
  MenuBook,
  AutoAwesome,
  Restaurant,
  Lightbulb,
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import { useAuthStore } from '@store/authStore'
import RecipeDetailModal from '../components/RecipeDetailModal'
import AISearchComponent from '../components/AISearchComponent'
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
  const [favoriteRecipes, setFavoriteRecipes] = useState<Set<string>>(new Set())
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null)
  const [recipeDetailOpen, setRecipeDetailOpen] = useState(false)
  const [aiRecommendedRecipes, setAiRecommendedRecipes] = useState<Recipe[]>([])

  const hasSubscription = user?.subscription?.isActive || false

  const quickPrompts = [
    {
      text: '점심으로 간단하고 빠른 키토 요리 추천해줘',
      icon: <MenuBook />,
      category: '빠른 요리'
    },
    {
      text: '아보카도를 활용한 맛있는 레시피가 뭐가 있을까?',
      icon: <AutoAwesome />,
      category: '재료별'
    },
    {
      text: '저녁에 만들 수 있는 고급스러운 키토 요리',
      icon: <Restaurant />,
      category: '저녁 요리'
    },
    {
      text: '키토 다이어트 초보자도 쉽게 만들 수 있는 요리',
      icon: <Lightbulb />,
      category: '초보자용'
    }
  ]

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
  }

  const handleRecipeSelect = (type: 'recipe' | 'restaurant', item: any) => {
    if (type === 'recipe') {
      setSelectedRecipe(item)
    setRecipeDetailOpen(true)
      // AI가 추천한 레시피를 추천 목록에 추가
      setAiRecommendedRecipes(prev => {
        const exists = prev.find(r => r.id === item.id)
        if (!exists) {
          return [item, ...prev.slice(0, 5)] // 최대 6개까지 유지
        }
        return prev
      })
    }
  }

  return (
    <>
      <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* AI 헤더 섹션 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Box
          sx={{
            background: 'linear-gradient(135deg, #2E7D32 0%, #4CAF50 30%, #FF8F00 100%)',
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
                      🍳 AI 레시피 어시스턴트
                    </Typography>
                    <Chip 
                      label="자연어로 대화하세요" 
                      sx={{ 
                        backgroundColor: 'rgba(255,255,255,0.2)',
                        color: 'white',
                        backdropFilter: 'blur(10px)'
                      }} 
                    />
                  </Box>
                </Box>
                <Typography variant="h6" sx={{ mb: 2, opacity: 0.9, fontWeight: 400 }}>
                  "점심으로 간단한 키토 요리 추천해줘"처럼 자연스럽게 물어보세요
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.8 }}>
                  AI가 당신의 취향과 상황에 맞는 완벽한 키토 레시피를 찾아드립니다
        </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ display: { xs: 'none', md: 'block' }, textAlign: 'center' }}>
                  <Typography variant="h1" sx={{ fontSize: '4rem', opacity: 0.3 }}>
                    🤖
        </Typography>
      </Box>
              </Grid>
            </Grid>
          </Box>
        </Box>
      </motion.div>

      <Grid container spacing={4}>
        {/* AI 대화 메인 영역 */}
        <Grid item xs={12} lg={8}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Card sx={{ 
              borderRadius: 4, 
              boxShadow: '0 12px 40px rgba(0,0,0,0.1)',
              border: '2px solid',
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
                  레시피 AI 어시스턴트
                </Typography>
                <Chip 
                  label="실시간 대화" 
                  size="small" 
                  sx={{ 
                    ml: 'auto',
                    backgroundColor: 'rgba(255,255,255,0.2)',
                    color: 'white',
                    animation: 'pulse 2s infinite'
                  }} 
                />
              </Box>
              <CardContent sx={{ p: 0 }}>
                <AISearchComponent 
                  placeholder="키토 레시피에 대해 무엇이든 물어보세요! 예: '점심으로 빠르게 만들 수 있는 키토 요리 추천해줘'"
                  onResultSelect={handleRecipeSelect}
                  showSuggestions={true}
                />
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        {/* 사이드 패널 */}
        <Grid item xs={12} lg={4}>
          {/* 빠른 질문 제안 */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <Card sx={{ mb: 3, borderRadius: 3 }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  💡 빠른 질문 예시
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
                          backgroundColor: 'primary.light',
                          color: 'white',
                          borderColor: 'primary.main'
                        }
                      }}
                      onClick={() => {
                        console.log('Quick prompt clicked:', prompt.text)
                        // TODO: AI 검색창에 텍스트 입력
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

          {/* AI 추천 레시피 */}
          {aiRecommendedRecipes.length > 0 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              <Card sx={{ mb: 3, borderRadius: 3 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                    🤖 AI가 추천한 레시피
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {aiRecommendedRecipes.slice(0, 3).map((recipe) => (
                      <Button
                        key={recipe.id}
                        variant="outlined"
                        size="small"
                        onClick={() => handleRecipeSelect('recipe', recipe)}
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
                      >
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="body2" sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
                            {recipe.title}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {recipe.cookingTime}분 · {recipe.difficulty}
                          </Typography>
                        </Box>
                      </Button>
                    ))}
      </Box>
                </CardContent>
              </Card>
            </motion.div>
          )}

      {/* 사용자 상태별 안내 */}
      {!isAuthenticated && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.8 }}
            >
              <Alert severity="info" sx={{ mb: 3, borderRadius: 3 }}>
                <Typography variant="body2">
                  로그인하면 개인 선호도를 반영한 맞춤형 AI 추천을 받을 수 있습니다.
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
              transition={{ duration: 0.6, delay: 0.8 }}
            >
              <Paper sx={{ 
                p: 3, 
                mb: 3, 
                background: 'linear-gradient(135deg, #FF8F00 0%, #FFB74D 100%)', 
                color: 'white',
                borderRadius: 3
              }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Lock sx={{ mr: 1 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    AI 프리미엄 기능
            </Typography>
          </Box>
                <Typography variant="body2" sx={{ mb: 2, opacity: 0.9 }}>
                  무제한 AI 대화, 개인 맞춤 식단 플래너, 고급 영양 분석
          </Typography>
          <Button variant="contained" size="small" href="/subscription" sx={{ backgroundColor: 'white', color: 'primary.main' }}>
            프리미엄 구독하기
          </Button>
        </Paper>
            </motion.div>
          )}

          {/* 키토 팁 카드 */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 1.0 }}
          >
            <Card sx={{ borderRadius: 3, background: 'linear-gradient(135deg, #E8F5E8 0%, #F1F8E9 100%)' }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
                  🌟 레시피 팁
                </Typography>
                <Typography variant="body2" sx={{ mb: 2, lineHeight: 1.6 }}>
                  키토 요리할 때 MCT 오일을 추가하면 더 빠른 키토시스 진입에 도움이 됩니다!
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
      />
    </>
  )
}

export default MealsPage
