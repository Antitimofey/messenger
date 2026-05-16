"""
Тонкий мост Eel → channel.stack.requirements.
Безопасные обёртки: таймаут, чтобы COM/eel не блокировали WebSocket.
"""

from __future__ import annotations

from typing import Any, Callable

import gevent
from gevent.timeout import Timeout as GeventTimeout

from phisical.physical import COMPortSettings
from settings_store import load_settings, save_settings as persist_settings

from channel.stack import requirements as req

EEL_CALL_TIMEOUT = 15.0


def _eel_safe(fn: Callable[..., dict[str, Any]], *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        with GeventTimeout(EEL_CALL_TIMEOUT, False):
            return fn(*args, **kwargs)
    except GeventTimeout:
        return {"ok": False, "error": f"Таймаут операции ({int(EEL_CALL_TIMEOUT)} с)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _line_to_com_port(port_name: str, line: dict[str, Any]) -> COMPortSettings:
    return COMPortSettings(
        port_name=port_name,
        baudrate=int(line.get("baudrate", 9600)),
        bytesize=int(line.get("bytesize", 8)),
        parity=str(line.get("parity", "N")),
        stopbits=float(line.get("stopbits", 1)),
        timeout=float(line.get("timeout", 1.0)),
    )


def _apply_saved_settings(s: dict[str, Any]) -> None:
    com1 = _line_to_com_port(s["portCom1"], s.get("com1", {}))
    com2 = _line_to_com_port(s["portCom2"], s.get("com2", {}))
    req.save_settings("input", com1)
    req.save_settings("output", com2)


def list_ports() -> dict[str, Any]:
    return _eel_safe(req.list_ports)


def save_settings(data: dict[str, Any]) -> dict[str, Any]:
    try:
        merged = persist_settings(data)
        _apply_saved_settings(merged)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def open_physical_channel() -> dict[str, Any]:
    try:
        s = load_settings()
        if not s.get("portCom1") or not s.get("portCom2"):
            return {"ok": False, "error": "Сначала сохраните параметры соединения"}
        _apply_saved_settings(s)
        result = _eel_safe(req.open_physical_channel, int(s.get("nodeAddress", 1)))
        if result.get("ok"):
            return {**result, "ports": [s["portCom1"], s["portCom2"]]}
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


def close_physical_channel() -> dict[str, Any]:
    return _eel_safe(req.close_physical_channel)


def connect_logical() -> dict[str, Any]:
    return _eel_safe(req.connect_logical)


def disconnect_logical() -> dict[str, Any]:
    return _eel_safe(req.disconnect_logical)


def send_message(text: str, destination: str) -> dict[str, Any]:
    return _eel_safe(req.send_message, text, str(destination))


def get_message() -> dict[str, Any]:
    return _eel_safe(req.get_message)
