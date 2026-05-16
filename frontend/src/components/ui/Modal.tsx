import { useEffect, type ReactNode } from 'react'

type Props = {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
  width?: 'sm' | 'md' | 'lg'
  footer?: ReactNode
}

export function Modal({
  open,
  title,
  onClose,
  children,
  width = 'md',
  footer,
}: Props) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className={`win-dialog win-dialog--${width}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="win-dialog__titlebar" id="modal-title">
          {title}
        </div>
        <div className="win-dialog__body">{children}</div>
        {footer && <div className="win-dialog__footer">{footer}</div>}
      </div>
    </div>
  )
}
