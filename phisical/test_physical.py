"""
Короткий тест физического уровня
Проверяет работу одной пары портов COM10 ↔ COM11
"""

import time
from physical import COMPort, get_available_ports

def main():
    print("=" * 50)
    print("Тест физического уровня")
    print("=" * 50)
    
    # Показываем доступные порты
    ports = get_available_ports()
    print(f"\nДоступные порты: {ports}")
    
    # Берём пару COM10 и COM11
    tx_port_name = 'COM10'
    rx_port_name = 'COM11'
    
    print(f"\nИспользуем пару: {tx_port_name} → {rx_port_name}")
    
    # Создаём порты
    tx = COMPort('output')
    rx = COMPort('input')
    
    # Настраиваем параметры
    tx.set_parameters(baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=2)
    rx.set_parameters(baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=2)
    
    # Открываем порты
    print("\n1. Открытие портов...")
    if not tx.open_port(tx_port_name):
        print("   ❌ Ошибка открытия tx порта")
        return
    if not rx.open_port(rx_port_name):
        print("   ❌ Ошибка открытия rx порта")
        return
    print("   ✅ Порты открыты")
    
    # Отправка и приём
    test_data = b'HELLO'
    print(f"\n2. Отправка: {test_data}")
    tx.send_bytes(test_data)
    
    time.sleep(0.1)
    
    received = rx.receive_bytes(len(test_data))
    print(f"   Получено: {received}")
    
    if received == test_data:
        print("   ✅ УСПЕХ! Данные переданы корректно")
    else:
        print("   ❌ ОШИБКА! Данные не совпадают")
    
    # Показываем параметры
    print("\n3. Текущие параметры:")
    params = tx.get_current_parameters()
    print(f"   Скорость: {params['baudrate']}")
    print(f"   Бит данных: {params['bytesize']}")
    print(f"   Чётность: {params['parity']}")
    print(f"   Стоп-биты: {params['stopbits']}")
    
    # Закрываем порты
    print("\n4. Закрытие портов...")
    tx.close_port()
    rx.close_port()
    print("   ✅ Порты закрыты")
    
    print("\n" + "=" * 50)
    print("Тест завершён")

if __name__ == "__main__":
    main()