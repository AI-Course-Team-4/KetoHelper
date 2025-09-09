import { Box, Card, CardContent, Typography, IconButton, Chip, Button, Rating } from '@mui/material'
import { LocationOn, Phone, Favorite, FavoriteBorder } from '@mui/icons-material'
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

// 임시 데이터
export const mockRestaurants: Restaurant[] = [
    {
        id: '1',
        name: '키토 스테이크하우스',
        address: '서울시 강남구 테헤란로 123',
        phone: '02-1234-5678',
        ketoScore: 95,
        distance: 0.8,
        images: ['https://via.placeholder.com/300x200'],
        menu: [
            { name: '립아이 스테이크', price: 45000, carbs: 2, isKetoFriendly: true },
            { name: '연어 그릴', price: 32000, carbs: 1, isKetoFriendly: true },
        ],
    },
    {
        id: '2',
        name: '아보카도 카페',
        address: '서울시 강남구 신사동 456',
        phone: '02-2345-6789',
        ketoScore: 88,
        distance: 1.2,
        images: ['https://via.placeholder.com/300x200'],
        menu: [
            { name: '아보카도 샐러드', price: 15000, carbs: 8, isKetoFriendly: true },
            { name: '키토 커피', price: 6000, carbs: 2, isKetoFriendly: true },
        ],
    },
    {
        id: '3',
        name: '해산물 전문점',
        address: '서울시 강남구 압구정동 789',
        phone: '02-3456-7890',
        ketoScore: 92,
        distance: 2.1,
        images: ['https://via.placeholder.com/300x200'],
        menu: [
            { name: '랍스터 그라탱', price: 68000, carbs: 5, isKetoFriendly: true },
            { name: '새우 샐러드', price: 25000, carbs: 6, isKetoFriendly: true },
        ],
    },
]

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
                    {isFavorite ? (<Favorite color="error" />) : (<FavoriteBorder />)}
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
                    <Typography variant="body2" color="text.secondary">{restaurant.address}{restaurant.distance != null ? ` • ${restaurant.distance}km` : ''}</Typography>
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