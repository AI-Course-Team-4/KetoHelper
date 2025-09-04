import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { Toaster } from 'react-hot-toast'
import { GoogleOAuthProvider } from '@react-oauth/google'

import App from './App.tsx'
import { theme } from './theme/index.ts'
import './index.css'

// React Query 클라이언트 생성
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5분
    },
  },
})

// 런타임에 주입된 Google Client ID 확인용 (임시 로그)
console.log('VITE_GOOGLE_CLIENT_ID: ', import.meta.env.VITE_GOOGLE_CLIENT_ID)
console.log('VITE_NAVER_CLIENT_ID:', import.meta.env.VITE_NAVER_CLIENT_ID)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <GoogleOAuthProvider
      clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID!}
      key={import.meta.env.VITE_GOOGLE_CLIENT_ID}
    >
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <App />
            <Toaster
              position="top-center"
              toastOptions={{
                duration: 2500,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
              }}
            />
          </ThemeProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </GoogleOAuthProvider>
  </React.StrictMode>,
)
