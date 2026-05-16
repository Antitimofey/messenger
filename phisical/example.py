# ==============================================
# ФИЗИЧЕСКИЙ УРОВЕНЬ (разработчик Гапонов Р.Д.)
# ==============================================
import serial
import threading
import time
from typing import Optional, Callable

class COMPort:
    """
    Физический уровень.
    САМ управляет потоком чтения, канальный уровень об этом не знает.
    """
    
    def __init__(self, role: str):
        self.role = role
        self.serial_port = None
        self.is_open_flag = False
        
        # Внутренние поля для потока (скрыты от канального уровня)
        self._read_thread = None
        self._thread_running = False
        self._receive_callback = None
        
    def set_receive_callback(self, callback: Callable[[bytes], None]) -> None:
        """
        Канальный уровень регистрирует callback.
        Физический уровень сам решит, в каком потоке его вызывать.
        """
        self._receive_callback = callback
        
        # Если порт уже открыт и это input порт - запускаем поток
        if self.is_open_flag and self.role == 'input':
            self._start_read_thread()
    
    def open_port(self, port_name: str, baudrate: int = 9600) -> bool:
        """Открытие порта"""
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                timeout=0.1  # Маленький таймаут для возможности остановки
            )
            self.is_open_flag = True
            self.port_name = port_name
            
            # Если callback уже зарегистрирован - запускаем поток
            if self.role == 'input' and self._receive_callback:
                self._start_read_thread()
                
            return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False
    
    def _start_read_thread(self):
        """Физический уровень сам запускает поток"""
        if self._read_thread and self._read_thread.is_alive():
            return
            
        self._thread_running = True
        self._read_thread = threading.Thread(
            target=self._read_loop,
            daemon=True,
            name=f"PhysicalLayer_{self.port_name}"
        )
        self._read_thread.start()
        print(f"[PHYS] Поток чтения запущен для {self.port_name}")
    
    def _read_loop(self):
        """Поток чтения (внутренняя реализация физического уровня)"""
        while self._thread_running and self.is_open_flag:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if data and self._receive_callback:
                        # Вызов callback из потока физического уровня
                        self._receive_callback(data)
                time.sleep(0.01)
            except Exception as e:
                print(f"[PHYS] Ошибка в потоке чтения: {e}")
                break
    
    def send_bytes(self, data: bytes) -> int:
        """Отправка байт (без потоков)"""
        if not self.is_open_flag:
            raise Exception("Порт не открыт")
        return self.serial_port.write(data)
    
    def close_port(self) -> bool:
        """Закрытие порта и остановка потока"""
        self._thread_running = False
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=1.0)
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        
        self.is_open_flag = False
        return True
    
    def is_open(self) -> bool:
        return self.is_open_flag

