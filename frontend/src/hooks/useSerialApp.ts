import { useCallback, useEffect, useState } from 'react'
import { api, DEMO_MODE } from '../api/client'
import type {
  ConnectionState,
  Destination,
  FrameTypeCode,
  LogEntry,
  SerialSettings,
} from '../types'
import {
  DEFAULT_DESTINATION,
  DEFAULT_SETTINGS,
  DESTINATION_STORAGE_KEY,
  SETTINGS_STORAGE_KEY,
} from '../types'

function nowTime() {
  return new Date().toLocaleTimeString('ru-RU', { hour12: false })
}

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function loadJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? ({ ...fallback, ...JSON.parse(raw) } as T) : fallback
  } catch {
    return fallback
  }
}

export function useSerialApp() {
  const [settings, setSettings] = useState<SerialSettings>(() =>
    loadJson(SETTINGS_STORAGE_KEY, DEFAULT_SETTINGS),
  )
  const [destination, setDestination] = useState<Destination>(() =>
    loadJson(DESTINATION_STORAGE_KEY, DEFAULT_DESTINATION),
  )
  const [ports, setPorts] = useState<string[]>([])
  const [connection, setConnection] = useState<ConnectionState>('disconnected')
  const [portOpen, setPortOpen] = useState(false)
  const [openPorts, setOpenPorts] = useState<string[]>([])
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [portOpenedAlert, setPortOpenedAlert] = useState(false)
  const [busy, setBusy] = useState(false)

  const pushLog = useCallback(
    (level: LogEntry['level'], message: string, frame?: FrameTypeCode) => {
      setLogs((prev) => [
        ...prev.slice(-499),
        { id: uid(), time: nowTime(), level, message, frame },
      ])
    },
    [],
  )

  useEffect(() => {
    api
      .listPorts()
      .then(setPorts)
      .catch(() => {
        pushLog('warn', 'Не удалось загрузить список портов')
        setPorts(['COM1', 'COM2', 'COM3'])
      })
  }, [pushLog])

  const saveSettings = useCallback(async () => {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings))
    setBusy(true)
    try {
      await api.saveSettings(settings)
      pushLog('success', 'Параметры соединения сохранены')
    } catch (e) {
      pushLog('error', e instanceof Error ? e.message : 'Ошибка сохранения параметров')
    } finally {
      setBusy(false)
    }
  }, [settings, pushLog])

  const setDestinationAndStore = useCallback((d: Destination) => {
    setDestination(d)
    localStorage.setItem(DESTINATION_STORAGE_KEY, JSON.stringify(d))
  }, [])

  const openPhysical = useCallback(async () => {
    setBusy(true)
    try {
      const opened = await api.openPhysicalChannel()
      setPortOpen(true)
      setOpenPorts(opened)
      setPortOpenedAlert(true)
      pushLog('success', `Физический канал: ${opened.join(', ')}`)
    } catch (e) {
      pushLog('error', e instanceof Error ? e.message : 'Ошибка открытия канала')
    } finally {
      setBusy(false)
    }
  }, [pushLog])

  const closePhysical = useCallback(async () => {
    setBusy(true)
    try {
      await api.closePhysicalChannel()
      setPortOpen(false)
      setOpenPorts([])
      setConnection('disconnected')
      pushLog('info', 'Физический канал закрыт')
    } catch (e) {
      pushLog('error', e instanceof Error ? e.message : 'Ошибка закрытия канала')
    } finally {
      setBusy(false)
    }
  }, [pushLog])

  const connectLink = useCallback(async () => {
    if (!portOpen) {
      pushLog('warn', 'Сначала установите физический канал')
      return
    }
    setConnection('connecting')
    setBusy(true)
    try {
      await api.connectLogical()
      setConnection('connected')
      pushLog('frame', 'Логическое соединение установлено (L-кадр)', 0x01)
      if (DEMO_MODE) pushLog('frame', 'Ответ узла кольца', 0x01)
    } catch (e) {
      setConnection('disconnected')
      pushLog('error', e instanceof Error ? e.message : 'Ошибка соединения')
    } finally {
      setBusy(false)
    }
  }, [portOpen, pushLog])

  const disconnectLink = useCallback(async () => {
    setBusy(true)
    try {
      await api.disconnectLogical()
      setConnection('disconnected')
      pushLog('frame', 'Разрыв логического соединения (U-кадр)', 0x02)
    } catch (e) {
      pushLog('error', e instanceof Error ? e.message : 'Ошибка разрыва')
    } finally {
      setBusy(false)
    }
  }, [pushLog])

  const destLabel =
    destination === 'broadcast' ? 'всем (широковещание)' : `узлу ${destination}`

  const sendMessage = useCallback(
    async (text: string) => {
      if (connection !== 'connected') {
        pushLog('warn', 'Нет логического соединения')
        return
      }
      const trimmed = text.trim()
      if (!trimmed) {
        pushLog('warn', 'Введите текст сообщения')
        return
      }
      setBusy(true)
      try {
        if (DEMO_MODE) {
          pushLog('info', `Сообщение → ${destLabel}: ${trimmed}`)
          pushLog('frame', 'I-кадр, ACK', 0x03)
          pushLog('success', 'Сообщение доставлено')
        } else {
          await api.sendMessage(trimmed, destination)
          pushLog('success', `Сообщение отправлено (${destLabel})`)
        }
      } catch (e) {
        pushLog('error', e instanceof Error ? e.message : 'Ошибка отправки сообщения')
      } finally {
        setBusy(false)
      }
    },
    [connection, destination, destLabel, pushLog],
  )

  const clearLogs = useCallback(() => setLogs([]), [])

  return {
    settings,
    setSettings,
    destination,
    setDestination: setDestinationAndStore,
    ports,
    connection,
    portOpen,
    openPorts,
    logs,
    portOpenedAlert,
    setPortOpenedAlert,
    busy,
    saveSettings,
    openPhysical,
    closePhysical,
    connectLink,
    disconnectLink,
    sendMessage,
    clearLogs,
    demoMode: DEMO_MODE,
  }
}
