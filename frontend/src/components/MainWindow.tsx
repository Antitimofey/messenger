import { useEffect, useRef } from 'react'
import type { ConnectionState, Destination, LogEntry, SerialSettings } from '../types'

type Props = {
  settings: SerialSettings
  destination: Destination
  onDestinationChange: (d: Destination) => void
  connection: ConnectionState
  portOpen: boolean
  busy: boolean
  logs: LogEntry[]
  onSendMessage: (text: string) => void
  onOpenPhysical: () => void
  onClosePhysical: () => void
  onConnect: () => void
  onDisconnect: () => void
  onSettings: () => void
  onExit: () => void
}

function statusText(connection: ConnectionState, portOpen: boolean) {
  if (!portOpen) return 'Соединение не установлено'
  if (connection === 'connecting') return 'Установка соединения…'
  if (connection === 'connected') return 'Соединение установлено'
  return 'Соединение не установлено'
}

function statusClass(connection: ConnectionState, portOpen: boolean) {
  if (!portOpen || connection === 'disconnected') return 'status--bad'
  if (connection === 'connecting') return 'status--wait'
  return 'status--ok'
}

export function MainWindow({
  settings,
  destination,
  onDestinationChange,
  connection,
  portOpen,
  busy,
  logs,
  onSendMessage,
  onOpenPhysical,
  onClosePhysical,
  onConnect,
  onDisconnect,
  onSettings,
  onExit,
}: Props) {
  const logRef = useRef<HTMLDivElement>(null)
  const messageRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const el = logRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [logs])

  const connected = connection === 'connected'
  const canSend = connected && !busy

  return (
    <div className="main-window">
      <fieldset className="group group--send-message">
        <legend>Отправить сообщение</legend>
        <div className="send-message-grid">
          <label className="send-message-grid__label" htmlFor="msg-destination">
            Получатель:
          </label>
          <select
            id="msg-destination"
            className="send-message-grid__control"
            value={String(destination)}
            onChange={(e) => {
              const v = e.target.value
              onDestinationChange(
                v === 'broadcast' ? 'broadcast' : (Number(v) as 1 | 2 | 3),
              )
            }}
            disabled={busy}
          >
            <option value="1">Узел 1</option>
            <option value="2">Узел 2</option>
            <option value="3">Узел 3</option>
            <option value="broadcast">Всем (широковещание)</option>
          </select>
          <label className="send-message-grid__label" htmlFor="msg-text">
            Текст сообщения:
          </label>
          <input
            id="msg-text"
            ref={messageRef}
            type="text"
            className="send-message-grid__control"
            disabled={!connected || busy}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && canSend) {
                onSendMessage(messageRef.current?.value ?? '')
                if (messageRef.current) messageRef.current.value = ''
              }
            }}
          />
          <div className="send-message-grid__actions">
            <button
              type="button"
              className="btn"
              disabled={!canSend}
              onClick={() => {
                onSendMessage(messageRef.current?.value ?? '')
                if (messageRef.current) messageRef.current.value = ''
              }}
            >
              Отправить сообщение
            </button>
          </div>
        </div>
      </fieldset>

      <fieldset className="group group--connection">
        <legend>Соединение</legend>
        <div className="connection-split">
          <div className="connection-left">
            <p className="connection-left__caption">Статус соединения</p>
            <p className={`connection-status ${statusClass(connection, portOpen)}`}>
              {statusText(connection, portOpen)}
            </p>
            <div className="connection-buttons">
              {!portOpen ? (
                <button type="button" className="btn" disabled={busy} onClick={onOpenPhysical}>
                  Установить физический канал
                </button>
              ) : (
                <button type="button" className="btn" disabled={busy} onClick={onClosePhysical}>
                  Закрыть физический канал
                </button>
              )}
              {connected ? (
                <button type="button" className="btn" disabled={busy} onClick={onDisconnect}>
                  Разорвать соединение
                </button>
              ) : (
                <button
                  type="button"
                  className="btn"
                  disabled={busy || !portOpen || connection === 'connecting'}
                  onClick={onConnect}
                >
                  Установить соединение
                </button>
              )}
              <button type="button" className="btn" disabled={busy} onClick={onSettings}>
                Параметры соединения
              </button>
            </div>
          </div>
          <div className="connection-right">
            <p className="connection-right__caption">Системные сообщения</p>
            <div className="log-area" ref={logRef} role="log" aria-live="polite">
              {logs.length === 0 ? (
                <span className="log-area__empty">&nbsp;</span>
              ) : (
                logs.map((entry) => (
                  <div key={entry.id} className={`log-line log-line--${entry.level}`}>
                    <span className="log-line__time">[{entry.time}]</span> {entry.message}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </fieldset>

      <div className="main-window__footer">
        <button type="button" className="btn" onClick={onExit}>
          Выход
        </button>
      </div>
    </div>
  )
}
