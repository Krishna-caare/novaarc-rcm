import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Netlify: base = '/'  (served from root domain)
// GitHub Pages: base = '/novaarc-rcm/'
// VITE_BASE_PATH env var is set in CI for each platform
const base = process.env.VITE_BASE_PATH || '/'

export default defineConfig({
  base,
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})