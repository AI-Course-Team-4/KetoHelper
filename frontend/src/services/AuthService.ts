import { useAuthStore } from '@/store/authStore'
import axios from 'axios'
import { api } from '@/hooks/useApi'

// User 타입 정의
interface User {
  id: string
  email: string
  name: string
  profileImage?: string
}

class AuthService {
  private isRefreshing = false
  private refreshPromise: Promise<any> | null = null
  private scheduledRefresh: NodeJS.Timeout | null = null
  private hasShownExpiryToast = false
  
  // 클라이언트 표시용 로그인 세션 플래그 (HttpOnly RT 유무를 대체 판단)
  private setLoginSessionFlag(on: boolean) {
    try {
      if (on) sessionStorage.setItem('has-login-session', '1')
      else sessionStorage.removeItem('has-login-session')
    } catch {}
  }
  private hasLoginSessionFlag(): boolean {
    try { return sessionStorage.getItem('has-login-session') === '1' } catch { return false }
  }
  
  // 메모리에 저장 (페이지 새로고침 시 초기화됨)
  private accessToken: string | null = null
  private refreshToken: string | null = null
  private user: User | null = null

  // Access Token을 메모리에만 저장 (보안상 localStorage 사용 안함)
  setAccessToken(token: string) {
    this.accessToken = token
    console.log('💾 Access Token을 메모리에만 저장 (localStorage 사용 안함)')
  }

  // Access Token을 메모리에서 가져오기
  getAccessToken(): string | null {
    return this.accessToken
  }

  // Refresh Token을 메모리에 저장
  setRefreshToken(token: string) {
    this.refreshToken = token
  }

  // Refresh Token을 메모리에서 가져오기
  getRefreshToken(): string | null {
    return this.refreshToken
  }

  // 사용자 정보를 메모리에 저장
  setUser(user: User) {
    this.user = user
  }

  // 사용자 정보를 메모리에서 가져오기
  getUser(): User | null {
    return this.user
  }

  // 메모리 초기화
  clearMemory() {
    this.accessToken = null
    this.refreshToken = null
    this.user = null
    console.log('🧹 메모리 초기화 완료')
    // 로그인 세션 플래그 제거
    this.setLoginSessionFlag(false)
  }

  // 개발용: 토큰 만료 테스트
  simulateTokenExpiry() {
    console.log('🧪 토큰 만료 시뮬레이션 시작...')
    this.accessToken = null
    console.log('🧪 accessToken 삭제 완료, 새로고침하면 refresh가 실행됩니다')
  }

  async validateAndRefreshTokens() {
    // 메모리에서 accessToken 확인
    const accessToken = this.getAccessToken()
    
    // HttpOnly 쿠키는 JavaScript에서 읽을 수 없음
    // refresh_token은 백엔드에서 자동으로 처리됨
    
    // accessToken이 있으면 유효성 검사
    if (accessToken) {
      try {
        // 토큰 만료 시간 검증
        if (this.isTokenExpired(accessToken)) {
          console.log('⏰ accessToken 만료됨, refresh 시도')
          return await this.refreshTokens()
        }
        
        // 토큰에서 사용자 정보 추출
        const payload = this.decodeJWTPayload(accessToken)
        if (payload && payload.sub) {
          console.log('✅ accessToken 유효, 사용자 정보 복원')
          const user = {
            id: payload.sub,
            email: payload.email || '',
            name: payload.name || '',
            profileImage: payload.profile_image || payload.profileImage || ''
          }
          this.setUser(user)
          this.setAccessToken(accessToken)
          return { success: true, user, accessToken: accessToken, refreshToken: '' }
        } else {
          throw new Error('토큰에서 사용자 정보 추출 실패')
        }
      } catch (error) {
        console.log('❌ accessToken 무효, refresh 시도')
        return await this.refreshTokens()
      }
    } else {
      // accessToken이 없으면: 로그인 세션 플래그가 있을 때만 refresh 시도
      if (!this.hasLoginSessionFlag()) {
        console.log('🔕 accessToken 없음 + 세션 플래그 없음 → refresh 스킵')
        return { success: false, user: null, accessToken: null, refreshToken: null }
      }
      console.log('🔄 accessToken 없음, (세션 플래그 O) refresh 시도...')
      return await this.refreshTokens()
    }
  }

  async refreshTokens(): Promise<{ success: boolean; user: any; accessToken: string | null; refreshToken: string | null }> {
    // 이미 갱신 중이면 기존 Promise 반환
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise
    }

    this.isRefreshing = true
    this.refreshPromise = this.performRefresh()

