import type { ApiResult } from '../types'

export interface EelApi {
  list_ports(): Promise<ApiResult<{ ports: string[] }>>
  save_settings(settings: unknown): Promise<ApiResult>
  open_physical_channel(): Promise<ApiResult<{ ports?: string[] }>>
  close_physical_channel(): Promise<ApiResult>
  connect_logical(): Promise<ApiResult>
  disconnect_logical(): Promise<ApiResult>
  send_message(text: string, destination: string): Promise<ApiResult>
  get_message(): Promise<ApiResult<{ message?: string }>>
}

declare global {
  interface Window {
    eel?: {
      expose: (fn: unknown, name?: string) => void
    } & {
      [K in keyof EelApi]: (
        ...args: Parameters<EelApi[K]>
      ) => () => ReturnType<EelApi[K]>
    }
    eel_host?: string
    eel_port?: number
  }
}

export {}
