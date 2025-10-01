import { createContext, useContext, ReactNode, useEffect, useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import { authService } from '@/services/AuthService'

interface AuthContextType {
  user: any
  loading: boolean
  login: (user: any, accessToken: string, refreshToken: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { user, setAuth, clear, ensureGuestId } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [isInitialized, setIsInitialized] = useState(false)
  
  // 앱 시작 시 토큰 검증 및 갱신 (한 번만 실행)
  useEffect(() => {
    if (isInitialized) return
    
    const initializeAuth = async () => {
      try {
        console.log('🚀 AuthProvider 초기화 시작...')
        
        // 게스트 사용자인지 확인 (isGuest 상태 확인)
        const authData = localStorage.getItem('keto-auth')
        let isGuest = true
        
        if (authData) {
          try {
            const parsed = JSON.parse(authData)
            isGuest = parsed.state?.isGuest !== false
          } catch (e) {
            console.error('Auth 데이터 파싱 실패:', e)
            isGuest = true
          }
        } else {
          // localStorage에 auth 데이터가 없으면 게스트 사용자
          console.log('🔍 localStorage에 auth 데이터 없음 - 게스트 사용자로 설정')
          isGuest = true
        }
        
        if (isGuest) {
          console.log('🕊️ 게스트 사용자 - 토큰 검증 스킵')
          // 게스트 사용자 ID 보장
          const guestId = ensureGuestId()
          console.log('🎭 게스트 사용자 ID 보장:', guestId)
          
          // 게스트 상태를 강제로 설정 (ensureGuestId가 이미 isGuest: true로 설정함)
          console.log('🔍 게스트 상태 설정 완료')
          return
        }
        
        console.log('🔍 AuthContext: 로그인 사용자 - 토큰 검증 진행')
        
        const result = await authService.validateAndRefreshTokens()
        console.log('🔍 validateAndRefreshTokens 결과:', result)
        
        if (result.success && result.user && result.accessToken) {
          console.log('✅ 토큰 검증 성공, 사용자 정보 설정 중...')
          // AuthService에서 반환된 데이터로 setAuth 호출
          setAuth(result.user, result.accessToken, result.refreshToken || '')
          
          // 토큰이 유효하면 만료 전 갱신 예약
          authService.scheduleTokenRefresh(result.accessToken)
          console.log('✅ 인증 초기화 완료, 토큰 갱신 예약됨')
        } else {
          console.log('❌ 인증 초기화 실패, 로그인 필요')
          console.log('🔍 실패 이유:', { success: result.success, hasUser: !!result.user, hasToken: !!result.accessToken })
        }
      } catch (error) {
        console.error('❌ 인증 초기화 실패:', error)
      } finally {
        setLoading(false)
        setIsInitialized(true)
      }
    }

    initializeAuth()
  }, [isInitialized])
  
  const login = (user: any, accessToken: string, refreshToken: string) => {
    // 메모리에 저장
    authService.setUser(user)
    authService.setAccessToken(accessToken)
    authService.setRefreshToken(refreshToken)
    
    // Zustand store에도 저장 (UI 상태 관리용)
    setAuth(user, accessToken, refreshToken)
    
    // 토큰 갱신 예약
    authService.scheduleTokenRefresh(accessToken)
    
    console.log('✅ 로그인 완료, 메모리 및 store에 저장됨')
  }
  
  const logout = () => {
    // 메모리 초기화
    authService.clearMemory()
    
    // Zustand store 초기화
    clear(true) // shouldRedirect = true
    
    console.log('🚪 로그아웃 완료, 메모리 및 store 초기화됨')
  }
  
  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
