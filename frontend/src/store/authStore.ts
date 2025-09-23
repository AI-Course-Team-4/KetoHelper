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
  updateUser: (updates: Partial<AuthUser>) => void
  clear: (shouldRedirect?: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: undefined,
      refreshToken: undefined,
      setAuth: (user, accessToken, refreshToken) => {
        console.log('🔐 setAuth 호출:', {
          user: !!user,
          accessToken: !!accessToken,
          refreshToken: !!refreshToken,
          accessTokenLength: accessToken?.length,
          refreshTokenLength: refreshToken?.length
        });
        set({ user, accessToken, refreshToken });
      },
      setAccessToken: (accessToken) => set({ accessToken }),
      updateUser: (updates) => {
        const currentUser = get().user
        if (currentUser) {
          set({ user: { ...currentUser, ...updates } })
        }
      },
      clear: (shouldRedirect = false) => {
        set({ user: null, accessToken: undefined, refreshToken: undefined })
        // 권한 필요 페이지에서만 리다이렉트
        if (shouldRedirect && typeof window !== 'undefined') {
          window.location.href = '/'
        }
      },
    }),
    {
      name: 'keto-auth',
      version: 4, // 토큰 로딩 문제 해결
      // 보안을 위해 토큰들을 localStorage가 아닌 sessionStorage 사용하거나
      // 또는 HttpOnly 쿠키를 통해서만 관리하는 것이 더 좋지만,
      // 현재 구조를 유지하면서 개선
      partialize: (state) => ({ 
        user: state.user,
        accessToken: state.accessToken, // 임시로 accessToken도 저장
        refreshToken: state.refreshToken
      }),
      migrate: (persistedState: any, version) => {
        console.log('🔄 Zustand 마이그레이션 실행:', { version, persistedState });
        
        if (persistedState && typeof persistedState === 'object') {
          // state.user 형태로 저장된 경우와 직접 저장된 경우 모두 처리
          const state = persistedState.state || persistedState;
          
          const migrated = {
            user: state.user ?? null,
            accessToken: state.accessToken,
            refreshToken: state.refreshToken
          };
          
          console.log('✅ 마이그레이션 결과:', migrated);
          return migrated;
        }
        
        console.log('❌ 마이그레이션 실패, 초기화');
        return { user: null, accessToken: undefined, refreshToken: undefined }
      },
    }
  )
)