    try {
      const result = await this.refreshPromise
      return result
    } finally {
      this.isRefreshing = false
      this.refreshPromise = null
    }
  }

  private async performRefresh(): Promise<{ success: boolean; user: any; accessToken: string | null; refreshToken: string | null }> {
    try {
      console.log('🔄 쿠키 기반 토큰 갱신 시도...')
      const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const fullURL = `${baseURL}/api/v1/auth/refresh`
      console.log('🔍 API 호출 URL:', fullURL)
      console.log('🔍 withCredentials: true')
      console.log('🔍 현재 쿠키:', document.cookie)
      console.log('🔍 baseURL:', baseURL)
      console.log('🔍 VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL)
      
      const res = await axios.post('/api/v1/auth/refresh', {}, {
        withCredentials: true,
        baseURL: baseURL
      })
      console.log('🔍 refresh API 응답:', res.data)
      console.log('🔍 refresh API 상태:', res.status)
      const { accessToken: newAccess, refreshToken: newRefresh, user } = res.data
      
      if (newAccess) {
        console.log('✅ 토큰 갱신 성공')
        console.log('🔍 갱신된 사용자 정보:', user)
        
        // 백엔드 응답의 profile_image를 profileImage로 변환
        const normalizedUser = {
          ...user,
          profileImage: user.profile_image || user.profileImage || ''
        }
        console.log('🔍 정규화된 사용자 정보:', normalizedUser)
        
        // 메모리에 저장
        this.setAccessToken(newAccess)
        this.setRefreshToken(newRefresh)
        this.setUser(normalizedUser)
        this.setLoginSessionFlag(true)

        // 전역 스토어 동기화 (axios 인터셉터에서 최신 토큰 사용)
        try {
          const { setAuth } = useAuthStore.getState()
          setAuth(normalizedUser as any, newAccess, newRefresh || '')
        } catch (e) {
          console.warn('useAuthStore.setAuth 동기화 실패:', e)
        }
        
        return { success: true, user: normalizedUser, accessToken: newAccess, refreshToken: newRefresh }
      } else {
        throw new Error('토큰 갱신 실패')
      }
    } catch (refreshError: any) {
      console.log('❌ 토큰 갱신 실패, 로그아웃')
      console.log('🔍 에러 상세:', refreshError)
      console.log('🔍 에러 응답:', refreshError.response?.data)
      console.log('🔍 에러 상태:', refreshError.response?.status)
      
      // 설계에 따라: RT 만료 = 세션 종료
      // 메모리 초기화
      this.clearMemory()
      
      // Zustand store 상태도 초기화
      const { clear } = useAuthStore.getState()
      clear(false) // 리다이렉트는 axios 인터셉터에서 처리
      
      // 페이지 진입 시 한 번만 토스트를 띄우기 위해 플래그만 설정
      try {
        sessionStorage.setItem('session-expired', '1')
      } catch {}
      
      return { success: false, user: null, accessToken: null, refreshToken: null }
    }
  }

  // HttpOnly 쿠키는 JavaScript에서 읽을 수 없음
  // Refresh Token은 백엔드에서 자동으로 처리됨
  private getCookieValue(name: string): string | null {
    // HttpOnly 쿠키는 document.cookie로 읽을 수 없음
    console.log('🍪 HttpOnly 쿠키는 JavaScript에서 읽을 수 없습니다:', name)
    return null
  }

  // JWT 토큰 디코딩
  private decodeJWTPayload(token: string) {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
      return JSON.parse(jsonPayload)
    } catch (error) {
      console.error('JWT 디코딩 실패:', error)
      return null
    }
  }

  // 토큰 만료 시간 검증
  private isTokenExpired(token: string): boolean {
    try {
      const payload = this.decodeJWTPayload(token)
      if (!payload || !payload.exp) return true
      
      const currentTime = Math.floor(Date.now() / 1000)
      return payload.exp < currentTime
    } catch (error) {
      console.error('토큰 만료 검증 실패:', error)
      return true
    }
  }

  // 토큰 만료 전 갱신 예약
  scheduleTokenRefresh(accessToken: string) {
    // 기존 예약이 있으면 취소
    if (this.scheduledRefresh) {
      clearTimeout(this.scheduledRefresh)
      this.scheduledRefresh = null
    }
    
    try {
      const payload = this.decodeJWTPayload(accessToken)
      if (!payload) return
      
      const exp = payload.exp * 1000 // 밀리초로 변환
      const now = Date.now()
      const timeUntilExpiry = exp - now
      
      // 만료 5분 전에 갱신
      const refreshTime = Math.max(timeUntilExpiry - 5 * 60 * 1000, 0)
      
      if (refreshTime > 0) {
        console.log(`⏰ 토큰 갱신 예약: ${Math.round(refreshTime / 1000)}초 후`)
        this.scheduledRefresh = setTimeout(() => {
          this.validateAndRefreshTokens()
        }, refreshTime)
      }
    } catch (error) {
      console.warn('토큰 만료 시간 파싱 실패:', error)
    }
  }

  // 중앙 토큰 검증 및 갱신 (API 호출 전에 호출)
  async checkTokenAndRefresh(): Promise<boolean> {
    const accessToken = this.getAccessToken()
    
    if (!accessToken) {
      if (!this.hasLoginSessionFlag()) {
        console.log('🔕 accessToken 없음 + 세션 플래그 없음 → refresh 스킵')
        return false
      }
      console.log('🔄 accessToken 없음, (세션 플래그 O) refresh 시도...')
      const result = await this.refreshTokens()
      return result.success
    }

    // 토큰 만료 시간 검증
    if (this.isTokenExpired(accessToken)) {
      console.log('⏰ accessToken 만료됨, refresh 시도')
      const result = await this.refreshTokens()
      return result.success
    }

    return true
  }
}

export const authService = new AuthService()
