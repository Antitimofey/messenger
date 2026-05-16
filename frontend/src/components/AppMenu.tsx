import { useEffect, useRef, useState } from 'react'

type MenuId = 'file' | 'connection' | 'help' | null

type Props = {
  connected: boolean
  portOpen: boolean
  busy: boolean
  onExit: () => void
  onOpenPhysical: () => void
  onClosePhysical: () => void
  onConnect: () => void
  onDisconnect: () => void
  onSettings: () => void
  onAbout: () => void
}

export function AppMenu({
  connected,
  portOpen,
  busy,
  onExit,
  onOpenPhysical,
  onClosePhysical,
  onConnect,
  onDisconnect,
  onSettings,
  onAbout,
}: Props) {
  const [open, setOpen] = useState<MenuId>(null)
  const barRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (barRef.current && !barRef.current.contains(e.target as Node)) {
        setOpen(null)
      }
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const pick = (_menu: MenuId, action: () => void) => {
    setOpen(null)
    action()
  }

  return (
    <nav className="app-menu" ref={barRef} aria-label="Меню">
      <div className="app-menu__item">
        <button
          type="button"
          className={open === 'file' ? 'active' : ''}
          onClick={() => setOpen(open === 'file' ? null : 'file')}
        >
          Файл
        </button>
        {open === 'file' && (
          <ul className="app-menu__dropdown">
            <li>
              <button type="button" onClick={() => pick('file', onExit)}>
                Выход
              </button>
            </li>
          </ul>
        )}
      </div>

      <div className="app-menu__item">
        <button
          type="button"
          className={open === 'connection' ? 'active' : ''}
          onClick={() => setOpen(open === 'connection' ? null : 'connection')}
        >
          Соединение
        </button>
        {open === 'connection' && (
          <ul className="app-menu__dropdown">
            <li>
              <button
                type="button"
                disabled={portOpen || busy}
                onClick={() => pick('connection', onOpenPhysical)}
              >
                Установить физический канал
              </button>
            </li>
            <li>
              <button
                type="button"
                disabled={!portOpen || busy}
                onClick={() => pick('connection', onClosePhysical)}
              >
                Закрыть физический канал
              </button>
            </li>
            <li className="sep" />
            <li>
              <button
                type="button"
                disabled={!portOpen || connected || busy}
                onClick={() => pick('connection', onConnect)}
              >
                Установить соединение
              </button>
            </li>
            <li>
              <button
                type="button"
                disabled={!connected || busy}
                onClick={() => pick('connection', onDisconnect)}
              >
                Разорвать соединение
              </button>
            </li>
            <li className="sep" />
            <li>
              <button type="button" onClick={() => pick('connection', onSettings)}>
                Параметры соединения…
              </button>
            </li>
          </ul>
        )}
      </div>

      <div className="app-menu__item">
        <button
          type="button"
          className={open === 'help' ? 'active' : ''}
          onClick={() => setOpen(open === 'help' ? null : 'help')}
        >
          Справка
        </button>
        {open === 'help' && (
          <ul className="app-menu__dropdown">
            <li>
              <button type="button" onClick={() => pick('help', onAbout)}>
                О программе…
              </button>
            </li>
          </ul>
        )}
      </div>
    </nav>
  )
}
