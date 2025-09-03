import { apiHelper } from './api'
import type { User, GoogleAuthResponse, LoginCredentials } from '../types/index'

export const authService = {
  // Google OAuth 로그인
  googleLogin: async (tokenId: string): Promise<GoogleAuthResponse> => {
    return apiHelper.post<GoogleAuthResponse>('/auth/google', { token: tokenId })
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
