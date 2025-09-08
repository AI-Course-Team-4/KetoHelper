import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import type { ApiResponse, ApiError } from '../types/index'

// API 기본 설정
const API_BASE_URL = (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000'

// Axios 인스턴스 생성
export const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    // 토큰이 있으면 헤더에 추가
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 요청 로깅 (dev 모드에서만)
    if ((import.meta as any).env.VITE_DEV_MODE === 'true') {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    }
    
    return config
  },
  (error) => {
    console.error('[API] Request error:', error)
    return Promise.reject(error)
  }
)

// 응답 인터셉터
api.interceptors.response.use(
  (response: AxiosResponse<ApiResponse<any>>) => {
    // 응답 로깅 (dev 모드에서만)
    if ((import.meta as any).env.VITE_DEV_MODE === 'true') {
      const url = response.config?.url || ''
      const raw = (response as any)?.data
      const data = (raw as any)?.data ?? raw
      console.log('data', data)
      if (url.endsWith('/auth/google')) {
        console.log('[API] Google login user:', data?.user ?? null)
      } else {
        console.log(`[API] Response ${response.status}:`, raw)
      }
    }
    return response
  },
  (error) => {
    // 에러 로깅
    console.error('[API] Response error:', error)
    
    // 401 에러시 로그아웃 처리
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('auth-storage')
      window.location.href = '/login'
    }
    
    // API 에러 형식으로 변환
    const apiError: ApiError = {
      code: error.response?.data?.code || 'UNKNOWN_ERROR',
      message: error.response?.data?.message || error.message || '알 수 없는 오류가 발생했습니다.',
      details: error.response?.data?.details,
    }
    
    return Promise.reject(apiError)
  }
)

// API 헬퍼 함수들
export const apiHelper = {
  get: async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    const response = await api.get<ApiResponse<T>>(url, config)
    return (response as any).data?.data
  },

  post: async <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    const response = await api.post<ApiResponse<T>>(url, data, config)
    return (response as any).data?.data
  },

  put: async <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    const response = await api.put<ApiResponse<T>>(url, data, config)
    return (response as any).data?.data
  },

  patch: async <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    const response = await api.patch<ApiResponse<T>>(url, data, config)
    return (response as any).data?.data
  },

  delete: async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    const response = await api.delete<ApiResponse<T>>(url, config)
    return (response as any).data?.data
  },
}

// 파일 업로드 헬퍼
export const uploadFile = async (file: File, endpoint: string): Promise<string> => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post<ApiResponse<{ url: string }>>(endpoint, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  
  return (response as any).data?.data?.url
}

export default api
