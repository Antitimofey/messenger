"""
Тонкий мост Eel → channel.stack.requirements.
Преобразует только save_settings (dict с фронта) и open_physical_channel (адрес узла).
"""

from __future__ import annotations

from typing import Any

from phisical.physical import COMPortSettings
from settings_store import load_settings, save_settings as persist_settings

from channel.stack import requirements as req


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


def save_settings(data: dict[str, Any]) -> dict[str, Any]:
    """Сохранить JSON с фронта и применить к rx/tx."""
    try:
        merged = persist_settings(data)
        _apply_saved_settings(merged)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def open_physical_channel() -> dict[str, Any]:
    """Открыть физический канал (номер узла из сохранённых настроек)."""
    try:
        s = load_settings()
        if not s.get("portCom1") or not s.get("portCom2"):
            return {"ok": False, "error": "Сначала сохраните параметры соединения"}
        _apply_saved_settings(s)
        result = req.open_physical_channel(int(s.get("nodeAddress", 1)))
        if result.get("ok"):
            return {
                **result,
                "ports": [s["portCom1"], s["portCom2"]],
            }
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}
