"""Хранение параметров COM и настроек приложения."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parent / "data"
_SETTINGS_FILE = _DATA_DIR / "settings.json"
_PREFS_FILE = _DATA_DIR / "preferences.json"

_DEFAULT_LINE: dict[str, Any] = {
    "baudrate": 9600,
    "bytesize": 8,
    "parity": "N",
    "stopbits": 1,
    "timeout": 1.0,
}

DEFAULT_SETTINGS: dict[str, Any] = {
    "portCom1": "COM1",
    "portCom2": "COM2",
    "nodeAddress": 1,
    "com1": dict(_DEFAULT_LINE),
    "com2": dict(_DEFAULT_LINE),
}

DEFAULT_PREFERENCES: dict[str, Any] = {
    "workMode": "file",
    "destination": 2,
    "receiveDirectory": "./received",
}


def _ensure_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _migrate_settings(data: dict[str, Any]) -> dict[str, Any]:
    """Старый формат: baudRate, dataBits, parity (none/even/odd) на оба порта."""
    if "com1" in data and "com2" in data:
        return data

    parity_map = {"none": "N", "even": "E", "odd": "O", "N": "N", "E": "E", "O": "O"}
    legacy_parity = str(data.get("parity", "none")).lower()
    line = {
        "baudrate": int(data.get("baudRate", _DEFAULT_LINE["baudrate"])),
        "bytesize": int(data.get("dataBits", _DEFAULT_LINE["bytesize"])),
        "parity": parity_map.get(legacy_parity, "N"),
        "stopbits": float(data.get("stopBits", _DEFAULT_LINE["stopbits"])),
        "timeout": float(data.get("timeout", _DEFAULT_LINE["timeout"])),
    }
    return {
        "portCom1": data.get("portCom1", "COM1"),
        "portCom2": data.get("portCom2", "COM2"),
        "nodeAddress": data.get("nodeAddress", 1),
        "com1": dict(line),
        "com2": dict(line),
    }


def load_settings() -> dict[str, Any]:
    _ensure_dir()
    if _SETTINGS_FILE.exists():
        with _SETTINGS_FILE.open(encoding="utf-8") as f:
            merged = {**DEFAULT_SETTINGS, **json.load(f)}
            return {**DEFAULT_SETTINGS, **_migrate_settings(merged)}
    return dict(DEFAULT_SETTINGS)


def save_settings(data: dict[str, Any]) -> dict[str, Any]:
    _ensure_dir()
    merged = {**DEFAULT_SETTINGS, **_migrate_settings({**DEFAULT_SETTINGS, **data})}
    with _SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    return merged


def load_preferences() -> dict[str, Any]:
    _ensure_dir()
    if _PREFS_FILE.exists():
        with _PREFS_FILE.open(encoding="utf-8") as f:
            return {**DEFAULT_PREFERENCES, **json.load(f)}
    return dict(DEFAULT_PREFERENCES)


def save_preferences(data: dict[str, Any]) -> dict[str, Any]:
    _ensure_dir()
    merged = {**DEFAULT_PREFERENCES, **data}
    with _PREFS_FILE.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    return merged
