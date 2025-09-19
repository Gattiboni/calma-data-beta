import { defineConfig } from 'vite'

export default defineConfig({
  esbuild: {
    loader: 'jsx',
    include: /src\/.*\.[jt]sx?$/,
    exclude: []
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx'
      }
    }
  },
  server: {
    port: 3000,
    host: '0.0.0.0'
  },
  define: {
    global: 'globalThis'
  }
})