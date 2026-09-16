import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Netlify: base = '/'  (served from root domain)
// GitHub Pages: base = '/novaarc-rcm/'
// VITE_BASE_PATH env var is set in CI for each platform
const base = process.env.VITE_BASE_PATH || '/'

// During local dev, proxy API calls to the Render backend to avoid CORS issues.
// The VITE_API_URL in .env points to the real Render URL for production builds.
const BACKEND_URL = 'https://novaarc-backend.onrender.com'

export default defineConfig({
  base,
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5174,
    host: true,
    // Proxy all backend API paths to Render — avoids CORS in local dev
    proxy: {
      '/auth': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: true,
      },
      '/claims': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: true,
      },
      '/denials': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: true,
      },
      '/payments': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: true,
      },
      '/dashboard': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: true,
      },
      '/work-queues': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: true,
      },
      '/agents': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: true,
      },
      '/assistant': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: true,
      },
      '/health': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: true,
      },
    },
  },
})