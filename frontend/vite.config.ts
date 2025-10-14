import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url' 

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  // prod 번들에서 console/debugger 제거는 최상위 esbuild 옵션으로 설정해야 적용됩니다.
  esbuild: {
    drop: mode === 'production' ? ['console', 'debugger'] : [],
  },
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
    // esbuild drop은 최상위에서 설정됨
    target: 'es2018',
    chunkSizeWarningLimit: 1000
  }
}))
