import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react()],
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8001',
          changeOrigin: true,
          secure: false
        }
      }
    },
    define: {
      'process.env': {},
      'process.env.REACT_APP_BACKEND_URL': JSON.stringify(env.REACT_APP_BACKEND_URL),
      'import.meta.env.REACT_APP_BACKEND_URL': JSON.stringify(env.REACT_APP_BACKEND_URL)
    }
  }
})