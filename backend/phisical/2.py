import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from phisical.physical import COMPort
from channel.stack.requirements import COMPortSettings
from channel.stack.serialTracker import SerialTracker

MY_ADDR = 2
BROADCAST = 0

def main():
    rx_set = COMPortSettings(port_name='COM11', baudrate=19200)
    tx_set = COMPortSettings(port_name='COM12', baudrate=19200)
    
    rx = COMPort('input', rx_set)
    tx = COMPort('output', tx_set)
    
    tracker = SerialTracker(rx, tx, my_addr=MY_ADDR, broadcast_addr=BROADCAST)
    
    try:
        tracker.start_listening()
        print(f"=== Узел {MY_ADDR} запущен (Tracker Mode) ===")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return

    while True:
        try:
            cmd_input = input("> ").split(" ", 2)
            if not cmd_input or cmd_input[0] == "": continue
            
            if cmd_input[0] == "exit": break
                
            if cmd_input[0] == "send" and len(cmd_input) == 3:
                dest = BROADCAST if cmd_input[1].lower() == "broadcast" else int(cmd_input[1])
                tracker.send_message(dest, cmd_input[2])
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")

    tracker.stop_listening()
    rx.close_port()
    tx.close_port()

if __name__ == "__main__":
    main()