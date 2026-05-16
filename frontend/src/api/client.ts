import type { ApiResult, Destination, SerialSettings } from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function hasEel(): boolean {
  return typeof window !== 'undefined' && typeof window.eel !== 'undefined'
}

export const DEMO_MODE =
  !hasEel() && import.meta.env.VITE_DEMO_MODE !== 'false'

export const EEL_MODE = hasEel()

async function eelCall<T>(name: string, ...args: unknown[]): Promise<T> {
  const eel = window.eel as unknown as Record<
    string,
    (...a: unknown[]) => () => Promise<T>
  >
  const fn = eel[name]
  if (!fn) throw new Error(`Eel: функция ${name} не найдена`)
  return fn(...args)()
}

function unwrap<T extends Record<string, unknown>>(
  res: ApiResult<T>,
  fallbackError = 'Ошибка сервера',
): ApiOkFields<T> {
  if (!res.ok) throw new Error(res.error || fallbackError)
  return res
}

type ApiOkFields<T> = { ok: true } & T

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text || `HTTP ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  async listPorts(): Promise<string[]> {
    if (EEL_MODE) {
      const res = await eelCall<ApiResult<{ ports: string[] }>>('list_ports')
      return unwrap(res).ports ?? []
    }
    if (DEMO_MODE) return ['COM1', 'COM2', 'COM3']
    return request<string[]>('/api/ports')
  },

  async saveSettings(settings: SerialSettings): Promise<void> {
    if (EEL_MODE) {
      unwrap(await eelCall<ApiResult>('save_settings', settings))
      return
    }
    if (DEMO_MODE) return
    await request('/api/settings', { method: 'PUT', body: JSON.stringify(settings) })
  },

  async openPhysicalChannel(): Promise<string[]> {
    if (EEL_MODE) {
      const res = await eelCall<ApiResult<{ ports: string[] }>>('open_physical_channel')
      return unwrap(res).ports
    }
    if (DEMO_MODE) return ['COM1', 'COM2']
    const r = await request<{ ports: string[] }>('/api/connection/open', { method: 'POST' })
    return r.ports
  },

  async closePhysicalChannel(): Promise<void> {
    if (EEL_MODE) {
      unwrap(await eelCall<ApiResult>('close_physical_channel'))
      return
    }
    if (DEMO_MODE) return
    await request('/api/connection/close', { method: 'POST' })
  },

  async connectLogical(): Promise<void> {
    if (EEL_MODE) {
      unwrap(await eelCall<ApiResult>('connect_logical'))
      return
    }
    if (DEMO_MODE) return
    await request('/api/link/connect', { method: 'POST' })
  },

  async disconnectLogical(): Promise<void> {
    if (EEL_MODE) {
      unwrap(await eelCall<ApiResult>('disconnect_logical'))
      return
    }
    if (DEMO_MODE) return
    await request('/api/link/disconnect', { method: 'POST' })
  },

  async sendMessage(text: string, destination: Destination): Promise<void> {
    if (EEL_MODE) {
      unwrap(await eelCall<ApiResult>('send_message', text, destination))
      return
    }
    if (DEMO_MODE) return
    await request('/api/messages/send', {
      method: 'POST',
      body: JSON.stringify({ text, destination }),
    })
  },
}
