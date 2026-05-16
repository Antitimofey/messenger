"""
Модуль физического уровня для кольцевой сети


Предоставляет класс COMPort для работы с COM-портами в кольцевой топологии.
Соответствует интерфейсу, согласованному с канальным уровнем.
"""

import serial
import serial.tools.list_ports
import threading
import time
from typing import Optional, Callable, List, Tuple


class COMPort:
    """
    Класс для работы с COM-портом на физическом уровне.
    
    Предоставляет интерфейс для:
    - открытия/закрытия порта,
    - установки параметров RS-232C,
    - байтовой передачи/приёма,
    - управления потоком данных в кольцевой топологии.
    
    Разработчик канального уровня создаёт два экземпляра:
    - left_port = COMPort('input')   # порт, принимающий данные от предыдущего узла
    - right_port = COMPort('output') # порт, отправляющий данные следующему узлу
    """
    
    def __init__(self, role: str):
        """
        Инициализация объекта COM-порта.
        
        Параметры:
        ----------
        role : str
            Роль порта в кольцевой топологии:
            - 'input'  - порт для приёма данных от предыдущего узла
            - 'output' - порт для отправки данных следующему узлу
        """
        if role not in ['input', 'output']:
            raise ValueError(f"Некорректная роль: {role}. Допустимо: 'input' или 'output'")
        
        self.role = role
        self.port_name: Optional[str] = None
        self.serial: Optional[serial.Serial] = None
        
        # Параметры порта по умолчанию
        self.baudrate = 19200
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        self.timeout = 1.0
        
        # Для асинхронного чтения
        self._receive_callback: Optional[Callable[[bytes], None]] = None
        self._reading_thread: Optional[threading.Thread] = None
        self._stop_reading = False
        
        # Для отладки
        self.debug_mode = False
    
    def open_port(self, port_name: str, baudrate: int = 9600, bytesize: int = 8,
                  parity: str = 'N', stopbits: int = 1, timeout: float = 1.0) -> bool:
        """
        Открытие COM-порта с заданными параметрами.
        
        Параметры:
        ----------
        port_name : str
            Имя COM-порта (например, 'COM1', 'COM2', '/dev/ttyS0')
        baudrate : int, default=9600
            Скорость передачи (бит/с)
        bytesize : int, default=8
            Количество бит данных (5, 6, 7 или 8)
        parity : str, default='N'
            Чётность: 'N' (нет), 'E' (чёт), 'O' (нечёт)
        stopbits : int, default=1
            Количество стоп-бит (1 или 2)
        timeout : float, default=1.0
            Таймаут чтения в секундах
        """
        # Сохраняем параметры
        if not self.set_parameters(baudrate, bytesize, parity, stopbits, timeout):
            return False
        
        self.port_name = port_name
        
        try:
            # Закрываем старый порт, если открыт
            if self.serial is not None and self.serial.is_open:
                self.close_port()
            
            # Открываем порт
            self.serial = serial.Serial(
                port=port_name,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout
            )
            
            if self.debug_mode:
                print(f"[{self.role}:{self.port_name}] Порт открыт (скорость {self.baudrate})")
            
            return True
            
        except serial.SerialException as e:
            print(f"[{self.role}:{port_name}] Ошибка открытия порта: {e}")
            return False
        except Exception as e:
            print(f"[{self.role}:{port_name}] Неизвестная ошибка: {e}")
            return False
    
    def close_port(self) -> bool:
        """
        Закрытие COM-порта и освобождение ресурсов.
        """
        # Останавливаем фоновое чтение
        self.remove_receive_callback()
        
        if self.serial is not None and self.serial.is_open:
            try:
                self.serial.close()
                if self.debug_mode:
                    print(f"[{self.role}:{self.port_name}] Порт закрыт")
                self.serial = None
                return True
            except Exception as e:
                print(f" [{self.role}] Ошибка закрытия порта: {e}")
                return False
        
        return True
    
    def set_parameters(self, baudrate: int = None, bytesize: int = None,
                       parity: str = None, stopbits: int = None,
                       timeout: float = None) -> bool:
        """
        Изменение параметров COM-порта без переоткрытия.
        """
        try:
            if baudrate is not None:
                standard_baudrates = [110, 300, 600, 1200, 2400, 4800, 9600, 19200, 
                                       38400, 57600, 115200, 230400, 460800, 921600]
                if baudrate not in standard_baudrates:
                    print(f"Ошибка: скорость {baudrate} не поддерживается")
                    return False
                self.baudrate = baudrate
            
            if bytesize is not None:
                if bytesize not in [5, 6, 7, 8]:
                    raise ValueError(f"Некорректный bytesize: {bytesize}")
                self.bytesize = bytesize
            
            if parity is not None:
                if parity not in ['N', 'E', 'O']:
                    raise ValueError(f"Некорректная parity: {parity}")
                self.parity = parity
            
            if stopbits is not None:
                if stopbits not in [1, 1.5, 2]:
                    raise ValueError(f"Некорректный stopbits: {stopbits}")
                self.stopbits = stopbits
            
            if timeout is not None:
                self.timeout = timeout
            
            # Если порт открыт, применяем параметры
            if self.is_open():
                self.serial.baudrate = self.baudrate
                self.serial.bytesize = self.bytesize
                self.serial.parity = self.parity
                self.serial.stopbits = self.stopbits
                self.serial.timeout = self.timeout
            
            if self.debug_mode:
                print(f"[{self.role}] Параметры установлены: {self.baudrate}/{self.bytesize}/{self.parity}/{self.stopbits}, timeout={self.timeout}")
            
            return True
            
        except Exception as e:
            print(f"[{self.role}] Ошибка установки параметров: {e}")
            return False
    
    def send_bytes(self, data: bytes) -> int:
        """
        Отправка байтов через COM-порт.
        """
        if not self.is_open():
            print(f"[{self.role}] Ошибка отправки: порт не открыт")
            return -1
        
        if not isinstance(data, bytes) or len(data) == 0:
            print(f"[{self.role}] Ошибка: данные должны быть непустым bytes")
            return -1
        
        try:
            sent_bytes = self.serial.write(data)
            if self.debug_mode:
                print(f"[{self.role}] Отправлено {sent_bytes} байт: {data.hex() if len(data) <= 16 else data.hex()[:32] + '...'}")
            return sent_bytes
            
        except serial.SerialException as e:
            print(f"[{self.role}] Ошибка отправки: {e}")
            return -1
        except Exception as e:
            print(f"[{self.role}] Неизвестная ошибка отправки: {e}")
            return -1
    
    def receive_bytes(self, num_bytes: int) -> Optional[bytes]:
        """
        Приём байтов из COM-порта (блокирующий вызов до таймаута).
        """
        if not self.is_open():
            if self.debug_mode:
                print(f"[{self.role}] Попытка приёма при закрытом порте")
            return None
        
        if num_bytes <= 0 or num_bytes > 65536:
            raise ValueError(f"Некорректный num_bytes: {num_bytes}")
        
        try:
            data = self.serial.read(num_bytes)
            if data and self.debug_mode:
                print(f"[{self.role}] Принято {len(data)} байт: {data.hex() if len(data) <= 16 else data.hex()[:32] + '...'}")
            return data if data else None
            
        except serial.SerialException as e:
            print(f"[{self.role}] Ошибка приёма: {e}")
            return None
        except Exception as e:
            print(f"[{self.role}] Неизвестная ошибка приёма: {e}")
            return None
    
    def set_receive_callback(self, callback: Callable[[bytes], None]) -> None:
        """
        Установка асинхронного callback-а на получение данных.
        """
        if not callable(callback):
            raise ValueError("callback должен быть вызываемым объектом")
        
        self._receive_callback = callback
        
        # Запускаем поток чтения, если порт открыт
        if self.is_open() and not self._reading_thread:
            self._stop_reading = False
            self._reading_thread = threading.Thread(target=self._reader_loop, daemon=True)
            self._reading_thread.start()
            if self.debug_mode:
                print(f"[{self.role}] Поток чтения запущен")
    
    def remove_receive_callback(self) -> None:
        """
        Удаление установленного callback-а и остановка фонового чтения.
        """
        self._stop_reading = True
        if self._reading_thread and self._reading_thread.is_alive():
            self._reading_thread.join(timeout=2.0)
        self._reading_thread = None
        self._receive_callback = None
        if self.debug_mode:
            print(f"[{self.role}] Поток чтения остановлен")
    
    def is_open(self) -> bool:
        """
        Проверка состояния порта (открыт/закрыт).
        """
        return self.serial is not None and self.serial.is_open
    
    def clear_buffers(self) -> bool:
        """
        Очистка входного и выходного буферов COM-порта.
        """
        if not self.is_open():
            return False
        
        try:
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            if self.debug_mode:
                print(f"[{self.role}] Буферы очищены")
            return True
        except Exception as e:
            print(f"[{self.role}] Ошибка очистки буферов: {e}")
            return False
    
    def get_role(self) -> str:
        """Получение роли порта ('input' или 'output')."""
        return self.role
    
    def get_port_name(self) -> Optional[str]:
        """Получение имени открытого COM-порта."""
        return self.port_name if self.is_open() else None
    
    def get_current_parameters(self) -> dict:
        """
        Получение текущих параметров COM-порта.
        """
        params = {
            'baudrate': self.baudrate,
            'bytesize': self.bytesize,
            'parity': self.parity,
            'stopbits': self.stopbits,
            'timeout': self.timeout,
            'port': self.port_name,
            'is_open': self.is_open()
        }
        
        if self.is_open():
            params['in_waiting'] = self.serial.in_waiting
            params['out_waiting'] = self.serial.out_waiting
        
        return params
    
    def wait_for_data(self, timeout: float = None) -> bool:
        """
        Ожидание поступления данных во входной буфер.
        """
        if not self.is_open():
            return False
        
        wait_timeout = timeout if timeout is not None else self.timeout
        start_time = time.time()
        
        while self.is_open():
            if self.serial.in_waiting > 0:
                return True
            if wait_timeout is not None and (time.time() - start_time) > wait_timeout:
                return False
            time.sleep(0.01)
        
        return False
    
    def get_bytes_available(self) -> int:
        """
        Получение количества байт, доступных для чтения во входном буфере.
        """
        if not self.is_open():
            return -1
        
        try:
            return self.serial.in_waiting
        except:
            return -1
    
    def set_debug(self, enabled: bool = True):
        """Включение/выключение режима отладки."""
        self.debug_mode = enabled
        print(f"[{self.role}] Режим отладки: {'включён' if enabled else 'выключен'}")
    
    def _reader_loop(self):
        """Фоновый поток для асинхронного чтения данных."""
        while not self._stop_reading and self.is_open():
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.read(self.serial.in_waiting)
                    if data and self._receive_callback:
                        self._receive_callback(data)
                else:
                    time.sleep(0.01)
            except Exception as e:
                if self.debug_mode:
                    print(f"[{self.role}] Ошибка в потоке чтения: {e}")
                break


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_available_ports() -> List[str]:
    """Возвращает список доступных COM-портов в системе."""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def list_ports_with_details() -> List[Tuple[str, str, str]]:
    """Возвращает список доступных COM-портов с деталями."""
    ports = serial.tools.list_ports.comports()
    return [(port.device, port.description, port.hwid) for port in ports]


def test_port(port_name: str, baudrate: int = 19200) -> bool:
    """Тестовая функция для проверки работы порта."""
    port = COMPort('input')
    port.set_debug(True)
    
    if port.open_port(port_name, baudrate=baudrate, timeout=1):
        result = port.send_bytes(b'T')
        port.close_port()
        return result > 0
    
    return False