import { Modal } from '../ui/Modal'
import type { SerialSettings } from '../../types'

type Props = {
  open: boolean
  settings: SerialSettings
  onClose: () => void
}

export function PortAlert({ open, settings, onClose }: Props) {
  const footer = (
    <button type="button" className="btn btn--primary" onClick={onClose}>
      OK
    </button>
  )

  return (
    <Modal
      open={open}
      title="Открытие COM-порта"
      onClose={onClose}
      width="sm"
      footer={footer}
    >
      <p className="alert-message">
        Физический канал открыт: {settings.portCom1}, {settings.portCom2}
      </p>
    </Modal>
  )
}
