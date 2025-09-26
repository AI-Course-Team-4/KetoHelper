import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { CircularProgress, Box } from '@mui/material'

interface ProtectedRouteProps {
  children: ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading, accessToken } = useAuthStore()

  // 로딩 중이면 스피너 표시
  if (loading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    )
  }

  // 로그인되지 않은 경우 또는 토큰이 없는 경우 메인 페이지로 리다이렉트
  if (!user || !accessToken) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}