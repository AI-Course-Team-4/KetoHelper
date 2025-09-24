import { useEffect } from 'react'
import { Box, CircularProgress } from '@mui/material'
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
        const authPayload = {
          id: backendUser?.id ?? 'unknown',
          email: backendUser?.email ?? '',
          name: backendUser?.name ?? '',
          profileImage: backendUser?.profile_image ?? '',
        }
        setAuth(authPayload, at, rt)
        console.log('[Naver] Login success', {
          id: backendUser?.id,
          name: backendUser?.name,
          email: backendUser?.email,
          profile_image: backendUser?.profile_image,
        })
        toast.success(`안녕하세요 ${backendUser?.name || '사용자'}님!`)

        // If opened as a popup, post message back to opener and close
        try {
          if (window.opener && window.opener !== window) {
            window.opener.postMessage(
              {
                source: 'naver_oauth',
                type: 'success',
                user: authPayload,
                accessToken: at,
                refreshToken: rt,
              },
              window.location.origin
            )
            try { sessionStorage.removeItem('naver_oauth_state') } catch {}
            window.close()
            return
          }
        } catch (e) {
          console.warn('[Naver] postMessage to opener failed', e)
        }

        // Fallback: same-tab flow
        try {
          window.history.replaceState({}, document.title, '/')
          sessionStorage.removeItem('naver_oauth_state')
        } catch {}
        window.location.href = '/'
      } catch (e: any) {
        console.error('네이버 로그인 처리 실패:', e)
        toast.error(e?.message || '네이버 로그인에 실패했습니다.')
        // If in popup, notify opener of error and close
        try {
          if (window.opener && window.opener !== window) {
            window.opener.postMessage(
              {
                source: 'naver_oauth',
                type: 'error',
                message: e?.message || '네이버 로그인에 실패했습니다.'
              },
              window.location.origin
            )
            window.close()
            return
          }
        } catch {}
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