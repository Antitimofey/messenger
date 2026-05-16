"""
Мост Eel — функции из req.py (контракт для React).
"""

from __future__ import annotations

from typing import Any

from settings_store import load_settings, save_settings
from state import state

# --- Справочники и настройки ---


def list_ports() -> dict[str, Any]:
    s = load_settings()
    ports = sorted({s.get("portCom1", "COM1"), s.get("portCom2", "COM2"), "COM1", "COM2", "COM3"})
    return {"ok": True, "ports": list(ports)}


def save_settings_bridge(data: dict[str, Any]) -> dict[str, Any]:
    try:
        save_settings(data)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# --- Физический уровень ---


def open_physical_channel() -> dict[str, Any]:
    s = load_settings()
    if not s.get("portCom1") or not s.get("portCom2"):
        return {"ok": False, "error": "Сначала сохраните параметры соединения"}
    if state.physical_open:
        return {"ok": True, "ports": state.open_ports}
    # TODO: pyserial open
    state.physical_open = True
    state.open_ports = [s["portCom1"], s["portCom2"]]
    return {"ok": True, "ports": state.open_ports}


def close_physical_channel() -> dict[str, Any]:
    if state.logical_connected:
        disconnect_logical()
    state.physical_open = False
    state.open_ports = []
    return {"ok": True}


# --- Канальный уровень ---


def connect_logical() -> dict[str, Any]:
    if not state.physical_open:
        return {"ok": False, "error": "Физический канал не открыт"}
    # TODO: L-кадр, кольцо
    state.logical_connected = True
    return {"ok": True}


def disconnect_logical() -> dict[str, Any]:
    if not state.logical_connected:
        return {"ok": False, "error": "Логическое соединение не установлено"}
    state.logical_connected = False
    return {"ok": True}


# --- Прикладной уровень ---


def send_message(text: str, destination: str | int) -> dict[str, Any]:
    if not state.logical_connected:
        return {"ok": False, "error": "Нет логического соединения"}
    if not (text or "").strip():
        return {"ok": False, "error": "Пустое сообщение"}
    # TODO: кадры, адресация, CRC [7,4]
    _ = destination
    return {"ok": True}
