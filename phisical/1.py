import sys
from pathlib import Path
import time

# Настройка путей
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from phisical.physical import COMPort
from channel.stack.requirements import COMPortSettings
from channel.stack.serialTracker import SerialTracker

MY_ADDR = 1
BROADCAST = 0

def main():
    # Настройки портов
    rx_set = COMPortSettings(port_name='COM15', baudrate=19200)
    tx_set = COMPortSettings(port_name='COM10', baudrate=19200)
    
    rx = COMPort('input', rx_set)
    tx = COMPort('output', tx_set)
    
    # Инициализируем трекер
    tracker = SerialTracker(rx, tx, my_addr=MY_ADDR, broadcast_addr=BROADCAST)
    
    try:
        # Запускаем фоновое прослушивание (внутри создается поток)
        tracker.start_listening()
        print(f"=== Узел {MY_ADDR} запущен (Tracker Mode) ===")
        print("Команды: send <addr> <msg>, exit")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return

    while True:
        try:
            # Периодически можно проверять очередь, если нужно программно обработать данные
            # В данном тесте tracker сам печатает в консоль из фонового потока
            msg_data = tracker.get_message()
            if msg_data:
                # Здесь можно добавить доп. логику обработки принятого сообщения
                pass

            cmd_input = input("> ").split(" ", 2)
            if not cmd_input or cmd_input[0] == "": continue
            
            cmd = cmd_input[0].lower()
            
            if cmd == "exit":
                break
                
            if cmd == "send" and len(cmd_input) == 3:
                dest = BROADCAST if cmd_input[1].lower() == "broadcast" else int(cmd_input[1])
                text = cmd_input[2]
                tracker.send_message(dest, text)
                print(f"📤 Команда на отправку ушла...")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")

    tracker.stop_listening()
    rx.close_port()
    tx.close_port()

if __name__ == "__main__":
    main()