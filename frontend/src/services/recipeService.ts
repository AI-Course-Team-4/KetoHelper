import { apiHelper } from './api'
import type { Recipe, RecipeFilters, PaginatedResponse, RecommendationRequest, RecommendationResponse } from '../types/index'

export const recipeService = {
  // 레시피 목록 조회
  getRecipes: async (
    page = 1,
    pageSize = 20,
    filters?: RecipeFilters
  ): Promise<PaginatedResponse<Recipe>> => {
    const params = new URLSearchParams({
      page: page.toString(),
      pageSize: pageSize.toString(),
    })

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()))
          } else if (typeof value === 'object' && key === 'calorieRange') {
            params.append('minCalories', value[0].toString())
            params.append('maxCalories', value[1].toString())
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }

    return apiHelper.get<PaginatedResponse<Recipe>>(`/recipes?${params.toString()}`)
  },

  // 레시피 상세 조회
  getRecipe: async (id: string): Promise<Recipe> => {
    return apiHelper.get<Recipe>(`/recipes/${id}`)
  },

  // AI 기반 레시피 추천
  getRecommendations: async (request: RecommendationRequest): Promise<RecommendationResponse> => {
    return apiHelper.post<RecommendationResponse>('/recipes/recommendations', request)
  },

  // 레시피 검색
  searchRecipes: async (
    query: string,
    page = 1,
    pageSize = 20,
    filters?: RecipeFilters
  ): Promise<PaginatedResponse<Recipe>> => {
    const params = new URLSearchParams({
      q: query,
      page: page.toString(),
      pageSize: pageSize.toString(),
    })

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v.toString()))
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }

    return apiHelper.get<PaginatedResponse<Recipe>>(`/recipes/search?${params.toString()}`)
  },

  // 인기 레시피 조회
  getPopularRecipes: async (limit = 10): Promise<Recipe[]> => {
    return apiHelper.get<Recipe[]>(`/recipes/popular?limit=${limit}`)
  },

  // 최근 레시피 조회
  getRecentRecipes: async (limit = 10): Promise<Recipe[]> => {
    return apiHelper.get<Recipe[]>(`/recipes/recent?limit=${limit}`)
  },

  // 사용자 맞춤 레시피 조회
  getPersonalizedRecipes: async (limit = 10): Promise<Recipe[]> => {
    return apiHelper.get<Recipe[]>(`/recipes/personalized?limit=${limit}`)
  },

  // 레시피 즐겨찾기 추가/제거
  toggleFavorite: async (recipeId: string): Promise<{ isFavorite: boolean }> => {
    return apiHelper.post<{ isFavorite: boolean }>(`/recipes/${recipeId}/favorite`)
  },

  // 즐겨찾기 레시피 목록
  getFavoriteRecipes: async (page = 1, pageSize = 20): Promise<PaginatedResponse<Recipe>> => {
    return apiHelper.get<PaginatedResponse<Recipe>>(`/recipes/favorites?page=${page}&pageSize=${pageSize}`)
  },

  // 레시피 평점 등록
  rateRecipe: async (recipeId: string, rating: number, review?: string): Promise<void> => {
    await apiHelper.post<void>(`/recipes/${recipeId}/rating`, { rating, review })
  },

  // 레시피 리뷰 조회
  getRecipeReviews: async (recipeId: string, page = 1, pageSize = 10) => {
    return apiHelper.get(`/recipes/${recipeId}/reviews?page=${page}&pageSize=${pageSize}`)
  },

  // 주간 식단 계획 생성
  generateMealPlan: async (days = 7): Promise<{ mealPlan: Recipe[][] }> => {
    return apiHelper.post<{ mealPlan: Recipe[][] }>('/recipes/meal-plan', { days })
  },

  // 장보기 리스트 생성
  generateShoppingList: async (recipeIds: string[]): Promise<{ ingredients: any[] }> => {
    return apiHelper.post<{ ingredients: any[] }>('/recipes/shopping-list', { recipeIds })
  },
}
