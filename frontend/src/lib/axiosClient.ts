import axios from 'axios'
import { useAuthStore } from '@/store/authStore'
import { authService } from '@/services/AuthService';

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
  timeout: 40000,
})

console.log('axiosClient 설정:', {
  API_BASE,
  host: typeof window !== 'undefined' ? window.location.hostname : 'unknown',
  forceProxy,
  isDev,
  finalBaseURL: (isDev || forceProxy || !API_BASE) ? "/api/v1" : `${API_BASE}/api/v1`
});

client.interceptors.request.use((config) => {
  // 단순히 메모리에 있는 토큰만 붙인다. 인증 판정/리다이렉트는 response 401에서만 처리
  const { accessToken } = useAuthStore.getState()
  console.log('🔍 axios request 인터셉터:', {
    url: config.url,
    method: config.method,
    hasAccessToken: !!accessToken,
    tokenLength: accessToken?.length,
    tokenPreview: accessToken ? `${accessToken.substring(0, 20)}...` : 'null'
  })
  
  if (accessToken) {
    // JWT 토큰 만료 시간 확인
    try {
      const payload = JSON.parse(atob(accessToken.split('.')[1]))
      const currentTime = Math.floor(Date.now() / 1000)
      const tokenExp = payload.exp
      const timeUntilExpiry = tokenExp - currentTime
      
      console.log('🔍 토큰 만료 검증:', {
        url: config.url,
        currentTime: new Date(currentTime * 1000).toISOString(),
        tokenExp: new Date(tokenExp * 1000).toISOString(),
        timeUntilExpiry: timeUntilExpiry,
        isExpired: tokenExp < currentTime
      })
    } catch (error) {
      console.log('❌ 토큰 디코딩 실패:', error)
    }
    
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${accessToken}`
    hasLoggedOut = false
    console.log('✅ Authorization 헤더 설정됨:', {
      url: config.url,
      tokenLength: accessToken.length,
      tokenPreview: `${accessToken.substring(0, 20)}...`
    })
  } else {
    console.log('❌ accessToken 없음 - 인증되지 않은 요청:', {
      url: config.url,
      method: config.method
    })
  }
  return config
})


// 토큰 갱신 중인지 확인하는 플래그
let isRefreshing = false
let refreshPromise: Promise<any> | null = null
let hasLoggedOut = false // 중복 로그아웃 방지
let isManualLogout = false // 수동 로그아웃 여부 추적
// 인터셉터 내부에서 사용하는 커스텀 에러 생성기
type HandledError = Error & { _isHandled?: boolean; _suppressToast?: boolean }
const createHandledError = (message: string): HandledError => {
  const e = new Error(message) as HandledError
  e._isHandled = true
  e._suppressToast = true
  return e
}

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    console.log('🔍 axios 인터셉터 에러 처리:', {
      status: error.response?.status,
      url: error.config?.url,
      method: error.config?.method,
      baseURL: error.config?.baseURL,
      fullURL: error.config?.baseURL + error.config?.url,
      headers: error.config?.headers
    })
    const original = error.config
    // 이미 로그아웃 플로우가 진행 중이면 재시도/refresh 금지
    if (hasLoggedOut) {
      return Promise.reject(error)
    }
    
    // 수동 로그아웃 중이면 토스트 표시하지 않음
    if (isManualLogout || (typeof window !== 'undefined' && (window as any).isManualLogout)) {
      return Promise.reject(error)
    }
    
    // 401 에러 처리
    if (error.response?.status === 401 && !original._retry) {
      console.log('🔑 401 에러 감지, 토큰 갱신 시도...')
      original._retry = true
      
      // 401 에러는 여기서 완전히 처리하므로 기본 에러 토스트 방지
      error._isHandled = true
      error._suppressToast = true // 추가 플래그로 토스트 억제
      
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
          // 갱신 실패 시 에러 전달 (토스트 억제)
          return Promise.reject(createHandledError('Token refresh failed'))
        }
      }
      
      // 토큰 갱신 시작
      isRefreshing = true
      refreshPromise = (async () => {
        try {
          console.log('🔑 401 에러 발생, 토큰 갱신 시도...')
          
          const { authService } = await import('@/services/AuthService')
          console.log('🔍 authService.refreshTokens() 호출 전')
          const result = await authService.refreshTokens()
          console.log('🔍 authService.refreshTokens() 결과:', result)
          
          if (result.success && result.accessToken) {
            console.log('✅ 토큰 갱신 성공')
            return result
          } else {
            throw new Error('Token refresh failed')
          }
        } catch (refreshError) {
          console.log('❌ 토큰 갱신 실패, 로그아웃 처리')
          console.log('🔍 refreshError:', refreshError)
          
          // 로그아웃 처리 (한 번만)
          if (!hasLoggedOut) {
            hasLoggedOut = true
            // AuthService에서 토스트와 함께 메모리 초기화
            authService.clearMemory(true)
            
            // 자동 로그아웃 시에도 수동 로그아웃과 동일하게 처리
            const currentPath = typeof window !== 'undefined' ? window.location.pathname : '/'
            if (currentPath !== '/') {
              // 페이지 새로고침 대신 React Router 사용
              if (typeof window !== 'undefined') {
                window.location.href = '/'
                // 추가로 localStorage 완전 초기화
                try {
                  localStorage.removeItem('keto-auth')
                  localStorage.removeItem('keto-coach-profile-v2')
                  localStorage.removeItem('keto-coach-chat-v2')
                  // 플래그들도 초기화
                  hasLoggedOut = false
                } catch {}
              }
            }
          }
          
          // 401 에러를 완전히 처리했으므로 기본 에러 토스트 방지
          return Promise.reject(createHandledError('Session expired'))
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
        // 갱신 실패 시 에러 전달 (토스트 억제)
        return Promise.reject(createHandledError('Token refresh failed'))
      }
    }
    
    // 처리된 에러가 아닌 경우에만 전달
    if (!error._isHandled && !error._suppressToast) {
      return Promise.reject(error)
    }
    
    // 처리된 에러는 컴포넌트에 전달하지 않음
    return Promise.reject(new Error('Request handled by interceptor'))
  }
)

export default client


