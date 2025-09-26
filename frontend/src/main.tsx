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
      <HotToaster
          position="top-center"
          toastOptions={{
            duration: 3500,
            style: { fontSize: 14 },
            success: { duration: 3500 },
            error: { duration: 4000 },
          }}
        />
      {/* 새로고침 후 1회성 세션 만료 토스트 처리 */}
      {(() => {
        try {
          const flag = sessionStorage.getItem('session-expired')
          if (flag) {
            sessionStorage.removeItem('session-expired')
            // 지연하여 렌더 안정화 후 토스트 표시
            setTimeout(async () => {
              const { commonToasts } = await import('@/lib/toast')
              commonToasts.sessionExpired()
            }, 50)
          }
        } catch {}
        return null
      })()}
      <CssBaseline />
      <GoogleOAuthProvider clientId={googleClientId || ''}>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <AuthProvider>
              <App />
            </AuthProvider>
          </BrowserRouter>
        </QueryClientProvider>
      </GoogleOAuthProvider>
    </ThemeProvider>
  </React.StrictMode>,
)