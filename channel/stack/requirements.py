from dataclasses import dataclass
from typing import Any, TypedDict, Optional

@dataclass
class COMPortSettings:
    """Класс для хранения параметров соединения COM-порта"""
    port_name: str = ""
    baudrate: int = 19200
    bytesize: int = 8
    parity: str = 'N'      # 'N' (None), 'E' (Even), 'O' (Odd)
    stopbits: float = 1    # 1, 1.5, 2
    timeout: float = 1.0

class SerialSettings(TypedDict, total=False):
  # Структура для канального уровня
  portCom1: str
  portCom2: str
  nodeAddress: int
  baudRate: int

# --- ИСПРАВЛЕННЫЕ ФУНКЦИИ ИНТЕРФЕЙСА ---

def list_ports() -> dict[str, Any]:
  """
  Вернуть список доступных COM-портов.
  """
  return {"ok": False, "error": "not implemented", "ports": []}

def save_settings(settings: SerialSettings) -> dict[str, Any]:
  """
  Обновить параметры соединения.
  """
  return {"ok": False, "error": "not implemented"}

def open_physical_channel() -> dict[str, Any]:
  """
  Открыть ОБА порта с сохранёнными параметрами.
  """
  return {"ok": False, "error": "not implemented"}

def close_physical_channel() -> dict[str, Any]:
  """
  Закрыть COM1 и COM2.
  """
  return {"ok": False, "error": "not implemented"}

def connect_logical() -> dict[str, Any]:
  """
  Установить логическое соединение.
  """
  return {"ok": False, "error": "not implemented"}

def disconnect_logical() -> dict[str, Any]:
  """
  Разорвать логическое соединение.
  """
  return {"ok": False, "error": "not implemented"}

def send_message(text: str, destination: Any) -> dict[str, Any]:
  """
  Отправить сообщение.
  """
  return {"ok": False, "error": "not implemented"}

def get_message() -> dict[str, Any]:
  """
  Получить сообщение из очереди.
  """
  return {"ok": False, "error": "not implemented"}