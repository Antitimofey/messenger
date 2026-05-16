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

MY_ADDRESS = 3
BROADCAST = 0x00

def main():
    print(f"=== Узел {MY_ADDRESS} запущен ===")
    
    rx_set = COMPortSettings(port_name='COM13', baudrate=19200)
    tx_set = COMPortSettings(port_name='COM14', baudrate=19200)

    rx = COMPort('input')
    tx = COMPort('output')

    if not rx.open_port(rx_set) or not tx.open_port(tx_set):
        print("❌ Ошибка портов.")
        return

    def receive_logic():
        buffer = bytearray()
        while rx.is_open():
            byte = rx.receive_bytes(1)
            if byte:
                buffer.extend(byte)
                if len(buffer) >= 2 and buffer[0] == 0x7E and buffer[-1] == 0x7E:
                    try:
                        frame = EncryptedFrame(raw_bytes=bytes(buffer))
                        if frame.src_addr != MY_ADDRESS:
                            if frame.dest_addr in [MY_ADDRESS, BROADCAST]:
                                print(f"\n📥 ПОЛУЧЕНО от Узла {frame.src_addr}: {frame.get_data_as_text()}")
                            if frame.dest_addr != MY_ADDRESS:
                                tx.send_bytes(bytes(buffer))
                    except Exception as e: print(f"\n⚠️ Ошибка: {e}")
                    finally:
                        buffer.clear()
                        print("> ", end="", flush=True)

    threading.Thread(target=receive_logic, daemon=True).start()

    while True:
        try:
            cmd = input("> ").split(" ", 2)
            if not cmd or cmd[0] == "": continue
            if cmd[0] == "exit": break
            if cmd[0] == "send" and len(cmd) == 3:
                dest = BROADCAST if cmd[1].lower() == "broadcast" else int(cmd[1])
                msg = EncryptedFrame(dest, MY_ADDRESS, FrameType.DATA, cmd[2].encode('utf-8'))
                tx.send_bytes(msg.encrypted_serialize())
                print(f"📤 Отправлено")
        except Exception as e: print(e)

    rx.close_port(); tx.close_port()

if __name__ == "__main__":
    main()