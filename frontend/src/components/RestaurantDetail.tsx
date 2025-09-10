import { Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import { Box, Typography, Grid, Chip, Button, Divider } from '@mui/material'
import { LocationOn, Phone, Star } from '@mui/icons-material'
import type { Restaurant } from './RestaurantCard'

export interface RestaurantDetailProps {
  open: boolean
  onClose: () => void
  restaurant: Restaurant
}

const RestaurantDetail = ({ open, onClose, restaurant }: RestaurantDetailProps) => {
  const primaryImage = restaurant.images?.[0]

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            {restaurant.name}
          </Typography>
          <Chip label={`키토 점수 ${restaurant.ketoScore}`} color="success" size="small" />
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Grid container spacing={3}>
          <Grid item xs={12} md={5}>
            <Box sx={{ width: '100%', height: 220, borderRadius: 1, overflow: 'hidden', mb: 2 }}>
              <Box component="img" src={primaryImage} alt={restaurant.name} sx={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <LocationOn sx={{ fontSize: 18, mr: 0.5, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                {restaurant.address}{restaurant.distance != null ? ` • ${restaurant.distance}km` : ''}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Phone sx={{ fontSize: 18, mr: 0.5, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">{restaurant.phone}</Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={7}>
            {typeof restaurant.rating === 'number' && (
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Star sx={{ fontSize: 18, color: 'warning.main', mr: 0.5 }} />
                <Typography variant="body2" color="text.secondary">
                  {restaurant.rating}{typeof restaurant.reviewCount === 'number' ? ` (${restaurant.reviewCount}개 리뷰)` : ''}
                </Typography>
              </Box>
            )}
            {restaurant.category && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>{restaurant.category}</Typography>
            )}
            <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>대표 메뉴</Typography>
            <Divider sx={{ mb: 1 }} />
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {(restaurant.menu || []).map((m, idx) => (
                <Box key={`${m.name}_${idx}`} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">{m.name}</Typography>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Chip label={`탄수 ${m.carbs}g`} size="small" variant="outlined" />
                    <Typography variant="body2" color="text.secondary">₩{m.price.toLocaleString()}</Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>닫기</Button>
        <Button variant="contained" onClick={onClose}>길찾기</Button>
      </DialogActions>
    </Dialog>
  )
}

export default RestaurantDetail


