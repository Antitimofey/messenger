import sys
from pathlib import Path
from typing import Any

# Настройка путей
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from phisical.physical import COMPort, COMPortSettings, get_available_ports
from channel.stack.serialTracker import SerialTracker


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
  tracker.is_hpysical_open = True
  
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
  if tracker.is_logical_open:
    return {"ok": False, "error": "для этого действия необходимо сначала \033[31mзакрыть\033[0m логический канал"}
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
  if not tracker.is_hpysical_open:
    return {"ok": False, "error": "для этого действия необходимо сначала открыть физический канал"}

  if not rx.open_port():
    return {"ok": False, "error": f"Не удалось открыть порт приёма {rx.settings.port_name}"}
  if not tx.open_port():
    rx.close_port()
    return {"ok": False, "error": f"Не удалось открыть порт передачи {tx.settings.port_name}"}

  try:
    tracker.start_listening()
  except Exception as e:
    tracker.stop_listening()
    rx.close_port()
    tx.close_port()
    return {"ok": False, "error": str(e)}

  tracker.is_logical_open = True
  return {"ok": True, "error": "all fine"}


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
  if not tracker.is_logical_open:
    return {"ok": False, "error": "Логическое соединение не установлено"}

  tracker.stop_listening()
  rx.close_port()
  tx.close_port()
  tracker.is_logical_open = False
  return {"ok": True, "error": "seems fine"}


def _parse_destination(destination: Any) -> int:
  """1|2|3 -> addr, broadcast/0 -> 0. Безопасно для str/int и ошибочного '[object Object]'."""
  if isinstance(destination, dict):
    destination = destination.get("destination", destination.get("value", ""))
  if isinstance(destination, (int, float)):
    return 0 if int(destination) == 0 else int(destination)
  s = str(destination).strip().lower()
  if s in ("broadcast", "0", "всем (широковещание)"):
    return 0
  if "object object" in s:
    raise ValueError("Некорректный получатель (передан объект). Выберите узел 1, 2, 3 или «Всем».")
  return int(s)


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
  if isinstance(text, dict):
    destination = text.get("destination", destination)
    text = text.get("text", "")

  try:
    dest = _parse_destination(destination)
  except (TypeError, ValueError) as e:
    return {"ok": False, "error": f"Некорректный получатель: {e}"}

  try:
    sent = tracker.send_message(dest, str(text))
  except Exception as e:
    return {"ok": False, "error": f"during message sending exception oqured: {str(e)}"}
  if sent == -1:
    return {"ok": False, "error": "Не удалось отправить в COM-порт (порт закрыт или ошибка записи)"}
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
  if not tracker.is_logical_open:
    return {"ok": False, "error": "Нет логического соединения", "message": ""}

  try:
    if tracker.queue.empty():
      return {"ok": False, "error": "no more messages", "message": ""}
    msg_data = tracker.queue.get_nowait()
    return {"ok": True, "message": str(msg_data)}
  except Exception as e:
    return {"ok": False, "error": f"during message getting exception oqured: {str(e)}", "message": ""}
  
