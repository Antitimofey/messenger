import sys
from pathlib import Path

# Настройка путей (чтобы скрипт видел папку phisical и channel)
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

# Импортируем всё из requirements.py
# (Предполагается, что файл называется requirements.py и лежит в channel/stack/)
try:
    import channel.stack.requirements as req
    from channel.stack.requirements import COMPortSettings
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def print_menu():
    print("\n" + "="*30)
    print(" ТЕСТОВЫЙ УЗЕЛ (requirements.py)")
    print("="*30)
    print("1. Список портов (list_ports)")
    print("2. Настроить порты (save_settings)")
    print("3. Установить ID компьютера (open_physical_channel)")
    print("4. Открыть порты и запустить поток (connect_logical)")
    print("5. Отправить сообщение (send_message)")
    print("6. Проверить входящие (get_message)")
    print("7. Закрыть порты (disconnect_logical)")
    print("0. Выход")
    print("-" * 30)

def main():
    while True:
        print_menu()
        choice = input("Выберите действие: ")

        if choice == "1":
            res = req.list_ports()
            print(f"Результат: {res}")

        elif choice == "2":
            # Тестовая настройка
            p_in = input("Введите порт для RX (например, COM15): ")
            p_out = input("Введите порт для TX (например, COM10): ")
            
            s_in = COMPortSettings(port_name=p_in, baudrate=19200)
            s_out = COMPortSettings(port_name=p_out, baudrate=19200)
            
            req.save_settings("input", s_in)
            req.save_settings("output", s_out)
            print("✅ Настройки сохранены в объекты rx/tx")

        elif choice == "3":
            my_id = input("Введите ID этого компьютера (1, 2 или 3): ")
            if my_id.isdigit():
                res = req.open_physical_channel(int(my_id))
                print(f"Результат: {res}")
            else:
                print("❌ ID должен быть числом")

        elif choice == "4":
            # В requirements.py connect_logical только делает open_port()
            # Чтобы заработал прием, нужно вызвать tracker.start_listening()
            req.connect_logical()
            req.tracker.start_listening() # Запускаем фоновый поток трекера
            print("✅ Порты открыты, поток прослушивания запущен")

        elif choice == "5":
            dest = input("Кому (1, 2, 3 или broadcast): ")
            msg = input("Текст сообщения: ")
            res = req.send_message(msg, dest)
            print(f"Результат: {res}")

        elif choice == "6":
            # Проверяем очередь сообщений
            res = req.get_message()
            if res["ok"]:
                print(f"📩 НОВОЕ СООБЩЕНИЕ: {res['message']}")
            else:
                print(f"📭 {res['error']}")

        elif choice == "7":
            req.tracker.stop_listening() # Останавливаем поток
            res = req.disconnect_logical()
            print(f"✅ Каналы закрыты: {res}")

        elif choice == "0":
            req.tracker.stop_listening()
            req.disconnect_logical()
            print("Выход...")
            break
        else:
            print("❌ Неверный ввод")

if __name__ == "__main__":
    main()