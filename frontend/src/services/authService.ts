import { api, apiHelper } from './api'
import type { User, GoogleAuthResponse, LoginCredentials } from '../types/index'

export const authService = {
  // Google OAuth 로그인 (ID 토큰 교환)
  googleLogin: async (idToken: string): Promise<any> => {
    // Use raw axios to access either wrapped or unwrapped response
    const response = await api.post('/auth/google', { token: idToken })
    const data = (response as any)?.data?.data ?? (response as any)?.data

    const accessToken = data?.accessToken ?? data?.access_token
    if (accessToken) {
      localStorage.setItem('access_token', accessToken)
    }
    return data
  },

  // Google OAuth 로그인 (Access Token 교환)
  googleAccessLogin: async (accessTokenFromGoogle: string): Promise<any> => {
    const response = await api.post('/auth/google/access', { access_token: accessTokenFromGoogle })
    const data = (response as any)?.data?.data ?? (response as any)?.data

    const accessToken = data?.accessToken ?? data?.access_token
    if (accessToken) {
      localStorage.setItem('access_token', accessToken)
    }
    return data
  },

  // Naver OAuth 로그인 (Authorization Code 교환)
  naverLogin: async (code: string, state: string, redirectUri?: string): Promise<any> => {
    const response = await api.post('/auth/naver', { code, state, redirect_uri: redirectUri })
    const data = (response as any)?.data?.data ?? (response as any)?.data

    const accessToken = data?.accessToken ?? data?.access_token
    if (accessToken) {
      localStorage.setItem('access_token', accessToken)
    }
    return data
  },

  // Kakao OAuth 로그인 (Access Token 교환)
  kakaoLogin: async (accessTokenFromKakao: string): Promise<any> => {
    const response = await api.post('/auth/kakao', { token: accessTokenFromKakao })
    const data = (response as any)?.data?.data ?? (response as any)?.data

    const accessToken = data?.accessToken ?? data?.access_token
    if (accessToken) {
      localStorage.setItem('access_token', accessToken)
    }
    return data
  },

  // 일반 로그인 (향후 구현)
  login: async (credentials: LoginCredentials): Promise<GoogleAuthResponse> => {
    return apiHelper.post<GoogleAuthResponse>('/auth/login', credentials)
  },

  // 로그아웃
  logout: async (): Promise<void> => {
    await apiHelper.post<void>('/auth/logout')
    localStorage.removeItem('access_token')
  },

  // 토큰 갱신
  refreshToken: async (): Promise<{ accessToken: string }> => {
    return apiHelper.post<{ accessToken: string }>('/auth/refresh')
  },

  // 현재 사용자 정보 조회
  getCurrentUser: async (): Promise<User> => {
    return apiHelper.get<User>('/auth/me')
  },

  // 사용자 프로필 업데이트
  updateProfile: async (profileData: Partial<User>): Promise<User> => {
    return apiHelper.patch<User>('/auth/profile', profileData)
  },

  // 사용자 선호도 업데이트
  updatePreferences: async (preferences: Partial<User['preferences']>): Promise<User> => {
    return apiHelper.patch<User>('/auth/preferences', preferences)
  },

  // 사용자 설정 업데이트
  updateSettings: async (settings: Partial<User['settings']>): Promise<User> => {
    return apiHelper.patch<User>('/auth/settings', settings)
  },

  // 계정 삭제
  deleteAccount: async (): Promise<void> => {
    await apiHelper.delete<void>('/auth/account')
    localStorage.removeItem('access_token')
  },
}
