"""Хранение параметров COM и настроек приложения (заглушка до реализации уровней)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parent / "data"
_SETTINGS_FILE = _DATA_DIR / "settings.json"
_PREFS_FILE = _DATA_DIR / "preferences.json"

DEFAULT_SETTINGS: dict[str, Any] = {
    "portCom1": "COM1",
    "portCom2": "COM2",
    "nodeAddress": 1,
    "baudRate": 9600,
    "dataBits": 8,
    "parity": "none",
    "stopBits": 1,
    "flowControl": "none",
    "readTimeout": 1000,
    "writeTimeout": 1000,
    "readBufferSize": 4096,
    "writeBufferSize": 2048,
}

DEFAULT_PREFERENCES: dict[str, Any] = {
    "workMode": "file",
    "destination": 2,
    "receiveDirectory": "./received",
}


def _ensure_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict[str, Any]:
    _ensure_dir()
    if _SETTINGS_FILE.exists():
        with _SETTINGS_FILE.open(encoding="utf-8") as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    return dict(DEFAULT_SETTINGS)


def save_settings(data: dict[str, Any]) -> dict[str, Any]:
    _ensure_dir()
    merged = {**DEFAULT_SETTINGS, **data}
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
