import axios from 'axios'
import { useAuthStore } from '@/store/authStore'
import { commonToasts } from '@/lib/toast'

// useApi.ts와 동일한 baseURL 로직 적용
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, ''); // 끝 슬래시 제거
// 배포 도메인(예: *.vercel.app)에서는 강제로 프록시(/api/v1) 사용
const host = (typeof window !== 'undefined' ? window.location.hostname : '')
const forceProxy = /vercel\.app$/.test(host)
const isDev = import.meta.env.DEV;

// 배포에서도 상대경로(/api/v1)로 프록시 태우는 전략을 허용

const client = axios.create({ 
  baseURL: (isDev || forceProxy || !API_BASE) ? "/api/v1" : `${API_BASE}/api/v1`,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

console.log('axiosClient API_BASE =', API_BASE);

client.interceptors.request.use((config) => {
  // 단순히 메모리에 있는 토큰만 붙인다. 인증 판정/리다이렉트는 response 401에서만 처리
  const { accessToken } = useAuthStore.getState()
  if (accessToken) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${accessToken}`
    toastShown = false
    hasLoggedOut = false
  }
  return config
})


// 토큰 갱신 중인지 확인하는 플래그
let isRefreshing = false
let refreshPromise: Promise<any> | null = null
let toastShown = false // 토스트 표시 여부 추적
let hasLoggedOut = false // 중복 로그아웃 방지

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    console.log('🔍 axios 인터셉터 에러 처리:', error.response?.status, error.config?.url)
    const original = error.config
    // 이미 로그아웃 플로우가 진행 중이면 재시도/refresh 금지
    if (hasLoggedOut) {
      return Promise.reject(error)
    }
    
    // 401 에러 처리
    if (error.response?.status === 401 && !original._retry) {
      console.log('🔑 401 에러 감지, 토큰 갱신 시도...')
      original._retry = true
      
      // 이미 갱신 중이면 기존 Promise 대기
      if (isRefreshing && refreshPromise) {
        try {
          await refreshPromise
          // 갱신 완료 후 원래 요청 재시도
          const { accessToken } = useAuthStore.getState()
          if (accessToken) {
            original.headers = original.headers || {}
            original.headers.Authorization = `Bearer ${accessToken}`
            return client(original)
          }
        } catch (refreshError) {
          // 갱신 실패 시 에러 전달
          return Promise.reject(error)
        }
      }
      
      // 토큰 갱신 시작
      isRefreshing = true
      refreshPromise = (async () => {
        try {
          console.log('🔑 401 에러 발생, 토큰 갱신 시도...')
          
          const { authService } = await import('@/services/AuthService')
          const result = await authService.refreshTokens()
          
          if (result.success && result.accessToken) {
            console.log('✅ 토큰 갱신 성공')
            return result
          } else {
            throw new Error('Token refresh failed')
          }
        } catch (refreshError) {
          console.log('❌ 토큰 갱신 실패, 로그아웃 처리')
          
          // 토큰 만료 토스트 표시 (로그인 상태였던 경우에만, 한 번만)
          const { user } = useAuthStore.getState()
          if (user && !toastShown) {
            commonToasts.sessionExpired()
            toastShown = true
          }
          
          // 로그아웃 처리 (한 번만)
          if (!hasLoggedOut) {
            hasLoggedOut = true
            // 로그인된 상태였던 경우에만 1회성 토스트 플래그 저장
            try {
              const { user } = useAuthStore.getState()
              if (user) sessionStorage.setItem('session-expired', '1')
            } catch {}
            const currentPath = typeof window !== 'undefined' ? window.location.pathname : '/'
            if (currentPath !== '/') {
              window.location.href = '/'
            }
          }
          
          throw refreshError
        } finally {
          isRefreshing = false
          refreshPromise = null
        }
      })()
      
      try {
        await refreshPromise
        // 갱신 성공 시 원래 요청 재시도
        const { accessToken } = useAuthStore.getState()
        if (accessToken) {
          original.headers = original.headers || {}
          original.headers.Authorization = `Bearer ${accessToken}`
          console.log('🔄 요청 재시도:', original.url)
          return client(original)
        }
      } catch (refreshError) {
        return Promise.reject(error)
      }
    }
    
    return Promise.reject(error)
  }
)

export default client


