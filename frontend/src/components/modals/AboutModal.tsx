import cableImg from '../../assets/serial-cable.svg'
import { Modal } from '../ui/Modal'

type Props = {
  open: boolean
  onClose: () => void
}

export function AboutModal({ open, onClose }: Props) {
  const footer = (
    <button type="button" className="btn btn--primary" onClick={onClose}>
      OK
    </button>
  )

  return (
    <Modal open={open} title="О программе" onClose={onClose} width="lg" footer={footer}>
      <div className="about">
        <p className="about__heading">
          Локальная безадаптерная сеть — передача двоичных файлов и сообщений
        </p>
        <div className="about__body">
          <img src={cableImg} alt="" className="about__cable" width={120} height={80} />
          <div className="about__authors">
            <p className="about__authors-title">Выполнили (ИУ5-61Б):</p>
            <ul>
              <li>Сысоев И.А. — прикладной уровень</li>
              <li>Антипов Т.И. — канальный уровень</li>
              <li>Гапонов Р.Д. — физический уровень</li>
            </ul>
          </div>
        </div>
        <p className="about__dept">
          Кафедра ИУ5 · Сетевые технологии в АСОИУ
          <br />
          Вариант №4 · кольцо RS-232 · CRC [7,4]
          <br />
          Москва, 2025
        </p>
      </div>
    </Modal>
  )
}
