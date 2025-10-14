import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url' 

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path, // 경로를 그대로 유지
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    // 프로덕션 빌드에서 console/debugger 제거
    // 개발 모드에서는 보이도록 유지
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
          utils: ['axios', 'date-fns', 'zod', 'zustand', '@tanstack/react-query'],
          auth: ['@react-oauth/google', '@supabase/supabase-js']
        }
      }
    },
    // esbuild 옵션으로 prod에서만 드롭
    // (vite는 내부적으로 esbuild를 사용해 drop 옵션을 지원)
    target: 'es2018',
    // 모드별 설정 분기
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore - esbuild options pass-through
    esbuild: {
      drop: mode === 'production' ? ['console', 'debugger'] : [],
    },
    chunkSizeWarningLimit: 1000
  }
}))
