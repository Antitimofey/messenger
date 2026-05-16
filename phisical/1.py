import sys
import threading
from pathlib import Path

# Добавляем корень проекта в пути
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from phisical.physical import COMPort
from channel.stack.requirements import COMPortSettings
from channel.frame.encryptedFrame import EncryptedFrame
from channel.frame.frame import FrameType

MY_ADDR = 1
BROADCAST = 0

def receive_thread(rx_port, tx_port):
    buffer = bytearray()
    while True:
        byte = rx_port.receive_bytes(1)
        if byte:
            buffer.extend(byte)
            if len(buffer) >= 2 and buffer[0] == 0x7E and buffer[-1] == 0x7E:
                try:
                    frame = EncryptedFrame(raw_bytes=bytes(buffer))
                    if frame.src_addr == MY_ADDR:
                        print("\n🔄 Мое сообщение вернулось (круг пройден).")
                    else:
                        if frame.dest_addr == MY_ADDR or frame.dest_addr == BROADCAST:
                            print(f"\n📥 Сообщение от {frame.src_addr}: {frame.get_data_as_text()}")
                        if frame.dest_addr != MY_ADDR:
                            print(f"⏩ Ретрансляция сообщения от {frame.src_addr}...")
                            tx_port.send_bytes(bytes(buffer))
                except Exception as e:
                    print(f"\n⚠️ Ошибка кадра: {e}")
                finally:
                    buffer.clear()
                    print("> ", end="", flush=True)

def main():
    rx_set = COMPortSettings(port_name='COM15', baudrate=19200)
    tx_set = COMPortSettings(port_name='COM10', baudrate=19200)
    
    rx = COMPort('input', rx_set)
    tx = COMPort('output', tx_set)
    
    if not rx.open_port() or not tx.open_port():
        print("❌ Не удалось открыть порты!")
        return

    print(f"=== Узел {MY_ADDR} запущен. Команды: send <addr> <msg>, exit ===")
    threading.Thread(target=receive_thread, args=(rx, tx), daemon=True).start()

    while True:
        try:
            inp = input("> ").split(" ", 2)
            if inp[0] == "exit": break
            if inp[0] == "send" and len(inp) == 3:
                dest = BROADCAST if inp[1].lower() == "broadcast" else int(inp[1])
                msg = EncryptedFrame(dest, MY_ADDR, FrameType.DATA, inp[2].encode('utf-8'))
                tx.send_bytes(msg.encrypted_serialize())
        except KeyboardInterrupt: break
        except Exception as e: print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()