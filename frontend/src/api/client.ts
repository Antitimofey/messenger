import type { ApiResult, Destination, SerialSettings } from '../types'
import { destinationToApiArg, normalizeDestination } from '../types'

export const USE_EEL = import.meta.env.VITE_USE_EEL !== 'false'
export const DEMO_MODE =
  import.meta.env.VITE_DEMO_MODE === 'true' ||
  (import.meta.env.VITE_DEMO_MODE !== 'false' && !USE_EEL)

const EEL_TIMEOUT_MS = Number(import.meta.env.VITE_EEL_TIMEOUT_MS ?? 20000)

let eelReady = false

export function setEelReady(ready: boolean) {
  eelReady = ready
}

/** true, если eel.js загружен и WebSocket открыт */
export function isEelReady(): boolean {
  if (typeof window === 'undefined' || !window.eel) return false
  const ws = (window.eel as { _websocket?: WebSocket })._websocket
  return ws?.readyState === WebSocket.OPEN
}

/** eel.js подключён, WebSocket может ещё устанавливаться */
export function isEelLoaded(): boolean {
  return eelReady && typeof window !== 'undefined' && !!window.eel
}

function logEelResponse(method: string, args: unknown[], response: unknown) {
  console.log(`[eel] ${method}`, { args, response })
}

async function eelCall<T>(name: string, ...args: unknown[]): Promise<T> {
  if (!isEelReady()) {
    throw new Error(
      `Eel не подключён (нет WebSocket). Запустите: python backend/run_server.py :${import.meta.env.VITE_BACKEND_PORT ?? 8888}`,
    )
  }
  const eel = window.eel as unknown as Record<
    string,
    (...a: unknown[]) => () => Promise<T>
  >
  const fn = eel[name]
  if (!fn) throw new Error(`Eel: функция ${name} не найдена`)

  let timeoutId: ReturnType<typeof setTimeout>
  const callPromise = fn(...args)().catch((err: unknown) => {
    const msg = err instanceof Error ? err.message : String(err)
    throw new Error(`eel.${name}: ${msg}`)
  })
  const timeoutPromise = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(
      () => reject(new Error(`Таймаут eel.${name} (${EEL_TIMEOUT_MS} мс)`)),
      EEL_TIMEOUT_MS,
    )
  })

  try {
    const response = await Promise.race([callPromise, timeoutPromise])
    logEelResponse(name, args, response)
    return response
  } finally {
    clearTimeout(timeoutId!)
  }
}

function apiError(
  res: ApiResult<Record<string, unknown>>,
  fallback = 'Ошибка сервера',
): string {
  if (!res.ok && 'error' in res && res.error) return String(res.error)
  return fallback
}

function failIfNotOk<T extends Record<string, unknown>>(
  res: ApiResult<T>,
  fallbackError = 'Ошибка сервера',
): ApiResult<T> & { ok: true } {
  if (!res.ok) {
    throw new Error(apiError(res as ApiResult<Record<string, unknown>>, fallbackError))
  }
  return res as ApiResult<T> & { ok: true }
}

export const api = {
  async listPorts(): Promise<string[]> {
    if (isEelReady()) {
      const res = await eelCall<ApiResult<{ ports: string[] }>>('list_ports')
      if (!res.ok) {
        console.warn('[eel] list_ports:', apiError(res as ApiResult<Record<string, unknown>>))
        return []
      }
      return res.ports ?? []
    }
    if (DEMO_MODE) return ['COM1', 'COM2', 'COM3']
    return []
  },

  async saveSettings(settings: SerialSettings): Promise<void> {
    if (isEelReady()) {
      failIfNotOk(await eelCall<ApiResult>('save_settings', settings))
      return
    }
    if (DEMO_MODE) return
    throw new Error('Бэкенд недоступен')
  },

  async openPhysicalChannel(): Promise<string[]> {
    if (isEelReady()) {
      const res = failIfNotOk(
        await eelCall<ApiResult<{ ports?: string[] }>>('open_physical_channel'),
      )
      return res.ports ?? []
    }
    if (DEMO_MODE) return ['COM1', 'COM2']
    throw new Error('Бэкенд недоступен')
  },

  async closePhysicalChannel(): Promise<void> {
    if (isEelReady()) {
      failIfNotOk(await eelCall<ApiResult>('close_physical_channel'))
      return
    }
    if (DEMO_MODE) return
    throw new Error('Бэкенд недоступен')
  },

  async connectLogical(): Promise<void> {
    if (isEelReady()) {
      failIfNotOk(await eelCall<ApiResult>('connect_logical'))
      return
    }
    if (DEMO_MODE) return
    throw new Error('Бэкенд недоступен')
  },

  async disconnectLogical(): Promise<void> {
    if (isEelReady()) {
      failIfNotOk(await eelCall<ApiResult>('disconnect_logical'))
      return
    }
    if (DEMO_MODE) return
    throw new Error('Бэкенд недоступен')
  },

  async sendMessage(text: string, destination: Destination): Promise<void> {
    if (isEelReady()) {
      const dest = destinationToApiArg(normalizeDestination(destination))
      const body = String(text ?? '').trim()
      failIfNotOk(await eelCall<ApiResult>('send_message', body, dest))
      return
    }
    if (DEMO_MODE) return
    throw new Error('Бэкенд недоступен')
  },

  /** Short poll: сообщение из очереди или null (пустая очередь — не ошибка). */
  async pollMessage(): Promise<string | null> {
    if (!isEelReady()) return null
    const res = await eelCall<ApiResult<{ message?: string }>>('get_message')
    if (res.ok && res.message != null && String(res.message).length > 0) {
      return String(res.message)
    }
    return null
  },
}
