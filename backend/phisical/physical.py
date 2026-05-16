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
from dataclasses import dataclass
import serial
import serial.tools.list_ports

# Настройка путей
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

@dataclass
class COMPortSettings:
    """Класс для хранения параметров соединения COM-порта"""
    port_name: str = ""
    baudrate: int = 19200
    bytesize: int = 8
    parity: str = 'N'      # 'N' (None), 'E' (Even), 'O' (Odd)
    stopbits: float = 1    # 1, 1.5, 2
    timeout: float = 1.0

class COMPort:
    """
    Класс физического уровня. 
    Настройки порта передаются один раз при инициализации.
    """
    def __init__(self, role: str, settings: COMPortSettings):
        if role not in ['input', 'output']:
            raise ValueError(f"Роль {role} не поддерживается. Используйте 'input' или 'output'.")
        
        self.role = role
        self.settings = settings
        self.serial: Optional[serial.Serial] = None
        self._receive_callback: Optional[Callable[[bytes], None]] = None
        self._reading_thread: Optional[threading.Thread] = None
        self._stop_reading = False
        self.debug_mode = False

    def open_port(self) -> bool:
        """Открывает порт, используя настройки из self.settings"""
        try:
            if self.serial and self.serial.is_open:
                self.close_port()

            self.serial = serial.Serial(
                port=self.settings.port_name,
                baudrate=self.settings.baudrate,
                bytesize=self.settings.bytesize,
                parity=self.settings.parity,
                stopbits=self.settings.stopbits,
                timeout=self.settings.timeout,
                write_timeout=self.settings.timeout,
            )
            if self.debug_mode:
                print(f"[{self.role}] Порт {self.settings.port_name} открыт.")
            return True
        except Exception as e:
            print(f"[{self.role}] Ошибка открытия {self.settings.port_name}: {e}")
            return False

    def set_parameters(self, settings: COMPortSettings) -> bool:
        """Обновляет параметры открытого порта."""
        try:
            self.settings = settings
            if self.is_open():
                self.serial.baudrate = self.settings.baudrate
                self.serial.bytesize = self.settings.bytesize
                self.serial.parity = self.settings.parity
                self.serial.stopbits = self.settings.stopbits
                self.serial.timeout = self.settings.timeout
                self.serial.write_timeout = self.settings.timeout
            return True
        except Exception as e:
            print(f"[{self.role}] Ошибка обновления параметров: {e}")
            return False

    def close_port(self) -> bool:
        self.remove_receive_callback()
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.serial = None
        return True

    def send_bytes(self, data: bytes) -> int:
        if not self.is_open(): return -1
        try:
            sent = self.serial.write(data)
            self.serial.flush()
            return sent
        except: return -1

    def receive_bytes(self, num_bytes: int) -> Optional[bytes]:
        if not self.is_open(): return None
        try:
            return self.serial.read(num_bytes)
        except: return None

    def is_open(self) -> bool:
        return self.serial is not None and self.serial.is_open

    def set_receive_callback(self, callback: Callable[[bytes], None]):
        self._receive_callback = callback
        if self.is_open() and not self._reading_thread:
            self._stop_reading = False
            self._reading_thread = threading.Thread(target=self._reader_loop, daemon=True)
            self._reading_thread.start()

    def remove_receive_callback(self):
        self._stop_reading = True
        if self._reading_thread and self._reading_thread.is_alive():
            self._reading_thread.join(timeout=1.0)
        self._reading_thread = None

    def _reader_loop(self):
        while not self._stop_reading and self.is_open():
            try:
                if self.serial.in_waiting > 0:
                    data = self.serial.read(self.serial.in_waiting)
                    if data and self._receive_callback:
                        self._receive_callback(data)
                else: time.sleep(0.01)
            except: break

    def set_debug(self, state: bool):
        self.debug_mode = state

def get_available_ports() -> List[str]:
    return [port.device for port in serial.tools.list_ports.comports()]

def list_ports_with_details() -> List[tuple[str, str, str]]:
    """
    Возвращает список доступных COM-портов с деталями.
    Формат: (имя_порта, описание, ID_оборудования)
    """
    ports = serial.tools.list_ports.comports()
    return [(port.device, port.description, port.hwid) for port in ports]