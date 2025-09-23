import axios from 'axios'
import { useAuthStore } from '@/store/authStore'
import { shouldRedirectOnTokenExpiry } from './routeUtils'

// JWT 토큰에서 페이로드 추출 (디코딩만, 검증 안함)
function decodeJWTPayload(token: string) {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload))
  } catch {
    return null
  }
}

// useApi.ts와 동일한 baseURL 로직 적용
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, ''); // 끝 슬래시 제거
const isDev = import.meta.env.DEV;

if (!isDev && !API_BASE) {
  // 배포에서 값이 비어 있으면 바로 알 수 있게
  throw new Error('VITE_API_BASE_URL is missing in production build');
}

const client = axios.create({ 
  baseURL: isDev ? "/api/v1" : `${API_BASE}/api/v1`, // dev는 상대경로로 프록시 태움
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

console.log('axiosClient API_BASE =', API_BASE);

client.interceptors.request.use((config) => {
  const { accessToken } = useAuthStore.getState()
  console.log('🚀 API 요청:', {
    url: config.url,
    hasAccessToken: !!accessToken,
    tokenLength: accessToken?.length
  })
  if (accessToken) {
    config.headers = config.headers || {}
    ;(config.headers as any).Authorization = `Bearer ${accessToken}`
  }
  return config
})

let isRefreshing = false
let queue: Array<() => void> = []

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const { refreshToken, accessToken, setAccessToken, clear } = useAuthStore.getState()
      
      console.log('🔑 401 에러 발생, 토큰 상태:', {
        hasAccessToken: !!accessToken,
        hasRefreshToken: !!refreshToken,
        requestUrl: original.url
      })
      
      if (isRefreshing) {
        console.log('⏳ 이미 리프레시 중, 큐에 대기...')
        await new Promise<void>((resolve) => queue.push(resolve))
      } else {
        try {
          isRefreshing = true
          
          if (!refreshToken) {
            console.warn('❌ refreshToken이 없어서 리프레시 불가')
            throw new Error('No refresh token available')
          }
          
          console.log('🔄 토큰 리프레시 시도...')
          const body = { refresh_token: refreshToken }
          const refreshUrl = isDev ? '/api/v1/auth/refresh' : `${API_BASE}/api/v1/auth/refresh`
          
          const res = await axios.post(refreshUrl, body, { 
            withCredentials: true,
            timeout: 10000 // 10초 타임아웃
          })
          
          const newAccess = res.data?.accessToken
          const newRefresh = res.data?.refreshToken
          
          console.log('✅ 토큰 리프레시 성공:', {
            hasNewAccess: !!newAccess,
            hasNewRefresh: !!newRefresh
          })
          
          if (!newAccess) throw new Error('No access token in refresh response')
          
          setAccessToken(newAccess)
          
          // 새 토큰에서 사용자 정보 추출
          const payload = decodeJWTPayload(newAccess)
          const { setAuth, updateUser, user } = useAuthStore.getState()
          
          // 토큰에서 추출한 최신 정보로 사용자 정보 업데이트
          if (payload && user) {
            const updatedUser = {
              ...user,
              name: payload.name || user.name,
              email: payload.email || user.email
            }
            
            // 새로운 refreshToken이 있으면 setAuth로 전체 업데이트
            if (newRefresh) {
              setAuth(updatedUser, newAccess, newRefresh)
            } else {
              // refreshToken이 없으면 사용자 정보만 업데이트
              updateUser({ name: payload.name, email: payload.email })
            }
          } else if (newRefresh && user) {
            // 토큰 디코딩 실패한 경우 기존 로직 유지
            setAuth(user, newAccess, newRefresh)
          }
          
          queue.forEach((fn) => fn())
          queue = []
        } catch (e) {
          console.error('❌ 토큰 리프레시 실패:', e)
          
          // 현재 경로에 따라 리다이렉트 여부 결정
          const currentPath = typeof window !== 'undefined' ? window.location.pathname : '/'
          const shouldRedirect = shouldRedirectOnTokenExpiry(currentPath)
          
          console.log('🚪 로그아웃 처리:', { currentPath, shouldRedirect })
          clear(shouldRedirect)
          
          return Promise.reject(new Error('Authentication failed. Please login again.'))
        } finally {
          isRefreshing = false
        }
      }
      // 재시도
      const { accessToken: newAccessToken } = useAuthStore.getState()
      original.headers = original.headers || {}
      original.headers.Authorization = `Bearer ${newAccessToken}`
      console.log('🔄 요청 재시도:', original.url)
      return client(original)
    }
    return Promise.reject(error)
  }
)

export default client


