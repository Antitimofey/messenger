class SerialSettings(TypedDict, total=False):
  # посмотри, че в дисе у меня в выборе и придумай структуру, главное дай мне ее

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
  return {"ok": False, "error": "not implemented", "ports": []}


def save_settings(settings: SerialSettings) -> dict[str, Any]:
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
  return {"ok": False, "error": "not implemented"}


def open_physical_channel(PortInput, PortOutput) -> dict[str, Any]:
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
  return {"ok": False, "error": "not implemented"}

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
  return {"ok": False, "error": "not implemented", "ports": []}


def save_settings(settings: SerialSettings) -> dict[str, Any]:
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
  return {"ok": False, "error": "not implemented"}


def open_physical_channel() -> dict[str, Any]:
  """
  Аргументы:
    нет

  Что делать:
    • Открыть ОБА порта с сохранёнными параметрами.
    • Держать канал до close_physical_channel.
    • Если уже открыто — идемпотентно вернуть успех с текущими ports.

  Возврат при успехе:
    {"ok": True, "ports": ["COM1", "COM2"]}

  Возврат при ошибке:
    {"ok": False, "error": "COM1 занят другим приложением"}
    {"ok": False, "error": "Сначала сохраните параметры соединения"}
  """
  return {"ok": False, "error": "not implemented"}


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
  return {"ok": False, "error": "not implemented"}


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
  return {"ok": False, "error": "not implemented"}


def send_message(text: str, destination: Destination) -> dict[str, Any]:
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

  return {"ok": False, "error": "not implemented"}

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
  """"

  return {"ok": False, "error": "not implemented"}

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
  return {"ok": False, "error": "not implemented"}


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
  return {"ok": False, "error": "not implemented"}


def send_message(text: str, destination: Destination) -> dict[str, Any]:
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
  return {"ok": False, "error": "not implemented"}