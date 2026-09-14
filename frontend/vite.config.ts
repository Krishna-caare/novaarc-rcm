import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// When deploying to GitHub Pages the site lives at /novaarc-rcm/
// VITE_BASE_PATH is set to '/novaarc-rcm/' in the CI workflow
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