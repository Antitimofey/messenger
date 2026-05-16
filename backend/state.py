"""Состояние каналов (заглушка физического и канального уровней)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AppState:
    physical_open: bool = False
    logical_connected: bool = False
    open_ports: list[str] = field(default_factory=list)


state = AppState()
