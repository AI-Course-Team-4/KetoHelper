import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, AuthState } from '../types/index'

interface AuthStore extends AuthState {
  // Actions
  setUser: (user: User) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  login: (user: User) => void
  logout: () => void
  clearError: () => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      setUser: (user: User) =>
        set({
          user,
          isAuthenticated: true,
          error: null,
        }),

      setLoading: (isLoading: boolean) =>
        set({ isLoading }),

      setError: (error: string | null) =>
        set({ error, isLoading: false }),

      login: (user: User) =>
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        }),

      logout: () =>
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        }),

      clearError: () =>
        set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
