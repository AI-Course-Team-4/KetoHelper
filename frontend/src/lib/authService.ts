import { api } from '@/hooks/useApi';

export const authService = {
  async googleAccessLogin(accessToken: string) {
    const res = await api.post('/auth/google', { access_token: accessToken })
    return res.data
  },
  async kakaoLogin(accessToken: string) {
    const res = await api.post('/auth/kakao', { access_token: accessToken })
    return res.data
  },
  async naverLogin(code: string, state: string, redirectUri: string) {
    const res = await api.post('/auth/naver', { code, state, redirect_uri: redirectUri })
    return res.data
  },
  async refresh(refreshToken: string) {
    const res = await api.post('/auth/refresh', { refresh_token: refreshToken })
    return res.data
  },
  async logout() {
    const res = await api.post('/auth/logout')
    return res.data
  }
}


