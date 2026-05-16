export type ConnectionState = 'disconnected' | 'connecting' | 'connected'

export type FrameTypeCode = 0x00 | 0x01 | 0x02 | 0x03 | 0x04 | 0x05

export type ParityOption = 'none' | 'even' | 'odd' | 'mark' | 'space'
export type FlowControlOption = 'none' | 'hardware' | 'software'
export type NodeAddress = 1 | 2 | 3
export type Destination = NodeAddress | 'broadcast'

export interface SerialSettings {
  portCom1: string
  portCom2: string
  nodeAddress: NodeAddress
  baudRate: number
  dataBits: 5 | 6 | 7 | 8
  parity: ParityOption
  stopBits: 1 | 1.5 | 2
  flowControl: FlowControlOption
  readTimeout: number
  writeTimeout: number
  readBufferSize: number
  writeBufferSize: number
}

export const DEFAULT_SETTINGS: SerialSettings = {
  portCom1: 'COM1',
  portCom2: 'COM2',
  nodeAddress: 1,
  baudRate: 9600,
  dataBits: 8,
  parity: 'none',
  stopBits: 1,
  flowControl: 'none',
  readTimeout: 1000,
  writeTimeout: 1000,
  readBufferSize: 4096,
  writeBufferSize: 2048,
}

export const DEFAULT_DESTINATION: Destination = 2

export const BAUD_RATES = [
  300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 56000, 57600, 115200,
  128000,
] as const

export interface LogEntry {
  id: string
  time: string
  level: 'info' | 'success' | 'warn' | 'error' | 'frame'
  message: string
  frame?: FrameTypeCode
}

export const SETTINGS_STORAGE_KEY = 'lbs-serial-settings'
export const DESTINATION_STORAGE_KEY = 'lbs-destination'

/** Ответ бэкенда (req.py) */
export type ApiOk<T extends Record<string, unknown> = Record<string, never>> = {
  ok: true
} & T

export type ApiErr = { ok: false; error: string }

export type ApiResult<T extends Record<string, unknown> = Record<string, never>> =
  | ApiOk<T>
  | ApiErr
