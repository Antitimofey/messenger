export type ConnectionState = 'disconnected' | 'connecting' | 'connected'

export type FrameTypeCode = 0x00 | 0x01 | 0x02 | 0x03 | 0x04 | 0x05

/** Код четности pyserial / COMPortSettings.parity */
export type ParityCode = 'N' | 'E' | 'O'

export type NodeAddress = 1 | 2 | 3
export type Destination = NodeAddress | 'broadcast'

/** Параметры линии (без имени порта) — соответствует полям COMPortSettings в physical.py */
export interface PortLineSettings {
  baudrate: number
  bytesize: 5 | 6 | 7 | 8
  parity: ParityCode
  stopbits: 1 | 1.5 | 2
  timeout: number
}

/**
 * Параметры COM-порта — зеркало dataclass COMPortSettings из phisical/physical.py
 */
export interface COMPortSettings {
  portName: string
  baudrate: number
  bytesize: 5 | 6 | 7 | 8
  parity: ParityCode
  stopbits: 1 | 1.5 | 2
  timeout: number
}

/** Настройки приложения: два порта кольца + адрес узла */
export interface SerialSettings {
  portCom1: string
  portCom2: string
  nodeAddress: NodeAddress
  com1: PortLineSettings
  com2: PortLineSettings
}

export const DEFAULT_DESTINATION: Destination = 2

/** Нормализация получателя из state / localStorage / select */
export function normalizeDestination(raw: unknown): Destination {
  if (raw === 'broadcast' || raw === 0 || raw === '0') return 'broadcast'
  const n = typeof raw === 'number' ? raw : Number(raw)
  if (n === 1 || n === 2 || n === 3) return n as NodeAddress
  return DEFAULT_DESTINATION
}

/** Строка для Eel/Python: "1" | "2" | "3" | "broadcast" */
export function destinationToApiArg(destination: Destination): string {
  return destination === 'broadcast' ? 'broadcast' : String(destination)
}

export const BAUD_RATES = [
  300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 56000, 57600, 115200,
  128000,
] as const

export const DEFAULT_PORT_LINE: PortLineSettings = {
  baudrate: 9600,
  bytesize: 8,
  parity: 'N',
  stopbits: 1,
  timeout: 1,
}

export const DEFAULT_SETTINGS: SerialSettings = {
  portCom1: 'COM1',
  portCom2: 'COM2',
  nodeAddress: 1,
  com1: { ...DEFAULT_PORT_LINE },
  com2: { ...DEFAULT_PORT_LINE },
}

const PARITY_UI_TO_CODE: Record<string, ParityCode> = {
  none: 'N',
  even: 'E',
  odd: 'O',
  N: 'N',
  E: 'E',
  O: 'O',
}

export function parityUiToCode(value: string): ParityCode {
  return PARITY_UI_TO_CODE[value.toLowerCase()] ?? 'N'
}

export const PARITY_LABELS: Record<ParityCode, string> = {
  N: 'None',
  E: 'Even',
  O: 'Odd',
}

export function buildCOMPortSettings(
  portName: string,
  line: PortLineSettings,
): COMPortSettings {
  return { portName, ...line }
}

/** Миграция старого формата (один набор параметров на оба порта) */
export function normalizeSerialSettings(raw: unknown): SerialSettings {
  if (!raw || typeof raw !== 'object') return { ...DEFAULT_SETTINGS }

  const s = raw as Record<string, unknown>
  if (s.com1 && s.com2) {
    return {
      ...DEFAULT_SETTINGS,
      ...s,
      com1: { ...DEFAULT_PORT_LINE, ...(s.com1 as PortLineSettings) },
      com2: { ...DEFAULT_PORT_LINE, ...(s.com2 as PortLineSettings) },
    } as SerialSettings
  }

  const legacyLine: PortLineSettings = {
    baudrate: Number(s.baudRate ?? DEFAULT_PORT_LINE.baudrate),
    bytesize: Number(s.dataBits ?? DEFAULT_PORT_LINE.bytesize) as PortLineSettings['bytesize'],
    parity: parityUiToCode(String(s.parity ?? 'none')),
    stopbits: Number(s.stopBits ?? DEFAULT_PORT_LINE.stopbits) as PortLineSettings['stopbits'],
    timeout: DEFAULT_PORT_LINE.timeout,
  }

  return {
    portCom1: String(s.portCom1 ?? DEFAULT_SETTINGS.portCom1),
    portCom2: String(s.portCom2 ?? DEFAULT_SETTINGS.portCom2),
    nodeAddress: (Number(s.nodeAddress) || 1) as NodeAddress,
    com1: { ...legacyLine },
    com2: { ...legacyLine },
  }
}

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
