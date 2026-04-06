import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Phase 3 core endpoints
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/metrics': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/security': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ops': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/finance': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // Phase 4 + 5 endpoints
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
