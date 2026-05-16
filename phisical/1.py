import sys
import threading
from pathlib import Path

# 1. Настройка путей. 
# resolve().parent.parent выводит нас в D:\messenger\messenger
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# 2. Импорт из файла physical.py, который лежит в той же папке
try:
    from physical import COMPort
except ImportError:
    # Если папка называется phisical (через i), а не physical
    from phisical import COMPort

# 3. Импорты из папки channel
from channel.stack.requirements import COMPortSettings
from channel.frame.encryptedFrame import EncryptedFrame
from channel.frame.frame import FrameType

MY_ADDRESS = 1
BROADCAST = 0x00

def main():
    print(f"=== Узел {MY_ADDRESS} запущен ===")
    
    # Настройка портов
    rx_set = COMPortSettings(port_name='COM15', baudrate=19200)
    tx_set = COMPortSettings(port_name='COM10', baudrate=19200)

    rx = COMPort('input')
    tx = COMPort('output')

    if not rx.open_port(rx_set) or not tx.open_port(tx_set):
        print("❌ Ошибка открытия портов. Проверьте com0com.")
        return

    def receive_logic():
        buffer = bytearray()
        while rx.is_open():
            byte = rx.receive_bytes(1)
            if byte:
                buffer.extend(byte)
                # Ищем кадр, ограниченный флагами 0x7E
                if len(buffer) >= 2 and buffer[0] == 0x7E and buffer[-1] == 0x7E:
                    try:
                        # Пытаемся обработать защищенный кадр (Хэмминг + CRC)
                        frame = EncryptedFrame(raw_bytes=bytes(buffer))
                        
                        if frame.src_addr == MY_ADDRESS:
                            print("\n🔄 Сообщение совершило круг и удалено.")
                        else:
                            # Проверяем, нам ли сообщение
                            if frame.dest_addr == MY_ADDRESS or frame.dest_addr == BROADCAST:
                                print(f"\n📥 ПОЛУЧЕНО от Узла {frame.src_addr}: {frame.get_data_as_text()}")
                            
                            # Ретрансляция, если не нам или это broadcast
                            if frame.dest_addr != MY_ADDRESS:
                                print(f"⏩ Ретрансляция сообщения от Узла {frame.src_addr}...")
                                tx.send_bytes(bytes(buffer))
                        
                    except Exception as e:
                        print(f"\n⚠️ Ошибка кадра: {e}")
                    finally:
                        buffer.clear()
                        print("> ", end="", flush=True)
                elif len(buffer) > 0 and buffer[0] != 0x7E:
                    # Если мусор в начале — чистим
                    buffer.clear()

    threading.Thread(target=receive_logic, daemon=True).start()

    while True:
        try:
            cmd = input("> ").split(" ", 2)
            if not cmd or cmd[0] == "": continue
            if cmd[0] == "exit": break
            
            if cmd[0] == "send" and len(cmd) == 3:
                dest = BROADCAST if cmd[1].lower() == "broadcast" else int(cmd[1])
                text = cmd[2]
                
                # Создаем кадр
                new_frame = EncryptedFrame(
                    dest_addr=dest, 
                    src_addr=MY_ADDRESS, 
                    frame_type=FrameType.DATA, 
                    data=text.encode('utf-8')
                )
                tx.send_bytes(new_frame.encrypted_serialize())
                print(f"📤 Отправлено Узлу {dest}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Ошибка ввода: {e}")

    rx.close_port()
    tx.close_port()

if __name__ == "__main__":
    main()