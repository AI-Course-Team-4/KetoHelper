import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { v4 as uuidv4 } from 'uuid'

export interface AuthUser {
  id: string
  email?: string
  name?: string
  profileImage?: string
  socialNickname?: string
}

interface AuthState {
  user: AuthUser | null
  accessToken?: string
  refreshToken?: string
  guestId: string // 게스트 ID 추가
  isGuest: boolean // 게스트 여부 확인
  setAuth: (user: AuthUser, accessToken: string, refreshToken: string) => void
  setAccessToken: (accessToken: string) => void
  updateUser: (updates: Partial<AuthUser>) => void
  clear: (shouldRedirect?: boolean) => void
  ensureGuestId: () => string // 게스트 ID 생성/조회 함수 추가
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: undefined,
      refreshToken: undefined,
      guestId: '', // 게스트 ID 초기화
      isGuest: false, // 게스트 여부 초기화
      setAuth: (user, accessToken, refreshToken) => {
        console.log('🔐 setAuth 호출:', {
          user: !!user,
          accessToken: !!accessToken,
          refreshToken: !!refreshToken,
          accessTokenLength: accessToken?.length,
          refreshTokenLength: refreshToken?.length
        });
        // 저장되는 사용자 정보 확인용 상세 로그
        try {
          console.log('👤 setAuth user detail:', {
            id: user?.id,
            email: user?.email,
            name: user?.name,
            profileImage: user?.profileImage,
          })
        } catch {}
        set({ user, accessToken, refreshToken, isGuest: false });
      },
      setAccessToken: (accessToken) => set({ accessToken }),
      updateUser: (updates) => {
        const currentUser = get().user
        if (currentUser) {
          set({ user: { ...currentUser, ...updates } })
        }
      },
      clear: (shouldRedirect = false) => {
        console.log('🚪 authStore.clear() 호출')
        set({ user: null, accessToken: undefined, refreshToken: undefined, isGuest: false })
        
        // ProfileStore도 함께 클리어 (다른 사용자 프로필 데이터 방지)
        if (typeof window !== 'undefined') {
          // Zustand persist 스토리지에서 프로필 데이터 클리어
          localStorage.removeItem('keto-coach-profile-v2')
          console.log('🗑️ 프로필 캐시 삭제 완료')
        }
        
        // 권한 필요 페이지에서만 리다이렉트
        if (shouldRedirect && typeof window !== 'undefined') {
          window.location.href = '/'
        }
      },
      // 게스트 ID 생성/조회 함수 추가
      ensureGuestId: () => {
        const state = get()
        let guestId = state.guestId
        
        // 게스트 ID가 없으면 새로 생성
        if (!guestId) {
          guestId = uuidv4()
          console.log('🎭 새 게스트 ID 생성:', guestId)
          set({ guestId, isGuest: true })
        }
        
        return guestId
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
        refreshToken: state.refreshToken,
        guestId: state.guestId, // 게스트 ID도 저장
        isGuest: state.isGuest // 게스트 여부도 저장
      }),
      migrate: (persistedState: any, version) => {
        console.log('🔄 Zustand 마이그레이션 실행:', { version, persistedState });
        
        if (persistedState && typeof persistedState === 'object') {
          // state.user 형태로 저장된 경우와 직접 저장된 경우 모두 처리
          const state = persistedState.state || persistedState;
          
          const migrated = {
            user: state.user ?? null,
            accessToken: state.accessToken,
            refreshToken: state.refreshToken,
            guestId: state.guestId ?? '',
            isGuest: state.isGuest ?? false
          };
          
          console.log('✅ 마이그레이션 결과:', migrated);
          return migrated;
        }
        
        console.log('❌ 마이그레이션 실패, 초기화');
        return { user: null, accessToken: undefined, refreshToken: undefined, guestId: '', isGuest: false }
      },
    }
  )
)