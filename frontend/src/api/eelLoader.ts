/**
 * Eel 0.16: WebSocket создаётся в обработчике DOMContentLoaded внутри eel.js.
 * Если скрипт подгружаем динамически — событие уже прошло, WS не появится.
 * Решение: после загрузки вручную вызвать DOMContentLoaded + прокси /eel в Vite.
 */

const useDevProxy = import.meta.env.DEV
const host = import.meta.env.VITE_BACKEND_HOST ?? 'localhost'
const port = Number(import.meta.env.VITE_BACKEND_PORT ?? '8888')

let loadPromise: Promise<boolean> | null = null

/** URL для <script src="…"> */
export function getEelScriptUrl(): string {
  if (useDevProxy) return '/eel.js'
  return `http://${host}:${port}/eel.js`
}

function ensureEelWebSocket(): void {
  const existing = (window.eel as { _websocket?: WebSocket } | undefined)?._websocket
  if (existing && existing.readyState !== WebSocket.CLOSED) return
  if (document.readyState === 'loading') return
  document.dispatchEvent(new Event('DOMContentLoaded'))
}

/** Дождаться WebSocket к Eel. */
export async function waitForEelWebSocket(timeoutMs = 20000): Promise<boolean> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const ws = (window.eel as { _websocket?: WebSocket } | undefined)?._websocket
    if (ws?.readyState === WebSocket.OPEN) {
      console.info('[eel] WebSocket подключён', ws.url)
      return true
    }
    await new Promise((r) => setTimeout(r, 50))
  }
  const ws = (window.eel as { _websocket?: WebSocket } | undefined)?._websocket
  console.warn('[eel] WebSocket не подключился за', timeoutMs, 'мс', ws?.url ?? '(нет сокета)')
  return false
}

export function loadEelScript(): Promise<boolean> {
  if (typeof window === 'undefined') return Promise.resolve(false)

  if (window.eel) {
    ensureEelWebSocket()
    return waitForEelWebSocket().then((ok) => ok || !!window.eel)
  }

  if (loadPromise) return loadPromise

  loadPromise = new Promise((resolve) => {
    const script = document.createElement('script')
    script.type = 'text/javascript'
    script.src = getEelScriptUrl()
    script.async = true

    script.onload = () => {
      try {
        console.info('[eel] eel.js загружен', getEelScriptUrl())
        ensureEelWebSocket()
        void waitForEelWebSocket().then((connected) => {
          if (connected) console.info('[eel] готов к вызовам')
          resolve(connected)
        })
      } catch (e) {
        console.error('[eel] ошибка после загрузки', e)
        resolve(false)
      }
    }

    script.onerror = () => {
      console.warn('[eel] не удалось загрузить', getEelScriptUrl())
      resolve(false)
    }

    document.head.appendChild(script)
  })

  return loadPromise
}
