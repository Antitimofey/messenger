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
from channel.stack import requirements as req

eel.init(str(EEL_WEB))

eel.expose(req.list_ports)
eel.expose(bridge.save_settings)
eel.expose(bridge.open_physical_channel)
eel.expose(req.close_physical_channel)
eel.expose(req.connect_logical)
eel.expose(req.disconnect_logical)
eel.expose(req.send_message)
eel.expose(req.get_message)


def main() -> None:
    print(f"Eel API: http://localhost:{BACKEND_PORT}")
    print(f"Ожидается фронтенд: {FRONTEND_ORIGIN}")
    print("Загрузите eel.js с этого хоста во фронтенде (VITE_BACKEND_PORT).")
    # mode=None — не открывать браузер; index.html — заглушка для API (eel.js)
    eel.start(
        "index.html",
        host="localhost",
        port=BACKEND_PORT,
        mode=None,
        cmdline_args=[],
    )


if __name__ == "__main__":
    main()
