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
  const { user, setAuth, clear } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [isInitialized, setIsInitialized] = useState(false)
  
  // 앱 시작 시 토큰 검증 및 갱신 (한 번만 실행)
  useEffect(() => {
    if (isInitialized) return
    
    const initializeAuth = async () => {
      try {
        console.log('🚀 AuthProvider 초기화 시작...')
        const result = await authService.validateAndRefreshTokens()
        console.log('🔍 validateAndRefreshTokens 결과:', result)
        if (result.success && result.user && result.accessToken) {
          // AuthService에서 반환된 데이터로 setAuth 호출
          setAuth(result.user, result.accessToken, result.refreshToken || '')
          
          // 토큰이 유효하면 만료 전 갱신 예약
          authService.scheduleTokenRefresh(result.accessToken)
          console.log('✅ 인증 초기화 완료, 토큰 갱신 예약됨')
        } else {
          console.log('❌ 인증 초기화 실패, 로그인 필요')
        }
      } catch (error) {
        console.error('인증 초기화 실패:', error)
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
