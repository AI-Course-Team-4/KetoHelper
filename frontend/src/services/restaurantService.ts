import { apiHelper } from './api'
import type { Restaurant, RestaurantFilters, PaginatedResponse } from '../types/index'

export const restaurantService = {
  // 식당 목록 조회
  getRestaurants: async (
    page = 1,
    pageSize = 20,
    filters?: RestaurantFilters
  ): Promise<PaginatedResponse<Restaurant>> => {
    const params = new URLSearchParams({
      page: page.toString(),
      pageSize: pageSize.toString(),
    })

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (key === 'location') {
            params.append('lat', value.lat.toString())
            params.append('lng', value.lng.toString())
            params.append('radius', value.radius.toString())
          } else if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()))
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }

    return apiHelper.get<PaginatedResponse<Restaurant>>(`/restaurants?${params.toString()}`)
  },

  // 식당 상세 조회
  getRestaurant: async (id: string): Promise<Restaurant> => {
    return apiHelper.get<Restaurant>(`/restaurants/${id}`)
  },

  // 위치 기반 식당 검색
  getNearbyRestaurants: async (
    lat: number,
    lng: number,
    radius = 5,
    limit = 20
  ): Promise<Restaurant[]> => {
    return apiHelper.get<Restaurant[]>(
      `/restaurants/nearby?lat=${lat}&lng=${lng}&radius=${radius}&limit=${limit}`
    )
  },

  // 식당 검색
  searchRestaurants: async (
    query: string,
    page = 1,
    pageSize = 20,
    filters?: RestaurantFilters
  ): Promise<PaginatedResponse<Restaurant>> => {
    const params = new URLSearchParams({
      q: query,
      page: page.toString(),
      pageSize: pageSize.toString(),
    })

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (key === 'location') {
            params.append('lat', value.lat.toString())
            params.append('lng', value.lng.toString())
            params.append('radius', value.radius.toString())
          } else if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()))
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }

    return apiHelper.get<PaginatedResponse<Restaurant>>(`/restaurants/search?${params.toString()}`)
  },

  // 키토 점수별 식당 조회
  getKetoFriendlyRestaurants: async (
    minScore = 70,
    page = 1,
    pageSize = 20,
    location?: { lat: number; lng: number; radius: number }
  ): Promise<PaginatedResponse<Restaurant>> => {
    const params = new URLSearchParams({
      minScore: minScore.toString(),
      page: page.toString(),
      pageSize: pageSize.toString(),
    })

    if (location) {
      params.append('lat', location.lat.toString())
      params.append('lng', location.lng.toString())
      params.append('radius', location.radius.toString())
    }

    return apiHelper.get<PaginatedResponse<Restaurant>>(`/restaurants/keto-friendly?${params.toString()}`)
  },

  // 카테고리별 식당 조회
  getRestaurantsByCategory: async (
    category: string,
    page = 1,
    pageSize = 20,
    location?: { lat: number; lng: number; radius: number }
  ): Promise<PaginatedResponse<Restaurant>> => {
    const params = new URLSearchParams({
      category,
      page: page.toString(),
      pageSize: pageSize.toString(),
    })

    if (location) {
      params.append('lat', location.lat.toString())
      params.append('lng', location.lng.toString())
      params.append('radius', location.radius.toString())
    }

    return apiHelper.get<PaginatedResponse<Restaurant>>(`/restaurants/category?${params.toString()}`)
  },

  // 식당 즐겨찾기 추가/제거
  toggleFavorite: async (restaurantId: string): Promise<{ isFavorite: boolean }> => {
    return apiHelper.post<{ isFavorite: boolean }>(`/restaurants/${restaurantId}/favorite`)
  },

  // 즐겨찾기 식당 목록
  getFavoriteRestaurants: async (page = 1, pageSize = 20): Promise<PaginatedResponse<Restaurant>> => {
    return apiHelper.get<PaginatedResponse<Restaurant>>(`/restaurants/favorites?page=${page}&pageSize=${pageSize}`)
  },

  // 식당 평점 등록
  rateRestaurant: async (restaurantId: string, rating: number, review?: string): Promise<void> => {
    await apiHelper.post<void>(`/restaurants/${restaurantId}/rating`, { rating, review })
  },

  // 식당 리뷰 조회
  getRestaurantReviews: async (restaurantId: string, page = 1, pageSize = 10) => {
    return apiHelper.get(`/restaurants/${restaurantId}/reviews?page=${page}&pageSize=${pageSize}`)
  },

  // 메뉴 키토 적합성 분석
  analyzeMenu: async (menuImageUrl: string): Promise<{ ketoScore: number; suggestions: string[] }> => {
    return apiHelper.post<{ ketoScore: number; suggestions: string[] }>('/restaurants/analyze-menu', {
      imageUrl: menuImageUrl,
    })
  },

  // 식당 카테고리 목록 조회
  getCategories: async (): Promise<string[]> => {
    return apiHelper.get<string[]>('/restaurants/categories')
  },
}
