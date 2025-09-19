import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface AuthUser {
  id: string
  email?: string
  name?: string
  profileImage?: string
}

interface AuthState {
  user: AuthUser | null
  accessToken?: string
  refreshToken?: string
  setAuth: (user: AuthUser, accessToken: string, refreshToken: string) => void
  setAccessToken: (accessToken: string) => void
  clear: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: undefined,
      refreshToken: undefined,
      setAuth: (user, accessToken, refreshToken) => set({ user, accessToken, refreshToken }),
      setAccessToken: (accessToken) => set({ accessToken }),
      clear: () => set({ user: null, accessToken: undefined, refreshToken: undefined }),
    }),
    {
      name: 'keto-auth',
      version: 2,
      // Persist only non-sensitive fields (exclude tokens)
      partialize: (state) => ({ user: state.user }),
      migrate: (persistedState: any, version) => {
        // Drop any previously saved tokens from storage
        if (version < 2 && persistedState && typeof persistedState === 'object') {
          return { user: persistedState.user ?? null }
        }
        // From v2 onward we only keep user in storage
        if (persistedState && typeof persistedState === 'object') {
          return { user: persistedState.user ?? null }
        }
        return { user: null }
      },
    }
  )
)