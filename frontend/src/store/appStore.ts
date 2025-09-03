import { create } from 'zustand'

interface AppState {
  // UI 상태
  isSidebarOpen: boolean
  isLoading: boolean
  
  // 검색 및 필터 상태
  searchQuery: string
  currentLocation: {
    lat: number
    lng: number
  } | null
  
  // 선택된 아이템들
  selectedRecipes: string[]
  selectedRestaurants: string[]
  
  // Actions
  toggleSidebar: () => void
  setLoading: (loading: boolean) => void
  setSearchQuery: (query: string) => void
  setCurrentLocation: (location: { lat: number; lng: number } | null) => void
  toggleRecipeSelection: (recipeId: string) => void
  toggleRestaurantSelection: (restaurantId: string) => void
  clearSelections: () => void
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  isSidebarOpen: true,
  isLoading: false,
  searchQuery: '',
  currentLocation: null,
  selectedRecipes: [],
  selectedRestaurants: [],

  // Actions
  toggleSidebar: () =>
    set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  setLoading: (isLoading: boolean) =>
    set({ isLoading }),

  setSearchQuery: (searchQuery: string) =>
    set({ searchQuery }),

  setCurrentLocation: (currentLocation: { lat: number; lng: number } | null) =>
    set({ currentLocation }),

  toggleRecipeSelection: (recipeId: string) =>
    set((state) => ({
      selectedRecipes: state.selectedRecipes.includes(recipeId)
        ? state.selectedRecipes.filter((id) => id !== recipeId)
        : [...state.selectedRecipes, recipeId],
    })),

  toggleRestaurantSelection: (restaurantId: string) =>
    set((state) => ({
      selectedRestaurants: state.selectedRestaurants.includes(restaurantId)
        ? state.selectedRestaurants.filter((id) => id !== restaurantId)
        : [...state.selectedRestaurants, restaurantId],
    })),

  clearSelections: () =>
    set({
      selectedRecipes: [],
      selectedRestaurants: [],
    }),
}))
