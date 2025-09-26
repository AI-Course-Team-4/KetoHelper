import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

interface PublicOnlyRouteProps {
  children: ReactNode
  redirectTo?: string
}

export function PublicOnlyRoute({ children, redirectTo = '/' }: PublicOnlyRouteProps) {
  const { user } = useAuthStore()

  // 로그인된 경우 메인 페이지로 리다이렉트
  if (user) {
    return <Navigate to={redirectTo} replace />
  }

  return <>{children}</>
}
