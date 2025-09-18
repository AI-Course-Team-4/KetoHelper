import { useEffect } from 'react'
import { Box } from '@mui/material'
import CircularProgress from '@mui/material/CircularProgress'
import { toast } from 'react-hot-toast'
import { authService } from '@/lib/authService'
import { useAuthStore } from '@/store/authStore'

export default function NaverCallback() {
  const setAuth = useAuthStore((s) => s.setAuth)

  useEffect(() => {
    const run = async () => {
      try {
        console.log('[Naver] Callback start', window.location.href)
        const params = new URLSearchParams(window.location.search)
        const code = params.get('code') || ''
        const state = params.get('state') || ''
        // const debug = params.get('debug') === '1'
        console.log('[Naver] Params', { code: !!code, state })
        if (!code || !state) throw new Error('잘못된 네이버 인증 응답입니다.')
        try {
          const expected = sessionStorage.getItem('naver_oauth_state')
          if (expected && expected !== state) {
            throw new Error('네이버 로그인 상태값이 일치하지 않습니다. 다시 시도해주세요.')
          }
          console.log('[Naver] State OK', { expected, state })
        } catch (e) {
          console.warn('[Naver] State check skipped/failed', e)
        }
        const redirectUri = `${window.location.origin}/auth/naver/callback`
        const result = await authService.naverLogin(code, state, redirectUri)
        const backendUser = (result as any)?.user
        const at = (result as any)?.accessToken
        const rt = (result as any)?.refreshToken
        if (!at || !rt) throw new Error('토큰 발급에 실패했습니다.')
        setAuth(
          {
            id: backendUser?.id ?? 'unknown',
            email: backendUser?.email ?? '',
            name: backendUser?.name ?? '',
            profileImage: backendUser?.profile_image ?? '',
          },
          at,
          rt,
        )
        console.log('[Naver] Login success', {
          id: backendUser?.id,
          name: backendUser?.name,
          email: backendUser?.email,
          profile_image: backendUser?.profile_image,
        })
        toast.success(`안녕하세요 ${backendUser?.name || '사용자'}님!`)
        try {
          window.history.replaceState({}, document.title, '/')
          sessionStorage.removeItem('naver_oauth_state')
        } catch {}
        window.location.href = '/'
      } catch (e: any) {
        console.error('네이버 로그인 처리 실패:', e)
        toast.error(e?.message || '네이버 로그인에 실패했습니다.')
        // 잠깐 대기 후 홈으로 이동 (로그 확인 시간 확보)
        setTimeout(() => { window.location.href = '/' }, 200)
      }
    }
    run()
  }, [setAuth])

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '50vh' }}>
      <CircularProgress />
    </Box>
  )
}