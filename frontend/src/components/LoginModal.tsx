import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { Box } from '@mui/material'
import MuiButton from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import { toast } from 'react-hot-toast'
import { useState } from 'react'
import { useGoogleLogin } from '@react-oauth/google'
import { authService } from '@/lib/authService'
import { useAuthStore } from '@/store/authStore'

interface LoginModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function LoginModal({ open, onOpenChange }: LoginModalProps) {
    const googleLogoUrl = (import.meta as any).env.VITE_GOOGLE_LOGO_URL
    const kakaoLogoUrl = (import.meta as any).env.VITE_KAKAO_LOGO_URL
    const [isGoogleLoading, setIsGoogleLoading] = useState(false)
    const [isKakaoLoading, setIsKakaoLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [isNaverLoading, setIsNaverLoading] = useState(false)
    const setAuth = useAuthStore((s) => s.setAuth)

    const startGoogleAccessFlow = useGoogleLogin({
        flow: 'implicit',
        onSuccess: async (tokenResponse: any) => {
            try {
                setIsGoogleLoading(true)
                const accessToken = tokenResponse?.access_token
                if (!accessToken) throw new Error('Google 액세스 토큰을 가져오지 못했습니다.')
                console.log('[Auth] Google login success', { tokenResponse, accessToken })
                const result = await authService.googleAccessLogin(accessToken)
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
                try {
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
                                resolve()
                            } catch (err) { reject(err) }
                        },
                        fail: (err: any) => {
                            console.error('[Auth] Kakao login fail', err)
                            reject(err)
                        },
                    })
                } catch (e) { reject(e) }
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
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[400px]">
                <DialogHeader>
                    <DialogTitle>소셜 로그인</DialogTitle>
                    <DialogDescription>선호하는 계정으로 로그인하세요.</DialogDescription>
                </DialogHeader>

                <div className="grid grid-cols-1 gap-2">
                    <Box sx={{ mb: 1, display: 'flex', justifyContent: 'center' }}>
                        <MuiButton
                            onClick={() => startGoogleAccessFlow()}
                            variant="contained"
                            disableElevation
                            startIcon={<Box component="img" src={googleLogoUrl} alt="Google" sx={{ width: 18, height: 18 }} aria-hidden />}
                            sx={{
                                maxWidth: 320,
                                width: '100%',
                                borderRadius: 0.5,
                                bgcolor: '#fff',
                                color: '#000',
                                border: '1px solid #dadce0',
                                boxShadow: 'none',
                                '&:hover': { bgcolor: '#fff', boxShadow: 'none' },
                            }}
                        >
                            {isGoogleLoading ? <CircularProgress size={20} sx={{ color: '#000' }} /> : 'Google로 로그인'}
                        </MuiButton>
                    </Box>

                    {/* Kakao Auth 버튼 */}
                    <Box sx={{ mb: 1, display: 'flex', justifyContent: 'center' }}>
                        <MuiButton
                            onClick={handleKakaoLogin}
                            disabled={isKakaoLoading}
                            variant="contained"
                            disableElevation
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
                                boxShadow: 'none',
                                '&:hover': { bgcolor: '#ffe812', boxShadow: 'none' },
                            }}
                        >
                            {isKakaoLoading ? <CircularProgress size={20} sx={{ color: '#000' }} /> : '카카오로 로그인'}
                        </MuiButton>
                    </Box>

                    {/* <Button
                        variant="outline"
                        type="button"
                        className="w-full"
                    >
                        <span className="mr-2">🟢</span>
                        Naver로 계속하기
                    </Button> */}
                    {/* Naver Auth 버튼 */}
                    <Box sx={{ mb: 1, display: 'flex', justifyContent: 'center' }}>
                        <MuiButton
                            disableElevation
                            variant="contained"
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
                                    // Popup blocked, fall back to full-page redirect
                                    window.location.href = authUrl
                                    return
                                }

                                // Attempt to enforce size/position even if the browser reused an existing window
                                try {
                                    if (popup) {
                                        popup.resizeTo(width, height)
                                        popup.moveTo(Math.round(left), Math.round(top))
                                    }
                                } catch {}

                                const messageHandler = (event: MessageEvent) => {
                                    try {
                                        if (event.origin !== window.location.origin) return
                                        const data: any = (event as any).data
                                        if (!data || data.source !== 'naver_oauth') return
                                        if (data.type === 'success') {
                                            const user = data.user
                                            const at = data.accessToken
                                            const rt = data.refreshToken
                                            if (user && at && rt) {
                                                setAuth(user, at, rt)
                                                toast.success(`안녕하세요 ${user?.name || '사용자'}님!`)
                                                onOpenChange(false)
                                            } else {
                                                toast.error('네이버 로그인 정보가 올바르지 않습니다.')
                                            }
                                        } else if (data.type === 'error') {
                                            const msg = data.message || '네이버 로그인에 실패했습니다.'
                                            toast.error(msg)
                                        }
                                    } finally {
                                        window.removeEventListener('message', messageHandler)
                                        try { popup.close() } catch { }
                                        setIsNaverLoading(false)
                                    }
                                }

                                window.addEventListener('message', messageHandler)

                                // Fallback: if user closes popup without completing
                                const checkClosed = setInterval(() => {
                                    if (popup.closed) {
                                        clearInterval(checkClosed)
                                        window.removeEventListener('message', messageHandler)
                                        setIsNaverLoading(false)
                                    }
                                }, 500)
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
                                boxShadow: 'none',
                                '&:hover': { bgcolor: '#06be34', boxShadow: 'none' },
                            }}
                        >
                            {isNaverLoading ? <CircularProgress size={20} sx={{ color: '#fff' }} /> : '네이버로 로그인'}
                        </MuiButton>
                    </Box>

                    {/* 에러 메시지 */}
                    {error && (
                        <Box sx={{ color: '#d32f2f', fontSize: 12, textAlign: 'center', mt: 1 }}>{error}</Box>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    )
}