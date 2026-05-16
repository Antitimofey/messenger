#!/usr/bin/env python3
"""Eel API-сервер (requirements.py). Фронтенд — отдельно: npm run dev."""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
EEL_WEB = BACKEND_DIR / "eel_web"

sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent / ".env")

BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8888"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5173"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", f"http://localhost:{FRONTEND_PORT}")

import eel

import bridge

eel.init(str(EEL_WEB))

eel.expose(bridge.list_ports)
eel.expose(bridge.save_settings)
eel.expose(bridge.open_physical_channel)
eel.expose(bridge.close_physical_channel)
eel.expose(bridge.connect_logical)
eel.expose(bridge.disconnect_logical)
eel.expose(bridge.send_message)
eel.expose(bridge.get_message)


def main() -> None:
    print(f"Eel API: http://localhost:{BACKEND_PORT}")
    print(f"Ожидается фронтенд: {FRONTEND_ORIGIN}")
    print("Загрузите eel.js через Vite (/eel.js) при npm run dev.")
    eel.start(
        "index.html",
        host="localhost",
        port=BACKEND_PORT,
        mode=None,
        cmdline_args=[],
    )


if __name__ == "__main__":
    main()
