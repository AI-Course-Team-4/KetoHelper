import {
  Card,
  CardMedia,
  CardContent,
  Typography,
  Box,
  Chip,
  Button,
  IconButton,
} from '@mui/material'
import {
  Star,
  StarBorder,
  AccessTime,
  LocalFireDepartment,
  Add,
  CheckCircle,
  CheckCircleOutline,
} from '@mui/icons-material'
import type { Recipe } from '../types/index'

interface RecipeCardProps {
  recipe?: Recipe | null
  variant?: 'default' | 'compact' | 'add' // add는 + 버튼 카드
  isFavorite?: boolean
  isCompleted?: boolean
  mealType?: 'breakfast' | 'lunch' | 'dinner'
  onRecipeClick?: (recipe: Recipe) => void
  onFavoriteToggle?: (recipeId: string) => void
  onCompletionToggle?: (completed: boolean) => void
  onAddClick?: () => void
  showActions?: boolean
  actionLabel?: string
}

const RecipeCard = ({
  recipe,
  variant = 'default',
  isFavorite = false,
  isCompleted = false,
  mealType,
  onRecipeClick,
  onFavoriteToggle,
  onCompletionToggle,
  onAddClick,
  showActions = true,
  actionLabel = '레시피 보기'
}: RecipeCardProps) => {
  const mealTypeMap = {
    breakfast: '아침',
    lunch: '점심',
    dinner: '저녁'
  } as const

  // + 버튼 카드 (식단이 없을 때)
  if (variant === 'add') {
    return (
      <Card
        sx={{
          height: 200,
          cursor: 'pointer',
          border: 2,
          borderColor: 'primary.main',
          borderStyle: 'dashed',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          '&:hover': {
            backgroundColor: 'action.hover',
            transform: 'translateY(-2px)',
          },
          transition: 'all 0.2s ease-in-out',
        }}
        onClick={onAddClick}
      >
        <CardContent sx={{ textAlign: 'center' }}>
          {mealType && (
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              {mealTypeMap[mealType]}
            </Typography>
          )}
          <IconButton
            size="large"
            sx={{
              backgroundColor: 'primary.main',
              color: 'white',
              mb: 2,
              '&:hover': {
                backgroundColor: 'primary.dark',
              }
            }}
          >
            <Add fontSize="large" />
          </IconButton>
          <Typography variant="body2" color="text.secondary">
            식단을 선택하세요
          </Typography>
        </CardContent>
      </Card>
    )
  }

  // 레시피가 없으면 null 반환
  if (!recipe) return null

  const handleCardClick = () => {
    if (onRecipeClick) {
      onRecipeClick(recipe)
    }
  }

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onFavoriteToggle) {
      onFavoriteToggle(recipe.id)
    }
  }

  const handleCompletionClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onCompletionToggle) {
      onCompletionToggle(!isCompleted)
    }
  }

  // 컴팩트 버전 (캘린더용)
  if (variant === 'compact') {
    return (
      <Card
        sx={{
          height: 120,
          cursor: 'pointer',
          border: 1,
          borderColor: isCompleted ? 'success.main' : 'divider',
          '&:hover': {
            backgroundColor: 'action.hover',
            transform: 'translateY(-1px)',
          },
          transition: 'all 0.2s ease-in-out',
        }}
        onClick={handleCardClick}
      >
        <Box sx={{ display: 'flex', height: '100%' }}>
          {/* 작은 이미지 */}
          <CardMedia
            component="img"
            sx={{ width: 80, flexShrink: 0 }}
            image={recipe.imageUrl}
            alt={recipe.title}
          />
          
          <CardContent sx={{ flex: 1, p: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <Box>
              {mealType && (
                <Typography variant="caption" color="primary.main" sx={{ fontWeight: 600 }}>
                  {mealTypeMap[mealType]}
                </Typography>
              )}
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                {recipe.title}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <AccessTime sx={{ fontSize: 12 }} />
                <Typography variant="caption">{recipe.cookingTime}분</Typography>
                <LocalFireDepartment sx={{ fontSize: 12, ml: 1 }} />
                <Typography variant="caption">{recipe.nutrition.calories}kcal</Typography>
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                {recipe.isKetoFriendly && (
                  <Chip label="키토" size="small" color="primary" sx={{ fontSize: '0.6rem', height: 16 }} />
                )}
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {onCompletionToggle && (
                  <IconButton size="small" onClick={handleCompletionClick}>
                    {isCompleted ? (
                      <CheckCircle color="success" sx={{ fontSize: 16 }} />
                    ) : (
                      <CheckCircleOutline sx={{ fontSize: 16 }} />
                    )}
                  </IconButton>
                )}
                {onFavoriteToggle && (
                  <IconButton size="small" onClick={handleFavoriteClick}>
                    {isFavorite ? (
                      <Star sx={{ color: 'warning.main', fontSize: 16 }} />
                    ) : (
                      <StarBorder sx={{ fontSize: 16 }} />
                    )}
                  </IconButton>
                )}
              </Box>
            </Box>
          </CardContent>
        </Box>
      </Card>
    )
  }

  // 기본 버전 (식단 페이지용)
  return (
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
      onClick={handleCardClick}
    >
      <Box sx={{ position: 'relative' }}>
        <CardMedia
          component="img"
          height="200"
          image={recipe.imageUrl}
          alt={recipe.title}
        />
        {/* 즐겨찾기 버튼 */}
        {onFavoriteToggle && (
          <IconButton
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 1)',
              },
            }}
            onClick={handleFavoriteClick}
          >
            {isFavorite ? (
              <Star sx={{ color: 'warning.main' }} />
            ) : (
              <StarBorder />
            )}
          </IconButton>
        )}

      </Box>

      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        {/* 식사 타입 라벨과 완료 상태 */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          {mealType && (
            <Typography variant="body2" color="primary.main" sx={{ fontWeight: 600 }}>
              {mealTypeMap[mealType]}
            </Typography>
          )}
          {onCompletionToggle && (
            <IconButton size="small" onClick={handleCompletionClick}>
              {isCompleted ? (
                <CheckCircle color="success" sx={{ fontSize: 20 }} />
              ) : (
                <CheckCircleOutline sx={{ fontSize: 20 }} />
              )}
            </IconButton>
          )}
        </Box>

        {/* 키토 친화 뱃지와 태그 */}
        <Box sx={{ display: 'flex', gap: 0.5, mb: 2, flexWrap: 'wrap' }}>
          {recipe.isKetoFriendly && (
            <Chip
              label="키토 친화적"
              size="small"
              color="primary"
            />
          )}
          {recipe.tags.slice(0, 2).map((tag) => (
            <Chip
              key={tag}
              label={tag}
              size="small"
              variant="outlined"
            />
          ))}
        </Box>

        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
          {recipe.title}
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 2,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
          }}
        >
          {recipe.description}
        </Typography>

        {/* 조리 시간, 난이도, 칼로리 */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AccessTime sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {recipe.cookingTime}분
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <LocalFireDepartment sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {recipe.nutrition.calories}kcal
            </Typography>
          </Box>
          <Chip
            label={recipe.difficulty}
            size="small"
            variant="outlined"
            color={recipe.difficulty === '쉬움' ? 'success' : recipe.difficulty === '중간' ? 'warning' : 'error'}
          />
        </Box>

        {/* 영양 정보 */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, fontSize: '0.75rem' }}>
          <Typography variant="caption" color="text.secondary">
            탄수화물 {recipe.nutrition.carbs}g
          </Typography>
          <Typography variant="caption" color="text.secondary">
            단백질 {recipe.nutrition.protein}g
          </Typography>
          <Typography variant="caption" color="text.secondary">
            지방 {recipe.nutrition.fat}g
          </Typography>
        </Box>

        {/* 평점 */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Star sx={{ fontSize: 16, color: 'warning.main', mr: 0.5 }} />
          <Typography variant="body2" sx={{ mr: 1 }}>
            {recipe.rating}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            ({recipe.reviewCount || 0}개 리뷰)
          </Typography>
        </Box>

        {/* 액션 버튼 */}
        {showActions && (
          <Button
            fullWidth
            variant="contained"
            color="primary"
            onClick={(e) => {
              e.stopPropagation()
              handleCardClick()
            }}
          >
            {actionLabel}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

export default RecipeCard
