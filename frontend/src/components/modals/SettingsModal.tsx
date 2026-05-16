import { Modal } from '../ui/Modal'
import type { FlowControlOption, NodeAddress, ParityOption, SerialSettings } from '../../types'
import { BAUD_RATES } from '../../types'

type Props = {
  open: boolean
  settings: SerialSettings
  ports: string[]
  onChange: (s: SerialSettings) => void
  onClose: () => void
  onApply: () => void
}

const PARITY: { value: ParityOption; label: string }[] = [
  { value: 'none', label: 'None' },
  { value: 'even', label: 'Even' },
  { value: 'odd', label: 'Odd' },
]

const FLOW: { value: FlowControlOption; label: string }[] = [
  { value: 'none', label: 'None' },
  { value: 'hardware', label: 'Hardware' },
  { value: 'software', label: 'Software' },
]

export function SettingsModal({
  open,
  settings,
  ports,
  onChange,
  onClose,
  onApply,
}: Props) {
  const patch = (partial: Partial<SerialSettings>) =>
    onChange({ ...settings, ...partial })

  const portOptions = [...new Set([...ports, settings.portCom1, settings.portCom2])]

  const footer = (
    <>
      <button type="button" className="btn btn--primary" onClick={onApply}>
        OK
      </button>
      <button type="button" className="btn" onClick={onClose}>
        Отмена
      </button>
    </>
  )

  return (
    <Modal
      open={open}
      title="Параметры соединения"
      onClose={onClose}
      width="md"
      footer={footer}
    >
      <form
        className="settings-form"
        onSubmit={(e) => {
          e.preventDefault()
          onApply()
        }}
      >
        <fieldset className="settings-group">
          <legend>Последовательный порт (кольцо RS-232)</legend>
          <label className="settings-row">
            <span>COM1 (в кольцо):</span>
            <select
              value={settings.portCom1}
              onChange={(e) => patch({ portCom1: e.target.value })}
            >
              {portOptions.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label className="settings-row">
            <span>COM2 (из кольца):</span>
            <select
              value={settings.portCom2}
              onChange={(e) => patch({ portCom2: e.target.value })}
            >
              {portOptions.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label className="settings-row">
            <span>Адрес этого узла:</span>
            <select
              value={settings.nodeAddress}
              onChange={(e) =>
                patch({ nodeAddress: Number(e.target.value) as NodeAddress })
              }
            >
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
          </label>
        </fieldset>

        <fieldset className="settings-group">
          <legend>Параметры порта</legend>
          <label className="settings-row">
            <span>Бит в секунду:</span>
            <select
              value={settings.baudRate}
              onChange={(e) => patch({ baudRate: Number(e.target.value) })}
            >
              {BAUD_RATES.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
          </label>
          <label className="settings-row">
            <span>Биты данных:</span>
            <select
              value={settings.dataBits}
              onChange={(e) =>
                patch({ dataBits: Number(e.target.value) as SerialSettings['dataBits'] })
              }
            >
              {[5, 6, 7, 8].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
          <label className="settings-row">
            <span>Четность:</span>
            <select
              value={settings.parity}
              onChange={(e) => patch({ parity: e.target.value as ParityOption })}
            >
              {PARITY.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <label className="settings-row">
            <span>Стоповые биты:</span>
            <select
              value={String(settings.stopBits)}
              onChange={(e) =>
                patch({
                  stopBits: parseFloat(e.target.value) as SerialSettings['stopBits'],
                })
              }
            >
              <option value="1">One</option>
              <option value="1.5">OnePointFive</option>
              <option value="2">Two</option>
            </select>
          </label>
        </fieldset>
        <p className="form-note">
          OK сохраняет параметры. Физический канал открывается отдельной командой в окне
          «Соединение».
        </p>
      </form>
    </Modal>
  )
}
