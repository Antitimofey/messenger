

import threading
import sys
from pathlib import Path
from queue import Queue

# Настройка путей
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from phisical.physical import COMPort
from channel.frame.encryptedFrame import EncryptedFrame
from channel.frame.frame import FrameType

MY_ADDR = 1
BROADCAST = 0


class SerialTracker:
    def __init__(self, rx: COMPort, tx: COMPort, my_addr: int = MY_ADDR, broadcast_addr: int = BROADCAST):
        self.rx = rx
        self.tx = tx
        self.my_addr = my_addr
        self.broadcast_addr = broadcast_addr
        
        # queue.Queue потокобезопасна из коробки, семафоры не нужны
        self.queue = Queue() 
        
        # Флаг для контроля работы потока
        self._is_running = False
        self.listening_thread = None


    def send_message(self, dest_addr: int, message_text: str):
            """
            Конвертирует строку в EncryptedFrame и отправляет в TX порт.
            :param dest_addr: Адрес получателя (ID узла или BROADCAST)
            :param message_text: Текст сообщения для отправки
            """
            try:
                # Кодируем текст в байты и создаем объект кадра
                frame = EncryptedFrame(
                    dest_addr=dest_addr, 
                    src_addr=self.my_addr, 
                    frame_type=FrameType.DATA, 
                    data=message_text.encode('utf-8')
                )
                # Сериализуем и отправляем в порт
                self.tx.send_bytes(frame.encrypted_serialize())
            except Exception as e:
                print(f"\n⚠️ Ошибка при отправке сообщения: {e}")


    def receive_message(self):
        buffer = bytearray()
        
        while self._is_running:
            try:
                # Читаем по 1 байту, как в рабочей логике
                byte = self.rx.receive_bytes(1)
                if not byte:
                    continue
                
                buffer.extend(byte)
                
                # Проверяем маркеры кадра 0x7E
                if len(buffer) >= 2 and buffer[0] == 0x7E and buffer[-1] == 0x7E:
                    try:
                        frame = EncryptedFrame(raw_bytes=bytes(buffer))
                        
                        if frame.src_addr == self.my_addr:
                            print("\n🔄 Мое сообщение вернулось (круг пройден).")
                            
                        else:
                            # Проверяем, нам ли сообщение
                            if frame.dest_addr == self.my_addr or frame.dest_addr == self.broadcast_addr:
                                text_msg = frame.get_data_as_text()
                                log_entry = f"Сообщение от {frame.src_addr}: {text_msg}"
                                
                                print(f"\n📥 {log_entry}")
                                # Кладываем строку в потокобезопасную очередь
                                self.queue.put(text_msg)
                            
                            # Если адресовано не нам (или это broadcast), ретранслируем дальше
                            if frame.dest_addr != self.my_addr:
                                print(f"⏩ Ретрансляция сообщения от {frame.src_addr}...")
                                self.tx.send_bytes(bytes(buffer))
                                
                    except Exception as e:
                        print(f"\n⚠️ Ошибка кадра: {e}")
                    finally:
                        buffer.clear()
                        print("> ", end="", flush=True)
                        
            except Exception as e:
                print(f"\n⚠️ Ошибка при чтении из порта: {e}")

    def start_listening(self):
        if self._is_running:
            return
        
        # Проверяем, что оба порта открыты
        assert self.rx.open_port(), "Необходимо сначала открыть RX порт!"
        assert self.tx.open_port(), "Необходимо сначала открыть TX порт!"
        
        self._is_running = True
        self.listening_thread = threading.Thread(target=self.receive_message, daemon=True)
        self.listening_thread.start()

    def stop_listening(self):
        """ Корректная остановка потока """
        self._is_running = False
        if self.listening_thread:
            self.listening_thread.join(timeout=2)

    def get_message(self):
        """ Извлечение сообщения из очереди главным (или другим) потоком """
        if not self.queue.empty():
            return self.queue.get()
        return None





# === Пример использования обновленного класса в main ===

def main():
    from channel.stack.requirements import COMPortSettings

    rx_set = COMPortSettings(port_name='COM15', baudrate=19200)
    tx_set = COMPortSettings(port_name='COM10', baudrate=19200)
    
    rx = COMPort('input', rx_set)
    tx = COMPort('output', tx_set)
    
    # Инициализируем трекер логики
    tracker = SerialTracker(rx, tx, my_addr=MY_ADDR, broadcast_addr=BROADCAST)
    
    try:
        tracker.start_listening()
    except AssertionError as e:
        print(f"❌ {e}")
        return

    print(f"=== Узел {MY_ADDR} запущен. Команды: send <addr> <msg>, exit ===")

    while True:
        try:
            # Проверяем, появилось ли что-то в очереди (пример извлечения из основного потока)
            msg_from_queue = tracker.get_message()
            if msg_from_queue:
                # Здесь можно писать в файл, на интерфейс и т.д.
                # msg_from_queue уже содержит готовую строку
                pass

            # Чтение ввода (учтите, что input() блокирует поток, 
            # но для демонстрации отправки это ок)
            inp = input("> ").split(" ", 2)
            if inp[0] == "exit": 
                break
                
            if inp[0] == "send" and len(inp) == 3:
                dest = BROADCAST if inp[1].lower() == "broadcast" else int(inp[1])
                msg = EncryptedFrame(dest, MY_ADDR, FrameType.DATA, inp[2].encode('utf-8'))
                tx.send_bytes(msg.encrypted_serialize())
                
        except KeyboardInterrupt: 
            break
        except Exception as e: 
            print(f"Ошибка в основном цикле: {e}")
            
    tracker.stop_listening()

if __name__ == "__main__":
    main()

