import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import { CssBaseline } from '@mui/material'
import App from './App.tsx'
import '@/lib/bootCleanup'
import '@/lib/axiosClient'
import './index.css'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { muiTheme } from './theme/muiTheme'
import { Toaster as HotToaster } from 'react-hot-toast'
import { AuthProvider } from '@/contexts/AuthContext'

// React Query 클라이언트 설정
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
    mutations: {
      retry: 1,
    },
  },
})

const googleClientId = (import.meta as any).env.VITE_GOOGLE_CLIENT_ID as string

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={muiTheme}>
      <CssBaseline />
      <GoogleOAuthProvider clientId={googleClientId || ''}>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <AuthProvider>
              <App />
              {/* HotToaster를 모든 Provider 안쪽에 배치 */}
              <HotToaster
                position="top-center"
                toastOptions={{
                  duration: 3500,
                  style: { fontSize: 14 },
                  success: { duration: 3500 },
                  error: { duration: 4000 },
                }}
              />
            </AuthProvider>
          </BrowserRouter>
        </QueryClientProvider>
      </GoogleOAuthProvider>
      {/* 새로고침 후 1회성 세션 만료 토스트 처리 (수동 로그아웃/게스트일 때는 표시 X) */}
      {(() => {
        try {
          const flag = sessionStorage.getItem('session-expired')
          const manual = (window as any)?.isManualLogout === true
          const hasLoginSession = sessionStorage.getItem('has-login-session') === '1'
          if (flag && !manual && hasLoginSession) {
            sessionStorage.removeItem('session-expired')
            setTimeout(async () => {
              const { commonToasts } = await import('@/lib/toast')
              commonToasts.sessionExpired()
            }, 50)
          } else if (flag) {
            // 수동 로그아웃 또는 세션 없음이면 플래그만 제거하고 무시
            sessionStorage.removeItem('session-expired')
          }
        } catch {}
        return null
      })()}
    </ThemeProvider>
  </React.StrictMode>,
)