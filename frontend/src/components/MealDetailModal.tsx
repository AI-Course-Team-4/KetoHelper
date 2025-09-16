import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Grid,
  Chip,
  IconButton,
  Divider,
} from '@mui/material'
import {
  Close,
  AccessTime,
  LocalFireDepartment,
  Edit,
  Restaurant,
  Star,
} from '@mui/icons-material'
import type { Recipe } from '../types/index'

interface MealDetailModalProps {
  open: boolean
  onClose: () => void
  meal: Recipe | null
  mealType: 'breakfast' | 'lunch' | 'dinner'
  onEditRequest: () => void
  isCompleted?: boolean
  onToggleComplete?: () => void
}

const MealDetailModal = ({ 
  open, 
  onClose, 
  meal, 
  mealType, 
  onEditRequest,
  isCompleted = false,
  onToggleComplete
}: MealDetailModalProps) => {
  const mealTypeMap = {
    breakfast: '아침',
    lunch: '점심', 
    dinner: '저녁'
  } as const

  if (!meal) return null

  const handleEditClick = () => {
    onEditRequest()
    onClose()
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Restaurant sx={{ mr: 1 }} />
            <Typography variant="h6">
              {mealTypeMap[mealType]} 식단 상세정보
            </Typography>
          </Box>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        {/* 메인 이미지 */}
        <Box
          component="img"
          src={meal.imageUrl}
          alt={meal.title}
          sx={{
            width: '100%',
            height: 250,
            objectFit: 'cover',
            borderRadius: 2,
            mb: 3,
          }}
        />

        {/* 제목과 완료 상태 */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            {meal.title}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip 
              label={isCompleted ? '완료됨' : '미완료'} 
              color={isCompleted ? 'success' : 'default'}
              size="small"
            />
            {onToggleComplete && (
              <Button
                variant="outlined"
                size="small"
                onClick={onToggleComplete}
              >
                {isCompleted ? '완료 취소' : '완료 처리'}
              </Button>
            )}
          </Box>
        </Box>

        {/* 설명 */}
        <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
          {meal.description}
        </Typography>

        {/* 기본 정보 */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <AccessTime sx={{ fontSize: 20, mr: 1, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">조리시간</Typography>
            </Box>
            <Typography variant="h6">{meal.cookingTime}분</Typography>
          </Grid>
          <Grid item xs={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <LocalFireDepartment sx={{ fontSize: 20, mr: 1, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">칼로리</Typography>
            </Box>
            <Typography variant="h6">{meal.nutrition.calories}kcal</Typography>
          </Grid>
          <Grid item xs={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Star sx={{ fontSize: 20, mr: 1, color: 'warning.main' }} />
              <Typography variant="body2" color="text.secondary">평점</Typography>
            </Box>
            <Typography variant="h6">{meal.rating} ({meal.reviewCount})</Typography>
          </Grid>
        </Grid>

        <Divider sx={{ my: 3 }} />

        {/* 영양 정보 */}
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
          📊 영양 정보
        </Typography>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={3}>
            <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary">탄수화물</Typography>
              <Typography variant="h6" color="warning.main">{meal.nutrition.carbs}g</Typography>
            </Box>
          </Grid>
          <Grid item xs={3}>
            <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary">단백질</Typography>
              <Typography variant="h6" color="success.main">{meal.nutrition.protein}g</Typography>
            </Box>
          </Grid>
          <Grid item xs={3}>
            <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary">지방</Typography>
              <Typography variant="h6" color="info.main">{meal.nutrition.fat}g</Typography>
            </Box>
          </Grid>
          <Grid item xs={3}>
            <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary">식이섬유</Typography>
              <Typography variant="h6" color="primary.main">{meal.nutrition.fiber}g</Typography>
            </Box>
          </Grid>
        </Grid>

        {/* 추가 정보 */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            <strong>난이도:</strong> {meal.difficulty}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            <strong>인분:</strong> {meal.servings}인분
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {meal.tags.map((tag) => (
              <Chip key={tag} label={tag} size="small" variant="outlined" />
            ))}
          </Box>
        </Box>

        {/* TODO: 백엔드 연동 시 사용 - 상세 레시피 정보 */}
        {/* 
        {meal.ingredients && meal.ingredients.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
              🥘 재료
            </Typography>
            <Box sx={{ pl: 2 }}>
              {meal.ingredients.map((ingredient, index) => (
                <Typography key={index} variant="body2" sx={{ mb: 0.5 }}>
                  • {ingredient}
                </Typography>
              ))}
            </Box>
          </Box>
        )}

        {meal.instructions && meal.instructions.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
              📝 조리법
            </Typography>
            <Box sx={{ pl: 2 }}>
              {meal.instructions.map((step, index) => (
                <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                  {index + 1}. {step}
                </Typography>
              ))}
            </Box>
          </Box>
        )}
        */}
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button onClick={onClose} color="inherit">
          닫기
        </Button>
        <Button
          variant="contained"
          startIcon={<Edit />}
          onClick={handleEditClick}
        >
          식단정보변경
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default MealDetailModal
