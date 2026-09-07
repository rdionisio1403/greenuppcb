import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/pcbs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Eğer istek HTML/gezinme isteğiyse backend yerine index.html'e yönlendir (SPA Yenileme Desteği)
        bypass: (req, res, options) => {
          if (req.headers.accept && req.headers.accept.includes('text/html')) {
            return '/index.html';
          }
        }
      },
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
