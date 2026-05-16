#!/usr/bin/env python3
"""Локальная безадаптерная сеть — Python + Eel + React."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
ROOT = BACKEND_DIR.parent
WEB_DIR = ROOT / "frontend" / "dist"

sys.path.insert(0, str(BACKEND_DIR))

import eel

import bridge

eel.expose(bridge.list_ports)
eel.expose(bridge.save_settings_bridge, "save_settings")
eel.expose(bridge.open_physical_channel)
eel.expose(bridge.close_physical_channel)
eel.expose(bridge.connect_logical)
eel.expose(bridge.disconnect_logical)
eel.expose(bridge.send_message)


def main() -> None:
    if not WEB_DIR.is_dir():
        print("Соберите фронтенд: cd frontend && npm run build", file=sys.stderr)
        sys.exit(1)

    eel.init(str(WEB_DIR))
    eel.start("index.html", size=(780, 640), port=8080, mode="chrome")


if __name__ == "__main__":
    main()
