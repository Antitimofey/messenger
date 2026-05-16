import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { loadEelScript } from './api/eelLoader'
import { setEelReady, USE_EEL } from './api/client'

// UI не ждём Eel — иначе пустой экран, пока WebSocket не подключится
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

if (USE_EEL) {
  void loadEelScript()
    .then((ok) => {
      setEelReady(ok)
      if (!ok) {
        console.warn(
          '[app] Eel/WebSocket не подключён. Запустите: python backend/run_server.py',
        )
      }
    })
    .catch((e) => {
      console.error('[app] ошибка загрузки Eel', e)
      setEelReady(false)
    })
}
