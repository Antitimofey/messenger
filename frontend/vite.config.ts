import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const fePort = Number(env.FRONTEND_PORT || env.VITE_FRONTEND_PORT || 5173)
  const beUrl = `http://localhost:${env.BACKEND_PORT || env.VITE_BACKEND_PORT || 8888}`

  return {
    plugins: [react()],
    server: {
      port: fePort,
      strictPort: true,
      proxy: {
        // Eel: eel.js и WebSocket ws://…/eel — через тот же origin, что и Vite
        '/eel.js': { target: beUrl, changeOrigin: true },
        '/eel': { target: beUrl, changeOrigin: true, ws: true },
      },
    },
  }
})
