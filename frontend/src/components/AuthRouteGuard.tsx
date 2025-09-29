import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { authService } from '@/services/AuthService'
import { LoginModal } from '@/components/LoginModal'
import { toast } from 'react-hot-toast'

// 단일 전역 가드: 모든 페이지 이동 시 토큰 상태를 점검하고 필요한 조치를 수행한다
export function AuthRouteGuard() {
  const { user, accessToken } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()
  const [loginOpen, setLoginOpen] = useState(false)
  const handledTickRef = useRef<number>(0)

  const path = location.pathname

  // 권한 정책: 보호 경로, 모달 유도 경로 정의
  const guards = useMemo(() => ({
    protectedPrefixes: ['/profile', '/calendar'],
    modalPrefixes: ['/subscribe'],
  }), [])

  useEffect(() => {
    const tick = Math.floor(Date.now() / 1000)
    if (handledTickRef.current === tick) return

    // 수동 로그아웃 중에는 개입하지 않음
    if (typeof window !== 'undefined' && (window as any).isManualLogout) return

    const run = async () => {
      // 토큰 만료 여부 계산
      let isExpired = false
      if (accessToken) {
        try {
          const payload = JSON.parse(atob(accessToken.split('.')[1]))
          const nowSec = Math.floor(Date.now() / 1000)
          isExpired = Number(payload?.exp) <= nowSec
        } catch {
          // 디코드 실패 시 인터셉터에서 처리되므로 여기선 패스
        }
      }

      const isAuthed = !!user && !!accessToken && !isExpired
      const isProtected = guards.protectedPrefixes.some((p) => path.startsWith(p))
      const isModalPath = guards.modalPrefixes.some((p) => path.startsWith(p))

      // 인증 안되었거나 토큰 만료로 보이는 경우: 먼저 refresh 시도
      if (!isAuthed) {
        handledTickRef.current = tick
        try {
          const res = await authService.refreshTokens()
          if (res?.success && res.accessToken) {
            // 갱신 성공 → 그대로 유지, 모달 닫기
            if (loginOpen) setLoginOpen(false)
            return
          }
        } catch {
          // 무시하고 아래 만료 처리 진행
        }

        // refresh 실패 → 세션 종료 및 분기 처리
        try { if (user) authService.clearMemory(true) } catch {}

        if (isProtected) {
          navigate('/')
          return
        }

        if (isModalPath) {
          if (!loginOpen) {
            toast.error('로그인해야 이용할 수 있는 기능입니다.')
            setLoginOpen(true)
          }
          return
        }
      } else {
        // 인증 복구 시 모달 닫기
        if (loginOpen) setLoginOpen(false)
      }
    }

    run()
  }, [user, accessToken, path, guards, navigate, loginOpen])

  return (
    <LoginModal
      open={loginOpen}
      onOpenChange={(next) => {
        setLoginOpen(next)
        if (!next) {
          const authed = !!useAuthStore.getState().user && !!useAuthStore.getState().accessToken
          if (!authed) navigate('/')
        }
      }}
    />
  )
}


