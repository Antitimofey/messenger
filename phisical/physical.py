"""
Модуль физического уровня для кольцевой сети


Предоставляет класс COMPort для работы с COM-портами в кольцевой топологии.
Соответствует интерфейсу, согласованному с канальным уровнем.
"""

import sys
import threading
import time
from pathlib import Path
from typing import Optional, Callable, List, Tuple

import serial
import serial.tools.list_ports

# --- ЛОГИКА ПУТЕЙ ДЛЯ WINDOWS ---
# Находим путь к папке, в которой лежат и 'physical', и 'channel'
# Path(__file__).resolve() — это полный путь к текущему файлу (physical.py)
# .parent — это папка 'physical'
# .parent.parent — это корень проекта
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Теперь импорт будет работать независимо от того, как запущен скрипт
try:
    from channel.stack.requirements import COMPortSettings
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print(f"Поиск велся в: {sys.path[0]}")
    raise

class COMPort:
    """
    Класс для работы с COM-портом на физическом уровне.
    Обеспечивает чтение, запись и управление параметрами.
    """
    
    def __init__(self, role: str):
        """
        :param role: 'input' (RX) или 'output' (TX)
        """
        if role not in ['input', 'output']:
            raise ValueError(f"Некорректная роль: {role}. Допустимо: 'input' или 'output'")
        
        self.role = role
        self.settings = COMPortSettings()
        self.serial: Optional[serial.Serial] = None
        
        # Для асинхронного чтения
        self._receive_callback: Optional[Callable[[bytes], None]] = None
        self._reading_thread: Optional[threading.Thread] = None
        self._stop_reading = False
        
        # Режим отладки
        self.debug_mode = False

    def open_port(self, settings: COMPortSettings) -> bool:
        """
        Открывает порт с заданными настройками.
        """
        self.settings = settings
        
        try:
            # Если порт уже открыт, сначала закрываем его
            if self.serial is not None and self.serial.is_open:
                self.close_port()
            
            # Создаем объект Serial с параметрами из нашего класса настроек
            self.serial = serial.Serial(
                port=self.settings.port_name,
                baudrate=self.settings.baudrate,
                bytesize=self.settings.bytesize,
                parity=self.settings.parity,
                stopbits=self.settings.stopbits,
                timeout=self.settings.timeout
            )
            
            if self.debug_mode:
                print(f"[{self.role}] Порт {self.settings.port_name} успешно открыт.")
            
            return True
            
        except Exception as e:
            print(f"[{self.role}] Ошибка при открытии {self.settings.port_name}: {e}")
            return False

    def close_port(self) -> bool:
        """Закрывает порт и останавливает потоки чтения."""
        self.remove_receive_callback()
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
                self.serial = None
                return True
            except Exception as e:
                print(f"[{self.role}] Ошибка при закрытии порта: {e}")
                return False
        return True

    def set_parameters(self, settings: COMPortSettings) -> bool:
        """Обновляет параметры порта 'на лету'."""
        try:
            self.settings = settings
            if self.is_open():
                self.serial.baudrate = self.settings.baudrate
                self.serial.bytesize = self.settings.bytesize
                self.serial.parity = self.settings.parity
                self.serial.stopbits = self.settings.stopbits
                self.serial.timeout = self.settings.timeout
            return True
        except Exception as e:
            print(f"[{self.role}] Ошибка смены параметров: {e}")
            return False

    def send_bytes(self, data: bytes) -> int:
        """Отправка сырых байтов в порт."""
        if not self.is_open():
            return -1
        try:
            sent = self.serial.write(data)
            self.serial.flush() # Ждем физического завершения отправки
            return sent
        except Exception as e:
            print(f"[{self.role}] Ошибка записи: {e}")
            return -1

    def receive_bytes(self, num_bytes: int) -> Optional[bytes]:
        """Блокирующее чтение заданного количества байт."""
        if not self.is_open():
            return None
        try:
            data = self.serial.read(num_bytes)
            return data if data else None
        except Exception as e:
            print(f"[{self.role}] Ошибка чтения: {e}")
            return None

    def is_open(self) -> bool:
        """Проверка, открыт ли порт."""
        return self.serial is not None and self.serial.is_open

    def clear_buffers(self):
        """Очистка системных буферов порта."""
        if self.is_open():
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()

    def set_receive_callback(self, callback: Callable[[bytes], None]):
        """Запуск фонового потока, который будет вызывать callback при поступлении данных."""
        if not callable(callback):
            raise ValueError("Callback должен быть функцией.")
        
        self._receive_callback = callback
        if self.is_open() and not self._reading_thread:
            self._stop_reading = False
            self._reading_thread = threading.Thread(target=self._reader_loop, daemon=True)
            self._reading_thread.start()

    def remove_receive_callback(self):
        """Остановка фонового чтения."""
        self._stop_reading = True
        if self._reading_thread and self._reading_thread.is_alive():
            self._reading_thread.join(timeout=1.0)
        self._reading_thread = None
        self._receive_callback = None

    def _reader_loop(self):
        """Внутренний цикл чтения для работы в потоке."""
        while not self._stop_reading and self.is_open():
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.read(self.serial.in_waiting)
                    if data and self._receive_callback:
                        self._receive_callback(data)
                else:
                    time.sleep(0.01) # Снижаем нагрузку на ЦП
            except Exception:
                break

    def set_debug(self, state: bool):
        self.debug_mode = state

# --- УТИЛИТЫ ---
def get_available_ports() -> List[str]:
    """Возвращает список имен доступных COM-портов."""
    return [port.device for port in serial.tools.list_ports.comports()]