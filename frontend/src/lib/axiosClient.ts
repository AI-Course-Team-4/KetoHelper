import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const client = axios.create({ withCredentials: true })

client.interceptors.request.use((config) => {
  const { accessToken } = useAuthStore.getState()
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
      const { refreshToken, setAccessToken, clear } = useAuthStore.getState()
      if (isRefreshing) {
        await new Promise<void>((resolve) => queue.push(resolve))
      } else {
        try {
          isRefreshing = true
          const body = refreshToken ? { refresh_token: refreshToken } : {}
          const res = await axios.post('/api/v1/auth/refresh', body, { withCredentials: true })
          const newAccess = res.data?.accessToken
          if (!newAccess) throw new Error('No access token')
          setAccessToken(newAccess)
          queue.forEach((fn) => fn())
          queue = []
        } catch (e) {
          clear()
          return Promise.reject(e)
        } finally {
          isRefreshing = false
        }
      }
      // 재시도
      const { accessToken } = useAuthStore.getState()
      original.headers = original.headers || {}
      original.headers.Authorization = `Bearer ${accessToken}`
      return client(original)
    }
    return Promise.reject(error)
  }
)

export default client


