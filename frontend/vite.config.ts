import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
<<<<<<< HEAD
import { fileURLToPath, URL } from 'node:url' 
=======
import { resolve } from 'path'
>>>>>>> origin/dev

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
<<<<<<< HEAD
      '@': fileURLToPath(new URL('./src', import.meta.url)),
=======
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@pages': resolve(__dirname, 'src/pages'),
      '@hooks': resolve(__dirname, 'src/hooks'),
      '@services': resolve(__dirname, 'src/services'),
      '@store': resolve(__dirname, 'src/store'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@types': resolve(__dirname, 'src/types'),
>>>>>>> origin/dev
    },
  },
  server: {
    port: 3000,
<<<<<<< HEAD
=======
    host: true,
>>>>>>> origin/dev
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
<<<<<<< HEAD
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  }
=======
        secure: false,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
>>>>>>> origin/dev
})
