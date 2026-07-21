import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  css: {
    postcss: './postcss.config.js'
  },
  server: {
    host: true, // Needed for Docker
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://backend:8000', // Assuming your python backend runs on 8000
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
