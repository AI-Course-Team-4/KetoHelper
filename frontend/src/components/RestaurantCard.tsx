import { Box, Card, CardContent, Typography, IconButton, Chip, Button, Rating } from '@mui/material'
import { LocationOn, Phone, Star, StarBorder } from '@mui/icons-material'
import { useState } from 'react'
import RestaurantDetail from './RestaurantDetail'

type MenuItem = {
    name: string
    price: number
    carbs: number
    isKetoFriendly: boolean
}

export type Restaurant = {
    id: string
    name: string
    address: string
    phone: string
    images: string[]
    distance?: number
    ketoScore: number
    rating?: number
    reviewCount?: number
    priceRange?: number
    category?: string
    menu: MenuItem[]
}

export interface RestaurantCardProps {
    restaurant: Restaurant
    isFavorite: boolean
    onToggleFavorite: (id: string) => void
}

function getKetoScoreColor(score: number): 'success' | 'warning' | 'error' {
    if (score >= 90) return 'success'
    if (score >= 70) return 'warning'
    return 'error'
}

const RestaurantCard = ({ restaurant, isFavorite, onToggleFavorite }: RestaurantCardProps) => {
    const primaryImage = restaurant.images?.[0]

    const [detailOpen, setDetailOpen] = useState(false)
    const [selected, setSelected] = useState<Restaurant | null>(null)

    return (
        <Card
            sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'stretch',
                p: 1,
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                '&:hover': { transform: 'translateY(-2px)', boxShadow: 4 },
            }}
        >
            <Box sx={{ position: 'relative', width: '100%', height: 200, borderRadius: 1, overflow: 'hidden' }}>
                <Box component="img" src={primaryImage} alt={restaurant.name} sx={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                <IconButton
                    onClick={(e) => { e.stopPropagation(); onToggleFavorite(restaurant.id) }}
                    sx={{ position: 'absolute', top: 8, right: 8, backgroundColor: 'rgba(255,255,255,0.9)', '&:hover': { backgroundColor: 'rgba(255,255,255,1)' } }}
                >
                    {isFavorite ? (<Star sx={{ color: '#fbbc05' }} />) : (<StarBorder />)}
                </IconButton>
                <Chip label={`키토 ${restaurant.ketoScore}`} color={getKetoScoreColor(restaurant.ketoScore)} size="small" sx={{ position: 'absolute', bottom: 8, left: 8, backgroundColor: 'rgba(255,255,255,0.95)' }} />
            </Box>
            <CardContent sx={{ flex: 1, p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>{restaurant.name}</Typography>
                </Box>
                {restaurant.category && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{restaurant.category}</Typography>
                )}
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <LocationOn sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">{restaurant.address}</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Phone sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">{restaurant.phone}</Typography>
                </Box>
                {typeof restaurant.rating === 'number' && (
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Rating value={restaurant.rating} precision={0.1} size="small" readOnly />
                        {typeof restaurant.reviewCount === 'number' && (
                            <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                                {restaurant.rating} ({restaurant.reviewCount}개 리뷰)
                            </Typography>
                        )}
                    </Box>
                )}
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>추천 키토 메뉴</Typography>
                {(restaurant.menu || []).slice(0, 2).map((menuItem, index) => (
                    <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="body2">{menuItem.name}</Typography>
                        <Typography variant="body2" color="text.secondary">₩{menuItem.price.toLocaleString()}</Typography>
                    </Box>
                ))}
                <Button variant="outlined" color="primary" sx={{ mt: 1, width: '100%' }} onClick={() => { setSelected(restaurant); setDetailOpen(true) }}>상세 정보 보기</Button>
                {selected && <RestaurantDetail open={detailOpen} onClose={() => setDetailOpen(false)} restaurant={selected} />}
            </CardContent>
        </Card>
    )
}

export default RestaurantCard