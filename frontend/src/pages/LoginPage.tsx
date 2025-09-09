import { useState, useEffect, useRef } from 'react'
import { Box, Paper, Typography, Button, CircularProgress, Alert } from '@mui/material'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@store/authStore'
import { authService } from '@services/authService'
import { toast } from 'react-hot-toast'
import { useGoogleLogin } from '@react-oauth/google'

const LoginPage = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { setUser } = useAuthStore()
  const [isGoogleLoading] = useState(false)
  const [isKakaoLoading, setIsKakaoLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const kakaoLogoUrl = (import.meta as any).env.VITE_KAKAO_LOGO_URL
  const googleLogoUrl = (import.meta as any).env.VITE_GOOGLE_LOGO_URL

  const startGoogleAccessFlow = useGoogleLogin({
    flow: 'implicit',
    onSuccess: async (tokenResponse: any) => {
      try {
        const accessToken = tokenResponse?.access_token
        if (!accessToken) throw new Error('Google 액세스 토큰을 가져오지 못했습니다.')
        const result = await authService.googleAccessLogin(accessToken)
        const backendUser = (result as any)?.user

        const finalUser = {
          id: backendUser?.id ?? 'unknown',
          email: backendUser?.email ?? '',
          name: backendUser?.name ?? '',
          profileImage: backendUser?.profile_image ?? undefined,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          preferences: {
            allergies: [],
            dislikes: [],
            dietaryRestrictions: [],
            experienceLevel: 'beginner' as const,
            goals: { targetCalories: 2000, macroRatio: { carbs: 5, protein: 25, fat: 70 } },
          },
          settings: {
            notifications: { mealReminders: true, recommendations: true, weeklyReport: false },
            units: 'metric' as const,
          },
          subscription: (backendUser as any)?.subscription ?? { isActive: true, plan: 'premium' as const, autoRenewal: true },
        }

        setUser(finalUser as any)
        toast.success(`환영합니다, ${finalUser.name || '사용자'}님!`)
        navigate('/')
      } catch (e: any) {
        console.error('Google 액세스 로그인 실패:', e)
        toast.error(e?.message || 'Google 로그인에 실패했습니다.')
      }
    },
    onError: () => toast.error('Google 로그인에 실패했습니다.'),
  })

  // Handle Naver callback inside LoginPage
  const isNaverCallback = location.pathname === '/auth/naver/callback'
  const naverProcessedRef = useRef(false)
  useEffect(() => {
    if (!isNaverCallback || naverProcessedRef.current) return
    naverProcessedRef.current = true
    const run = async () => {
      try {
        const params = new URLSearchParams(window.location.search)
        const code = params.get('code') || ''
        const state = params.get('state') || ''
        if (!code || !state) throw new Error('잘못된 네이버 인증 응답입니다.')
        // Prevent duplicate handling across React StrictMode re-renders
        const dedupeKey = `naver_cb_${code}`
        if (sessionStorage.getItem(dedupeKey)) return
        sessionStorage.setItem(dedupeKey, '1')

        const redirectUri = `${window.location.origin}/auth/naver/callback`
        const result = await authService.naverLogin(code, state, redirectUri)
        const backendUser = (result as any)?.user

        const finalUser = {
          id: backendUser?.id ?? 'unknown',
          email: backendUser?.email ?? '',
          name: backendUser?.name ?? '',
          profileImage: backendUser?.profile_image ?? undefined,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          preferences: {
            allergies: [],
            dislikes: [],
            dietaryRestrictions: [],
            experienceLevel: 'beginner' as const,
            goals: { targetCalories: 2000, macroRatio: { carbs: 5, protein: 25, fat: 70 } },
          },
          settings: {
            notifications: { mealReminders: true, recommendations: true, weeklyReport: false },
            units: 'metric' as const,
          },
          subscription: (backendUser as any)?.subscription ?? { isActive: true, plan: 'premium' as const, autoRenewal: true },
        }

        setUser(finalUser as any)
        toast.success(`환영합니다, ${finalUser.name || '사용자'}님!`)
        // Clean URL to avoid re-processing if user refreshes/back
        try {
          window.history.replaceState({}, document.title, '/')
        } catch { }
        navigate('/')
      } catch (e: any) {
        console.error('네이버 로그인 실패:', e)
        toast.error(e?.message || '네이버 로그인에 실패했습니다.')
        navigate('/login')
      }
    }
    run()
  }, [isNaverCallback, navigate, setUser])

  if (isNaverCallback) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  const loadKakaoSdk = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      try {
        const w = window as any
        if (w.Kakao && w.Kakao.isInitialized && w.Kakao.isInitialized()) {
          resolve()
          return
        }
        if (!document.getElementById('kakao-sdk')) {
          const script = document.createElement('script')
          script.id = 'kakao-sdk'
          script.src = 'https://developers.kakao.com/sdk/js/kakao.min.js'
          script.async = true
          script.onload = () => {
            try {
              const key = (import.meta as any).env.VITE_KAKAO_JAVASCRIPT_KEY
              if (!key) throw new Error('Kakao JavaScript Key가 설정되지 않았습니다.')
              w.Kakao.init(key)
              resolve()
            } catch (e) {
              reject(e)
            }
          }
          script.onerror = () => reject(new Error('Kakao SDK 로드 실패'))
          document.head.appendChild(script)
        } else {
          const key = (import.meta as any).env.VITE_KAKAO_JAVASCRIPT_KEY
          if (!key) return reject(new Error('Kakao JavaScript Key가 설정되지 않았습니다.'))
          w.Kakao.init?.(key)
          resolve()
        }
      } catch (e) {
        reject(e)
      }
    })
  }

  const handleKakaoLogin = async () => {
    setIsKakaoLoading(true)
    setError(null)
    try {
      await loadKakaoSdk()
      const w = window as any
      await new Promise<void>((resolve, reject) => {
        try {
          w.Kakao.Auth.login({
            success: async (authObj: any) => {
              try {
                const kakaoAccessToken = authObj?.access_token
                if (!kakaoAccessToken) throw new Error('Kakao 액세스 토큰을 가져오지 못했습니다.')
                const result = await authService.kakaoLogin(kakaoAccessToken)
                const accessToken = (result as any)?.accessToken ?? (result as any)?.access_token
                const backendUser = (result as any)?.user
                if (accessToken) {
                  localStorage.setItem('access_token', accessToken)
                }

                const finalUser = {
                  id: backendUser?.id ?? 'unknown',
                  email: backendUser?.email ?? '',
                  name: backendUser?.name ?? '',
                  profileImage: backendUser?.profile_image ?? undefined,
                  createdAt: new Date().toISOString(),
                  updatedAt: new Date().toISOString(),
                  preferences: {
                    allergies: [],
                    dislikes: [],
                    dietaryRestrictions: [],
                    experienceLevel: 'beginner' as const,
                    goals: { targetCalories: 2000, macroRatio: { carbs: 5, protein: 25, fat: 70 } },
                  },
                  settings: {
                    notifications: { mealReminders: true, recommendations: true, weeklyReport: false },
                    units: 'metric' as const,
                  },
                  subscription: (backendUser as any)?.subscription ?? { isActive: true, plan: 'premium' as const, autoRenewal: true },
                }

                setUser(finalUser as any)
                toast.success(`환영합니다, ${finalUser.name || '사용자'}님!`)
                navigate('/')
                resolve()
              } catch (err) {
                reject(err)
              }
            },
            fail: (err: any) => {
              reject(err)
            },
          })
        } catch (e) {
          reject(e)
        }
      })
    } catch (e: any) {
      console.error('카카오 로그인 실패:', e)
      setError(e?.message || '카카오 로그인 중 오류가 발생했습니다.')
      toast.error('카카오 로그인에 실패했습니다.')
    } finally {
      setIsKakaoLoading(false)
    }
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%)',
        p: 2,
      }}
    >
      <Paper
        elevation={8}
        sx={{
          p: 4,
          width: '100%',
          maxWidth: 400,
          textAlign: 'center',
          borderRadius: 3,
        }}
      >
        {/* 로고 */}
        <Typography variant="h3" sx={{ mb: 1, color: 'primary.main' }}>
          🥑
        </Typography>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          KetoHelper
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          키토 라이프스타일을 시작해보세요
        </Typography>

        {/* 에러 메시지 */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Google Auth 버튼 (커스텀) */}
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center' }}>
          <Button
            onClick={() => startGoogleAccessFlow()}
            variant="contained"
            startIcon={<Box component="img" src={googleLogoUrl} alt="Google" sx={{ width: 18, height: 18 }} aria-hidden />}
            sx={{
              maxWidth: 320,
              width: '100%',
              borderRadius: 0.5,
              bgcolor: '#fff',
              color: '#000',
              border: '1px solid #dadce0',
              '&:hover': { bgcolor: '#fff' },
            }}
          >
            Google로 로그인
          </Button>
        </Box>

        {/* Kakao Auth 버튼 */}
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center' }}>
          <Button
            onClick={handleKakaoLogin}
            disabled={isKakaoLoading}
            variant="contained"
            startIcon={
              kakaoLogoUrl ? (
                <Box component="img" src={kakaoLogoUrl} alt="Kakao" sx={{ width: 18, height: 18 }} aria-hidden />
              ) : (
                <Box
                  component="span"
                  aria-hidden
                  sx={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 20,
                    height: 20,
                    bgcolor: '#fff',
                    color: '#000',
                    borderRadius: 0.5,
                    fontWeight: 800,
                    fontSize: 12,
                    lineHeight: '20px',
                  }}
                >
                  K
                </Box>
              )
            }
            sx={{
              maxWidth: 320,
              width: '100%',
              borderRadius: 0.5,
              bgcolor: '#ffe812',
              color: '#000',
              '&:hover': { bgcolor: '#ffe812' },
            }}
          >
            {isKakaoLoading ? <CircularProgress size={20} sx={{ color: '#000' }} /> : '카카오로 로그인'}
          </Button>
        </Box>

        {/* Naver Auth 버튼 */}
        {/* <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center' }}>
          <Button
            fullWidth
            variant="contained"
            onClick={() => {
              const clientId = (import.meta as any).env.VITE_NAVER_CLIENT_ID
              const redirectUri = encodeURIComponent(`${window.location.origin}/auth/naver/callback`)
              const state = Math.random().toString(36).slice(2)
              const authUrl = `https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id=${clientId}&redirect_uri=${redirectUri}&state=${state}`
              window.location.href = authUrl
            }}
            startIcon={
              <Box
                component="span"
                aria-hidden
                sx={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 20,
                  height: 20,
                  color: '#fff',
                  borderRadius: 0.5,
                  fontWeight: 800,
                  fontSize: 15,
                  lineHeight: '20px',
                }}
              >
                N
              </Box>
            }
            sx={{
              maxWidth: 320,
              width: '100%',
              borderRadius: 0.5,
              bgcolor: '#06be34',
              color: '#fff',
              '&:hover': { bgcolor: '#06be34' },
            }}
          >
            네이버로 로그인
          </Button>
        </Box> */}
        {/* 버그 때문에 잠시 주석 처리 */}

        {/* 구글 로딩 표시 */}
        {isGoogleLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}

        

        {/* 개인정보 처리방침 */}
        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          로그인 시 <Link to="/privacy">개인정보처리방침</Link> 및{' '}
          <Link to="/terms">이용약관</Link>에 동의하는 것으로 간주됩니다.
        </Typography>
      </Paper>
    </Box>
  )
}

export default LoginPage
