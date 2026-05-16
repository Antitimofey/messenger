import { Modal } from '../ui/Modal'
import type {
  NodeAddress,
  ParityCode,
  PortLineSettings,
  SerialSettings,
} from '../../types'
import { BAUD_RATES, PARITY_LABELS } from '../../types'

type Props = {
  open: boolean
  settings: SerialSettings
  ports: string[]
  onChange: (s: SerialSettings) => void
  onClose: () => void
  onApply: () => void
}

const PARITY_OPTIONS = (Object.keys(PARITY_LABELS) as ParityCode[]).map((code) => ({
  value: code,
  label: PARITY_LABELS[code],
}))

type PortParamsProps = {
  legend: string
  line: PortLineSettings
  onChange: (line: PortLineSettings) => void
}

function PortParamsFields({ legend, line, onChange }: PortParamsProps) {
  const patch = (partial: Partial<PortLineSettings>) =>
    onChange({ ...line, ...partial })

  return (
    <fieldset className="settings-group">
      <legend>{legend}</legend>
      <label className="settings-row">
        <span>Бит в секунду:</span>
        <select
          value={line.baudrate}
          onChange={(e) => patch({ baudrate: Number(e.target.value) })}
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
          value={line.bytesize}
          onChange={(e) =>
            patch({ bytesize: Number(e.target.value) as PortLineSettings['bytesize'] })
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
          value={line.parity}
          onChange={(e) => patch({ parity: e.target.value as ParityCode })}
        >
          {PARITY_OPTIONS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </label>
      <label className="settings-row">
        <span>Стоповые биты:</span>
        <select
          value={String(line.stopbits)}
          onChange={(e) =>
            patch({
              stopbits: parseFloat(e.target.value) as PortLineSettings['stopbits'],
            })
          }
        >
          <option value="1">One</option>
          <option value="1.5">OnePointFive</option>
          <option value="2">Two</option>
        </select>
      </label>
    </fieldset>
  )
}

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
      width="lg"
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

        <PortParamsFields
          legend="Параметры COM1 (в кольцо)"
          line={settings.com1}
          onChange={(com1) => patch({ com1 })}
        />
        <PortParamsFields
          legend="Параметры COM2 (из кольца)"
          line={settings.com2}
          onChange={(com2) => patch({ com2 })}
        />

        <p className="form-note">
          OK сохраняет параметры. Физический канал открывается отдельной командой в окне
          «Соединение».
        </p>
      </form>
    </Modal>
  )
}
