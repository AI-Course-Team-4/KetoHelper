import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

interface ProtectedRouteProps {
  children: ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, accessToken } = useAuthStore()

  // 로그인되지 않은 경우 또는 토큰이 없는 경우 메인 페이지로 리다이렉트
  if (!user || !accessToken) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}