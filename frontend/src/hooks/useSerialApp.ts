import { useCallback, useEffect, useRef, useState } from 'react'
import { api, DEMO_MODE, isEelLoaded, isEelReady } from '../api/client'
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
  normalizeSerialSettings,
  SETTINGS_STORAGE_KEY,
} from '../types'

const POLL_MS = 1000

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

function loadSerialSettings(): SerialSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
    return raw ? normalizeSerialSettings(JSON.parse(raw)) : DEFAULT_SETTINGS
  } catch {
    return DEFAULT_SETTINGS
  }
}

export function useSerialApp() {
  const [settings, setSettings] = useState<SerialSettings>(loadSerialSettings)
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
  const [eelConnected, setEelConnected] = useState(isEelReady)
  const pollInFlight = useRef(false)

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
    const check = () => setEelConnected(isEelReady())
    check()
    const id = window.setInterval(check, 300)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    if (DEMO_MODE || eelConnected) return
    if (isEelLoaded()) {
      pushLog('warn', 'Ожидание WebSocket к бэкенду…')
      return
    }
    pushLog('warn', 'Бэкенд не подключён. Запустите: python backend/run_server.py')
  }, [eelConnected, pushLog])

  useEffect(() => {
    api
      .listPorts()
      .then(setPorts)
      .catch(() => {
        pushLog('warn', 'Не удалось загрузить список портов')
        setPorts(['COM1', 'COM2', 'COM3'])
      })
  }, [pushLog, eelConnected])

  // get_message на бэке требует открытый логический канал — не опрашиваем раньше времени
  useEffect(() => {
    if (!eelConnected || connection !== 'connected') return

    const poll = async () => {
      if (pollInFlight.current) return
      pollInFlight.current = true
      try {
        const msg = await api.pollMessage()
        if (msg) {
          pushLog('success', `Получено сообщение: ${msg}`)
        }
      } catch (e) {
        pushLog('error', e instanceof Error ? e.message : 'Ошибка опроса get_message')
      } finally {
        pollInFlight.current = false
      }
    }

    const id = window.setInterval(() => {
      void poll()
    }, POLL_MS)

    return () => window.clearInterval(id)
  }, [eelConnected, connection, pushLog])

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
      if (connection === 'connected') {
        await api.disconnectLogical()
        setConnection('disconnected')
      }
      await api.closePhysicalChannel()
      setPortOpen(false)
      setOpenPorts([])
      pushLog('info', 'Физический канал закрыт')
    } catch (e) {
      pushLog('error', e instanceof Error ? e.message : 'Ошибка закрытия канала')
    } finally {
      setBusy(false)
    }
  }, [connection, pushLog])

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
        await api.sendMessage(trimmed, destination)
        pushLog('success', `Сообщение отправлено (${destLabel})`)
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
    eelConnected,
  }
}
