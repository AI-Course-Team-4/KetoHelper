import axios from 'axios'

export const authService = {
  async googleAccessLogin(accessToken: string) {
    const res = await axios.post('/api/v1/auth/google', { access_token: accessToken }, { withCredentials: true })
    return res.data
  },
  async kakaoLogin(accessToken: string) {
    const res = await axios.post('/api/v1/auth/kakao', { access_token: accessToken }, { withCredentials: true })
    return res.data
  },
  async naverLogin(code: string, state: string, redirectUri: string) {
    const res = await axios.post('/api/v1/auth/naver', { code, state, redirect_uri: redirectUri }, { withCredentials: true })
    return res.data
  },
  async refresh(refreshToken: string) {
    const res = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken }, { withCredentials: true })
    return res.data
  },
  async logout() {
    const res = await axios.post('/api/v1/auth/logout', undefined, { withCredentials: true })
    return res.data
  }
}


