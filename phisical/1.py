import threading
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from channel.frame.encryptedFrame import EncryptedFrame

from physical import COMPort

MY_ADDRESS = 1
RX_PORT = 'COM15'  # Получает от Узла 3
TX_PORT = 'COM10'  # Отправляет Узлу 2
BROADCAST = 255

print(f"=== Узел {MY_ADDRESS} запущен ===")

rx = COMPort('input')
tx = COMPort('output')

if not rx.open_port(RX_PORT, baudrate=19200) or not tx.open_port(TX_PORT, baudrate=19200):
    print("❌ Ошибка открытия портов")
    exit(1)

def send_frame(dest, data):
    payload = data.encode('utf-8')
    frame = bytes([MY_ADDRESS, dest, len(payload)]) + payload
    tx.send_bytes(frame)
    print(f"📤 Отправлено узлу {dest}: {data}")

def receive_logic():
    while True:
        header = rx.receive_bytes(3)
        if header and len(header) == 3:
            src, dest, length = header[0], header[1], header[2]
            payload = rx.receive_bytes(length)
            
            if src == MY_ADDRESS:
                print("🔄 Сообщение вернулось (удалено из кольца)")
                continue

            if dest == MY_ADDRESS or dest == BROADCAST:
                print(f"📥 ПОЛУЧЕНО от {src}: {payload.decode('utf-8')}")
            
            if dest != MY_ADDRESS:
                print(f"⏩ РЕТРАНСЛЯЦИЯ дальше")
                tx.send_bytes(header + payload)

threading.Thread(target=receive_logic, daemon=True).start()

while True:
    cmd = input("> ").split(" ", 2)
    if cmd[0] == "exit": break
    if cmd[0] == "send" and len(cmd) == 3:
        addr = BROADCAST if cmd[1] == "broadcast" else int(cmd[1])
        send_frame(addr, cmd[2])

rx.close_port(); tx.close_port()