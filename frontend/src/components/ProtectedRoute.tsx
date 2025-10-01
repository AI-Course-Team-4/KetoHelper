import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

interface ProtectedRouteProps {
  children: ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, accessToken } = useAuthStore()

  // 단순히 user와 accessToken 존재 여부만 확인
  // 토큰 검증은 AuthProvider에서 처리
  if (!user || !accessToken) {
    return <Navigate to="/" replace />
  }
  
  return <>{children}</>
}