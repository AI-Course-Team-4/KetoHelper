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
  List,
  ListItem,
  ListItemText,
  Rating,
} from '@mui/material'
import {
  Close,
  AccessTime,
  LocalFireDepartment,
  Star,
  StarBorder,
  Restaurant,
  Schedule,
  Person,
} from '@mui/icons-material'
import type { Recipe } from '../types/index'

interface RecipeDetailModalProps {
  open: boolean
  onClose: () => void
  recipe: Recipe | null
  isFavorite?: boolean
  onToggleFavorite?: () => void
  onAddToCalendar?: () => void
}

const RecipeDetailModal = ({ 
  open, 
  onClose, 
  recipe,
  isFavorite = false,
  onToggleFavorite,
  onAddToCalendar
}: RecipeDetailModalProps) => {

  if (!recipe) return null

  const handleFavoriteClick = () => {
    if (onToggleFavorite) {
      onToggleFavorite()
    }
    
    // TODO: 백엔드 연동 시 사용 - 즐겨찾기 상태 저장
    // try {
    //   await recipeService.toggleFavorite(recipe.id)
    //   console.log('즐겨찾기 상태가 업데이트되었습니다.')
    // } catch (error) {
    //   console.error('즐겨찾기 업데이트 중 오류가 발생했습니다:', error)
    // }
  }

  const handleAddToCalendar = () => {
    if (onAddToCalendar) {
      onAddToCalendar()
    }
    
    // TODO: 백엔드 연동 시 사용 - 캘린더에 추가
    // try {
    //   await mealPlanService.addToCalendar(recipe.id, selectedDate, selectedMealType)
    //   console.log('캘린더에 추가되었습니다.')
    // } catch (error) {
    //   console.error('캘린더 추가 중 오류가 발생했습니다:', error)
    // }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="body"
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Restaurant sx={{ mr: 1 }} />
            <Typography variant="h6">레시피 상세정보</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton 
              onClick={handleFavoriteClick}
              sx={{ color: isFavorite ? 'warning.main' : 'text.secondary', mr: 1 }}
            >
              {isFavorite ? <Star /> : <StarBorder />}
            </IconButton>
            <IconButton onClick={onClose}>
              <Close />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {/* 메인 이미지 */}
        <Box
          component="img"
          src={recipe.imageUrl}
          alt={recipe.title}
          sx={{
            width: '100%',
            height: 300,
            objectFit: 'cover',
          }}
        />

        <Box sx={{ p: 3 }}>
          {/* 제목과 기본 정보 */}
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                  {recipe.title}
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  {recipe.description}
                </Typography>
              </Box>
            </Box>

            {/* 태그와 키토 친화성 */}
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              {recipe.isKetoFriendly && (
                <Chip label="키토 친화적" color="primary" size="small" />
              )}
              {recipe.tags.map((tag) => (
                <Chip key={tag} label={tag} variant="outlined" size="small" />
              ))}
            </Box>

            {/* 평점 */}
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Rating value={recipe.rating} precision={0.1} readOnly size="small" />
              <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                {recipe.rating} ({recipe.reviewCount || 0}개 리뷰)
              </Typography>
            </Box>
          </Box>

          {/* 기본 정보 카드 */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={4}>
              <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'grey.50', borderRadius: 2 }}>
                <AccessTime sx={{ fontSize: 24, color: 'primary.main', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">조리시간</Typography>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {recipe.cookingTime}분
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'grey.50', borderRadius: 2 }}>
                <LocalFireDepartment sx={{ fontSize: 24, color: 'error.main', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">칼로리</Typography>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {recipe.nutrition.calories}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'grey.50', borderRadius: 2 }}>
                <Person sx={{ fontSize: 24, color: 'info.main', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">인분</Typography>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {recipe.servings || 1}인분
                </Typography>
              </Box>
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          {/* 영양 정보 */}
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            📊 영양 정보
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={3}>
              <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'warning.50', borderRadius: 1, border: '1px solid', borderColor: 'warning.200' }}>
                <Typography variant="body2" color="text.secondary">탄수화물</Typography>
                <Typography variant="h6" color="warning.main" sx={{ fontWeight: 600 }}>
                  {recipe.nutrition.carbs}g
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={3}>
              <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'success.50', borderRadius: 1, border: '1px solid', borderColor: 'success.200' }}>
                <Typography variant="body2" color="text.secondary">단백질</Typography>
                <Typography variant="h6" color="success.main" sx={{ fontWeight: 600 }}>
                  {recipe.nutrition.protein}g
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={3}>
              <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'info.50', borderRadius: 1, border: '1px solid', borderColor: 'info.200' }}>
                <Typography variant="body2" color="text.secondary">지방</Typography>
                <Typography variant="h6" color="info.main" sx={{ fontWeight: 600 }}>
                  {recipe.nutrition.fat}g
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={3}>
              <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'primary.50', borderRadius: 1, border: '1px solid', borderColor: 'primary.200' }}>
                <Typography variant="body2" color="text.secondary">식이섬유</Typography>
                <Typography variant="h6" color="primary.main" sx={{ fontWeight: 600 }}>
                  {recipe.nutrition.fiber || 0}g
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {/* TODO: 백엔드 연동 시 사용 - 재료 및 조리법 */}
          {/* 현재는 더미 데이터로 표시 */}
          <Divider sx={{ my: 3 }} />
          
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            🥘 재료 (예시)
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText primary="• 아보카도 1개" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• 올리브오일 2큰술" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• 소금, 후추 약간" />
            </ListItem>
          </List>

          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, mt: 3 }}>
            📝 조리법 (예시)
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText primary="1. 아보카도를 반으로 잘라 씨를 제거합니다." />
            </ListItem>
            <ListItem>
              <ListItemText primary="2. 올리브오일을 뿌리고 소금, 후추로 간을 맞춥니다." />
            </ListItem>
            <ListItem>
              <ListItemText primary="3. 예쁘게 플레이팅하여 완성합니다." />
            </ListItem>
          </List>

          {/* TODO: 백엔드 연동 시 실제 재료 및 조리법 데이터 사용 */}
          {/* 
          {recipe.ingredients && recipe.ingredients.length > 0 && (
            <>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                🥘 재료
              </Typography>
              <List dense>
                {recipe.ingredients.map((ingredient, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={`• ${ingredient}`} />
                  </ListItem>
                ))}
              </List>
            </>
          )}

          {recipe.instructions && recipe.instructions.length > 0 && (
            <>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, mt: 3 }}>
                📝 조리법
              </Typography>
              <List dense>
                {recipe.instructions.map((step, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={`${index + 1}. ${step}`} />
                  </ListItem>
                ))}
              </List>
            </>
          )}
          */}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button onClick={onClose} color="inherit">
          닫기
        </Button>
        <Button
          variant="contained"
          startIcon={<Schedule />}
          onClick={handleAddToCalendar}
        >
          캘린더에 추가
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default RecipeDetailModal
