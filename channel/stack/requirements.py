from dataclasses import dataclass
from typing import Any, TypedDict, Optional

import threading
import typing
import sys
from pathlib import Path
from queue import Queue
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from phisical.physical import get_available_ports
from channel.stack.serialTracker import SerialTracker
from phisical.physical import COMPort


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


rx_set = COMPortSettings(port_name='COM15', baudrate=19200)
rx = COMPort(role="input", settings=rx_set)

tx_set = COMPortSettings(port_name='COM10', baudrate=19200)
tx = COMPort(role="output", settings=tx_set)

tracker = SerialTracker(rx, tx)

def list_ports() -> dict[str, Any]:
  """
  Аргументы:
    нет.

  Что делать:
    Вернуть список доступных COM-портов.

  Возврат при успехе:
    {"ok": True, "ports": ["COM1", "COM3", "COM5"]}

  Возврат при ошибке:
    {"ok": False, "error": "Не удалось получить список портов", "ports": []}
  """
  return {"ok": True, "error": "qorks fine", "ports": get_available_ports()}


def save_settings(port_direction: str, settings: COMPortSettings) -> dict[str, Any]:
  """
  Аргументы:
    settings — dict SerialSettings (portCom1, portCom2, nodeAddress, baudRate, …).

  Что делать:
    Обновить параметры соединения

  Возврат при успехе:
    {"ok": True}

  Примеры возвратов при ошибках:
    {"ok": False, "error": "Некорректная скорость: …"}
    ... другие ошибки ...
    {"ok": False, "error": "Не удалось сохранить настройки"}
  """
  if port_direction not in ["input", "output"]:
    messsage = f"port direction must be 'input' or 'output', got {port_direction}"
    return {"ok": False, "error": messsage}
  
  if port_direction == "input":
    rx.set_parameters(settings)
  if port_direction == "output":
    tx.set_parameters(settings)
  return {"ok": True, "error": "seems fine"}

def open_physical_channel(computer_number: int) -> dict[str, Any]:
  """
  Аргументы:
    порт1, порт2

  Что делать:
    • Держать канал до close_physical_channel.
    • Если уже открыто — идемпотентно вернуть успех с текущими ports.

  Возврат при успехе:
    {"ok": True, "ports": ["COM1", "COM2"]}

  Возврат при ошибке:
    {"ok": False, "error": "COM1 занят другим приложением"}
    {"ok": False, "error": "Сначала сохраните параметры соединения"}
  """
  
  tracker.my_addr = computer_number
  
  return {"ok": True, "error": "works fine"}


def close_physical_channel() -> dict[str, Any]:
  """
  Аргументы:
    нет.

  Что делать:
    • При активном логическом соединении — разорвать его, иначе ничего не делать.
    • Закрыть COM1 и COM2.

  Возврат при успехе:
    {"ok": True}

  Возврат при ошибке:
    {"ok": False, "error": "…"}
  """
  return {"ok": True, "error": "nothing to do"}


def connect_logical() -> dict[str, Any]:
  """
  Аргументы:
    нет

  Что делать:
    установить логическое соединение

  Возврат при успехе:
    {"ok": True}

  Возврат при ошибке:
    {"ok": False, "error": "Физический канал не открыт"}
    {"ok": False, "error": "Узел 2 не отвечает (таймаут)"}
  """
  rx.open_port()
  tx.open_port()
  return {"ok": False, "error": "not implemented"}


def disconnect_logical() -> dict[str, Any]:
  """
  Аргументы:
    нет.

  Что делать:
    U-кадр, logical_connected = False; физ. канал может остаться открытым.

  Возврат при успехе:
    {"ok": True}

  Возврат при ошибке:
    {"ok": False, "error": "Логическое соединение не установлено"}
  """
  rx.close_port()
  tx.close_port()
  return {"ok": False, "error": "not implemented"}


def send_message(text: str, destination: str) -> dict[str, Any]:
  """
  Аргументы:
    text        — короткое сообщение с клавиатуры.
    destination — 1 | 2 | 3 | "broadcast".

  Возврат при успехе:
    {"ok": True}

  Возврат при ошибке:
    {"ok": False, "error": "Нет логического соединения"}
    ... другие ошибки ...
    {"ok": False, "error": "Пустое сообщение"}
  """
  dest = 0 if destination == "broadcast" else int(destination)
  tracker.send_message(dest, text)
  return {"ok": True, "error": "all fine"}

def get_message() -> dict[str, Any]:
  """
  Аргументы:
    нет

  Что делать:
    • если вызвалась функция, то либо возвращать последнее сообщение из очереди, либо ошибку и удалять последнее
    сообщение из очереди

  Возврат при успехе:
    {"ok": True, "message": "..."}

  Возврат при ошибке:
    {"ok": False, "error": "..."}
  """
  msg_data = tracker.get_message()
  if msg_data is not None:
    return {"ok": True, "error": "all fine", "message": msg_data}
  return {"ok": False, "error": "no more messages", "message": ""}
  
