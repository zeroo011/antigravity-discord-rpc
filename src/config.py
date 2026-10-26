"""
Configuration settings for Antigravity Discord RPC.
"""

import os
import sys

# Discord Application Client ID.
# Create your own application at https://discord.com/developers/applications
# named 'Antigravity' to get custom Rich Presence name and assets.
# By default, uses a working public developer client ID.
DEFAULT_CLIENT_ID = "383226320970055681"
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", DEFAULT_CLIENT_ID)

# Idle timeout in seconds before switching to 'Idle' status
IDLE_TIMEOUT_SECONDS = int(os.getenv("RPC_IDLE_TIMEOUT", "120"))

# Local IPC channel settings for communication between Hook and Daemon
IPC_TCP_HOST = "127.0.0.1"
IPC_TCP_PORT = int(os.getenv("RPC_IPC_PORT", "39184"))

# Unix domain socket path for POSIX systems (Linux / macOS)
if sys.platform != "win32":
    runtime_dir = os.getenv("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}" if hasattr(os, "getuid") else "/tmp"
    if not os.path.exists(runtime_dir):
        runtime_dir = "/tmp"
    IPC_UNIX_SOCKET = os.path.join(runtime_dir, "antigravity_discord_rpc.sock")
else:
    IPC_UNIX_SOCKET = None

# Asset keys (configure these in Discord Developer Portal -> Rich Presence -> Art Assets)
ASSETS = {
    "large_image": "antigravity_logo",
    "large_text": "Google Antigravity",
    "thinking_icon": "thinking",
    "coding_icon": "coding",
    "terminal_icon": "terminal",
    "idle_icon": "idle",
}

# Status templates
STATUS_TEXTS = {
    "thinking": {
        "state": "Вайбкодит",
        "details": "Формулирует ответ...",
    },
    "editing": {
        "state": "Редактирует код",
        "details": "Файл: {filename}",
    },
    "terminal": {
        "state": "Запускает команду",
        "details": "{summary}",
    },
    "reading": {
        "state": "Анализирует проект",
        "details": "Файл: {filename}",
    },
    "research": {
        "state": "Ищет информацию",
        "details": "Поиск в сети...",
    },
    "idle": {
        "state": "В режиме ожидания",
        "details": "Готов к новым задачам",
    },
}
