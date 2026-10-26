"""
Local IPC transport between Antigravity Hooks and the RPC Daemon.
Supports Unix domain sockets on POSIX and localhost TCP on Windows.
"""

import os
import sys
import json
import socket
import logging
from typing import Callable, Optional

from . import config

logger = logging.getLogger("antigravity_rpc.channel")


def send_hook_event(event_data: dict, timeout: float = 0.5) -> bool:
    """
    Sends an event payload from hook.py to the daemon.
    Non-blocking, fails gracefully in milliseconds if daemon is offline.
    """
    data = (json.dumps(event_data) + "\n").encode("utf-8")

    # 1. Try Unix domain socket if on POSIX
    if config.IPC_UNIX_SOCKET and os.path.exists(config.IPC_UNIX_SOCKET):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect(config.IPC_UNIX_SOCKET)
            s.sendall(data)
            s.close()
            return True
        except Exception as e:
            logger.debug(f"Unix socket connection failed: {e}")

    # 2. Try TCP localhost (Windows or POSIX fallback)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((config.IPC_TCP_HOST, config.IPC_TCP_PORT))
        s.sendall(data)
        s.close()
        return True
    except Exception as e:
        logger.debug(f"TCP socket connection failed: {e}")
        return False


class LocalIPCServer:
    """
    Async/non-blocking listener for hook events in daemon.py.
    """

    def __init__(self, on_message: Callable[[dict], None]):
        self.on_message = on_message
        self.unix_sock = None
        self.tcp_sock = None
        self.running = False

    def start(self):
        self.running = True

        # Start Unix socket listener if available
        if config.IPC_UNIX_SOCKET:
            try:
                if os.path.exists(config.IPC_UNIX_SOCKET):
                    os.unlink(config.IPC_UNIX_SOCKET)
                self.unix_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.unix_sock.bind(config.IPC_UNIX_SOCKET)
                self.unix_sock.listen(16)
                self.unix_sock.setblocking(False)
                # Secure permissions (owner only)
                try:
                    os.chmod(config.IPC_UNIX_SOCKET, 0o600)
                except Exception:
                    pass
                logger.info(f"Listening on Unix socket: {config.IPC_UNIX_SOCKET}")
            except Exception as e:
                logger.warning(f"Could not bind Unix socket: {e}")
                self.unix_sock = None

        # Always start TCP listener (for Windows and universal fallback)
        try:
            self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_sock.bind((config.IPC_TCP_HOST, config.IPC_TCP_PORT))
            self.tcp_sock.listen(16)
            self.tcp_sock.setblocking(False)
            logger.info(f"Listening on TCP: {config.IPC_TCP_HOST}:{config.IPC_TCP_PORT}")
        except Exception as e:
            logger.warning(f"Could not bind TCP port: {e}")
            self.tcp_sock = None

    def get_sockets(self):
        socks = []
        if self.unix_sock:
            socks.append(self.unix_sock)
        if self.tcp_sock:
            socks.append(self.tcp_sock)
        return socks

    def handle_connection(self, sock: socket.socket):
        try:
            client, _ = sock.accept()
            client.settimeout(0.5)
            raw = b""
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                raw += chunk
                if b"\n" in raw:
                    break
            client.close()

            line = raw.strip()
            if line:
                payload = json.loads(line.decode("utf-8", errors="ignore"))
                self.on_message(payload)
        except Exception as e:
            logger.debug(f"Error handling IPC connection: {e}")

    def close(self):
        self.running = False
        if self.unix_sock:
            try:
                self.unix_sock.close()
            except Exception:
                pass
            if config.IPC_UNIX_SOCKET and os.path.exists(config.IPC_UNIX_SOCKET):
                try:
                    os.unlink(config.IPC_UNIX_SOCKET)
                except Exception:
                    pass
            self.unix_sock = None

        if self.tcp_sock:
            try:
                self.tcp_sock.close()
            except Exception:
                pass
            self.tcp_sock = None
