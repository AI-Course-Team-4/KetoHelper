import { Dialog } from '@/components/mui'
import { Box, CircularProgress } from '@mui/material'
import { toast } from 'react-hot-toast'
import { useState } from 'react'
import { useGoogleLogin } from '@react-oauth/google'
import { authService } from '@/lib/authService'
import { useAuthStore } from '@/store/authStore'


const googleLogo = "/google.svg";
const kakaoLogo  = "/kakaotalk.svg";

interface LoginModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function LoginModal({ open, onOpenChange }: LoginModalProps) {

    const [isGoogleLoading, setIsGoogleLoading] = useState(false)
    const [isKakaoLoading, setIsKakaoLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [isNaverLoading, setIsNaverLoading] = useState(false)
    const setAuth = useAuthStore((s) => s.setAuth)

    const startGoogleAccessFlow = useGoogleLogin({
        flow: 'implicit',
        scope: 'openid profile email',
        onSuccess: async (tokenResponse: any) => {
            try {
                setIsGoogleLoading(true)
                const accessToken = tokenResponse?.access_token
                if (!accessToken) throw new Error('Google 액세스 토큰을 가져오지 못했습니다.')
                console.log('[Auth] Google login success - raw tokenResponse:', tokenResponse)
                // 원본 구글 유저 정보 조회 (sh k 등 프로필 이름 확인)
                let googleProfile: any = null
                try {
                    const resp = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
                        headers: { Authorization: `Bearer ${accessToken}` },
                    })
                    googleProfile = await resp.json().catch(() => null)
                } catch {}
                console.log('[Auth] Google userinfo:', googleProfile)
                // 로컬 스토리지 저장은 불필요하므로 제거
                const result = await authService.googleAccessLogin(accessToken)
                const backendUser = (result as any)?.user
                console.log('Google login 원래 정보:', result)
                const at = (result as any)?.accessToken
                const rt = (result as any)?.refreshToken
                if (!at || !rt) throw new Error('토큰 발급에 실패했습니다.')
                setAuth(
                    {
                        id: backendUser?.id ?? 'unknown',
                        email: backendUser?.email ?? '',
                        name: backendUser?.name ?? '',
                        profileImage: backendUser?.profile_image ?? '',
                        socialNickname: googleProfile.name ?? '',
                    },
                    at,
                    rt,
                )
                console.log('[Auth] user', {
                    id: backendUser?.id,
                    name: backendUser?.name,
                    email: backendUser?.email,
                    profile_image: backendUser?.profile_image,
                })
                toast.success(`안녕하세요 ${backendUser?.name || '사용자'}님!`)
                onOpenChange(false)
            } catch (e: any) {
                console.error('Google 액세스 로그인 실패:', e)
                toast.error(e?.message || 'Google 로그인에 실패했습니다.')
            } finally {
                setIsGoogleLoading(false)
            }
        },
        onError: () => toast.error('Google 로그인에 실패했습니다.'),
    })

    const loadKakaoSdk = (): Promise<void> => {
        return new Promise((resolve, reject) => {
            try {
                const w = window as any
                if (w.Kakao && w.Kakao.isInitialized && w.Kakao.isInitialized()) {
                    resolve(); return
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
                        } catch (e) { reject(e) }
                    }
                    script.onerror = () => reject(new Error('Kakao SDK 로드 실패'))
                    document.head.appendChild(script)
                } else {
                    const key = (import.meta as any).env.VITE_KAKAO_JAVASCRIPT_KEY
                    if (!key) return reject(new Error('Kakao JavaScript Key가 설정되지 않았습니다.'))
                    w.Kakao.init?.(key)
                    resolve()
                }
            } catch (e) { reject(e) }
        })
    }

    const handleKakaoLogin = async () => {
        setIsKakaoLoading(true)
        setError(null)
        try {
            await loadKakaoSdk()
            const w = window as any
            await new Promise<void>((resolve, reject) => {
                let finished = false
                const cleanup = () => {
                    finished = true
                    try { window.removeEventListener('focus', onFocus) } catch { }
                    try { clearTimeout(timeoutId) } catch { }
                }
                const cancel = () => {
                    if (finished) return
                    cleanup()
                    // silently stop loading without showing error/toast
                    resolve()
                }
                const onFocus = () => {
                    // 사용자가 팝업을 닫고 부모 창으로 돌아온 경우로 간주
                    if (!finished) cancel()
                }
                const timeoutId = setTimeout(() => {
                    if (!finished) cancel()
                }, 20000)
                try {
                    window.addEventListener('focus', onFocus)
                    w.Kakao.Auth.login({
                        scope: 'account_email profile_nickname profile_image',
                        success: async (authObj: any) => {
                            try {
                                const kakaoAccessToken = authObj?.access_token
                                if (!kakaoAccessToken) throw new Error('Kakao 액세스 토큰을 가져오지 못했습니다.')
                                console.log('[Auth] Kakao login success', { authObj, kakaoAccessToken })
                                const result = await authService.kakaoLogin(kakaoAccessToken)
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
                                        socialNickname: backendUser?.name ?? '',
                                    },
                                    at,
                                    rt,
                                )
                                console.log('[Auth] user', {
                                    id: backendUser?.id,
                                    name: backendUser?.name,
                                    email: backendUser?.email,
                                    profile_image: backendUser?.profile_image,
                                })
                                cleanup()
                                toast.success(`안녕하세요 ${backendUser?.name || '사용자'}님!`)
                                onOpenChange(false)
                                resolve()
                            } catch (err) { cleanup(); reject(err as any) }
                        },
                        fail: (err: any) => {
                            console.error('[Auth] Kakao login fail', err)
                            // treat as user-cancel or silent fail → just stop loading
                            cleanup()
                            resolve()
                        },
                    })
                } catch (e) { cleanup(); reject(e as any) }
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
        <Dialog 
            open={open} 
            onClose={() => onOpenChange(false)}
            title="소셜 로그인"
            description="선호하는 계정으로 로그인하세요."
            maxWidth="xs"
        >

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, p: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                        <Box
                            component="button"
                            onClick={() => startGoogleAccessFlow()}
                            disabled={isGoogleLoading}
                            sx={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: 1,
                                maxWidth: 320,
                                width: '100%',
                                height: 40,
                                px: 3,
                                py: 1,
                                borderRadius: 1,
                                bgcolor: '#fff',
                                color: '#000',
                                border: '1px solid #dadce0',
                                boxShadow: 'none',
                                cursor: 'pointer',
                                '&:hover': { 
                                    bgcolor: '#f8f9fa',
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                                },
                                '&:disabled': {
                                    opacity: 0.6,
                                    cursor: 'not-allowed',
                                },
                            }}
                        >
                            <Box component="img" src={googleLogo} alt="Google" sx={{ width: 18, height: 18 }} />
                            {isGoogleLoading ? <CircularProgress size={20} sx={{ color: '#000' }} /> : 'Google로 로그인'}
                        </Box>
                    </Box>

                    {/* Kakao Auth 버튼 */}
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                        <Box
                            component="button"
                            onClick={handleKakaoLogin}
                            disabled={isKakaoLoading}
                            sx={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: 1,
                                maxWidth: 320,
                                width: '100%',
                                height: 40,
                                px: 3,
                                py: 1,
                                borderRadius: 1,
                                bgcolor: '#ffe812',
                                color: '#000',
                                border: 'none',
                                boxShadow: 'none',
                                cursor: 'pointer',
                                '&:hover': { 
                                    bgcolor: '#f7d600',
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                                },
                                '&:disabled': {
                                    opacity: 0.6,
                                    cursor: 'not-allowed',
                                },
                            }}
                        >
                            <Box component="img" src={kakaoLogo} alt="Kakao" sx={{ width: 18, height: 18 }} />
                            {isKakaoLoading ? <CircularProgress size={20} sx={{ color: '#000' }} /> : '카카오로 로그인'}
                        </Box>
                    </Box>

                    {/* Naver Auth 버튼 */}
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                        <Box
                            component="button"
                            onClick={() => {
                                const clientId = (import.meta as any).env.VITE_NAVER_CLIENT_ID as string
                                if (!clientId) {
                                    toast.error('Naver Client ID가 설정되지 않았습니다. .env에 VITE_NAVER_CLIENT_ID를 추가하세요.')
                                    return
                                }
                                setIsNaverLoading(true)
                                setError(null)
                                const redirectUriRaw = `${window.location.origin}/auth/naver/callback`
                                const redirectUri = encodeURIComponent(redirectUriRaw)
                                const state = Math.random().toString(36).slice(2)
                                try { sessionStorage.setItem('naver_oauth_state', state) } catch { }
                                const authUrl = `https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id=${clientId}&redirect_uri=${redirectUri}&state=${state}`
                                console.log('[Auth] Naver popup start', { authUrl, state, redirectUri: redirectUriRaw })

                                const width = 520
                                const height = 500
                                const left = window.screenX + Math.max(0, (window.outerWidth - width) / 2)
                                const top = window.screenY + Math.max(0, (window.outerHeight - height) / 2)
                                const popupName = `naver_oauth_popup_${state}`
                                const features = `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes,status=no,toolbar=no,menubar=no,location=no`
                                const popup = window.open(
                                    authUrl,
                                    popupName,
                                    features
                                )

                                if (!popup) {
                                    // 팝업 차단 시 전체 리다이렉트 대신 안내만 하고 중지
                                    toast.error('팝업이 차단되었습니다. 브라우저 팝업을 허용하고 다시 시도하세요.')
                                    setIsNaverLoading(false)
                                    return
                                }

                                // Attempt to enforce size/position even if the browser reused an existing window
                                try {
                                    if (popup) {
                                        popup.resizeTo(width, height)
                                        popup.moveTo(Math.round(left), Math.round(top))
                                    }
                                } catch {}

                                let handled = false
                                let checkClosed: any = null

                                const finalize = () => {
                                    try { window.removeEventListener('message', messageHandler) } catch {}
                                    try { window.removeEventListener('storage', storageHandler) } catch {}
                                    try { if (checkClosed) clearInterval(checkClosed) } catch {}
                                    try { popup.close() } catch {}
                                    setIsNaverLoading(false)
                                }

                                const processResult = (user: any, at: string, rt: string) => {
                                    if (handled) return
                                    handled = true
                                    setAuth(
                                        {
                                            id: user?.id ?? 'unknown',
                                            email: user?.email ?? '',
                                            name: user?.name ?? '',
                                            profileImage: user?.profile_image ?? user?.profileImage ?? '',
                                            socialNickname: user?.name ?? '',
                                        },
                                        at,
                                        rt,
                                    )
                                    // 먼저 팝업/리스너를 정리하고
                                    onOpenChange(false)
                                    finalize()
                                    // 그 다음 부모 창에서만 토스트 노출
                                    toast.success(`안녕하세요 ${user?.name || '사용자'}님!`)
                                }

                                const messageHandler = (event: MessageEvent) => {
                                    try {
                                        const data: any = (event as any).data
                                        if (!data || data.source !== 'naver_oauth') return
                                        if (data.type === 'success') {
                                            const user = data.user as any
                                            const at = data.accessToken
                                            const rt = data.refreshToken
                                            if (user && at && rt) {
                                                processResult(user, at, rt)
                                            } else {
                                                toast.error('네이버 로그인 정보가 올바르지 않습니다.')
                                            }
                                        } else if (data.type === 'error') {
                                            const msg = data.message || '네이버 로그인에 실패했습니다.'
                                            toast.error(msg)
                                        }
                                    } finally {}
                                }

                                window.addEventListener('message', messageHandler)

                                // storage 폴백 리스너 (프리뷰/기타 도메인에서 postMessage 실패 대비)
                                const storageHandler = (e: StorageEvent) => {
                                    if (e.key !== 'naver_oauth_result' || !e.newValue) return
                                    try {
                                        const data = JSON.parse(e.newValue)
                                        if (!data || data.source !== 'naver_oauth') return
                                        if (data.type === 'success') {
                                            const user = data.user as any
                                            const at = data.accessToken
                                            const rt = data.refreshToken
                                            if (user && at && rt) processResult(user, at, rt)
                                        }
                                    } finally {}
                                }
                                window.addEventListener('storage', storageHandler)

                                // Fallback: if user closes popup without completing
                                checkClosed = setInterval(() => {
                                    if (popup.closed) {
                                        clearInterval(checkClosed)
                                        finalize()
                                    }
                                }, 500)
                            }}
                            sx={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: 1,
                                maxWidth: 320,
                                width: '100%',
                                height: 40,
                                px: 3,
                                py: 1,
                                borderRadius: 1,
                                bgcolor: '#06be34',
                                color: '#fff',
                                border: 'none',
                                boxShadow: 'none',
                                cursor: 'pointer',
                                '&:hover': { 
                                    bgcolor: '#05a32a',
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                                },
                                '&:disabled': {
                                    opacity: 0.6,
                                    cursor: 'not-allowed',
                                },
                            }}
                        >
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
                            {isNaverLoading ? <CircularProgress size={20} sx={{ color: '#fff' }} /> : '네이버로 로그인'}
                        </Box>
                    </Box>

                    {/* 에러 메시지 */}
                    {error && (
                        <Box sx={{ color: '#d32f2f', fontSize: 12, textAlign: 'center', mt: 1 }}>{error}</Box>
                    )}
                </Box>
        </Dialog>
    )
}