"""
Zero-dependency Discord IPC implementation supporting Linux, macOS, and Windows.
"""

import os
import sys
import json
import time
import uuid
import struct
import logging

logger = logging.getLogger("antigravity_rpc.discord_ipc")

OP_HANDSHAKE = 0
OP_FRAME = 1
OP_CLOSE = 2
OP_PING = 3
OP_PONG = 4


class DiscordIPCConnection:
    """Manages low-level connection to Discord IPC across platforms."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.connected = False
        self._sock = None
        self._pipe = None

    def _find_ipc_target(self):
        """Finds the active Discord IPC socket (Unix) or named pipe (Windows)."""
        if sys.platform == "win32":
            for i in range(10):
                pipe_path = rf"\\.\pipe\discord-ipc-{i}"
                if os.path.exists(pipe_path):
                    return ("pipe", pipe_path)
            return ("pipe", r"\\.\pipe\discord-ipc-0")

        # POSIX (Linux / macOS)
        search_dirs = []
        if "XDG_RUNTIME_DIR" in os.environ:
            search_dirs.append(os.environ["XDG_RUNTIME_DIR"])
        if hasattr(os, "getuid"):
            search_dirs.append(f"/run/user/{os.getuid()}")
        if "TMPDIR" in os.environ:
            search_dirs.append(os.environ["TMPDIR"])
        search_dirs.extend(["/tmp", "/var/tmp"])

        for d in search_dirs:
            if not os.path.exists(d):
                continue
            for i in range(10):
                sock_path = os.path.join(d, f"discord-ipc-{i}")
                if os.path.exists(sock_path):
                    return ("socket", sock_path)

        return None

    def connect(self) -> bool:
        """Connects and handshakes with Discord IPC."""
        self.close()
        target = self._find_ipc_target()
        if not target:
            logger.debug("Discord IPC socket/pipe not found. Is Discord running?")
            return False

        kind, path = target
        try:
            if kind == "socket":
                import socket
                self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self._sock.settimeout(5.0)
                self._sock.connect(path)
            else:
                # Windows named pipe
                self._pipe = open(path, "r+b", buffering=0)

            # Send handshake
            handshake = json.dumps({"v": 1, "client_id": str(self.client_id)}).encode("utf-8")
            self._write_packet(OP_HANDSHAKE, handshake)
            op, resp = self._read_packet()

            if op == OP_FRAME and resp.get("cmd") == "DISPATCH":
                self.connected = True
                logger.info(f"Connected to Discord IPC via {path}")
                return True
            else:
                logger.warning(f"Unexpected handshake response: op={op}, resp={resp}")
                self.close()
                return False

        except Exception as e:
            logger.debug(f"Failed to connect to Discord IPC: {e}")
            self.close()
            return False

    def _write_packet(self, opcode: int, data: bytes):
        header = struct.pack("<II", opcode, len(data))
        if self._sock:
            self._sock.sendall(header + data)
        elif self._pipe:
            self._pipe.write(header + data)
            self._pipe.flush()

    def _read_packet(self):
        if self._sock:
            header = self._recv_exact(8)
        elif self._pipe:
            header = self._pipe.read(8)
        else:
            return None, None

        if not header or len(header) < 8:
            return None, None

        opcode, length = struct.unpack("<II", header)
        if self._sock:
            payload = self._recv_exact(length)
        elif self._pipe:
            payload = self._pipe.read(length)
        else:
            return None, None

        data = json.loads(payload.decode("utf-8", errors="ignore"))
        return opcode, data

    def _recv_exact(self, size: int) -> bytes:
        chunks = []
        bytes_recd = 0
        while bytes_recd < size:
            chunk = self._sock.recv(min(size - bytes_recd, 4096))
            if not chunk:
                break
            chunks.append(chunk)
            bytes_recd += len(chunk)
        return b"".join(chunks)

    def set_activity(self, activity: dict) -> bool:
        """Sends SET_ACTIVITY command to Discord."""
        if not self.connected:
            if not self.connect():
                return False

        payload = {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": os.getpid(),
                "activity": activity,
            },
            "nonce": str(uuid.uuid4()),
        }

        try:
            raw_data = json.dumps(payload).encode("utf-8")
            self._write_packet(OP_FRAME, raw_data)
            op, resp = self._read_packet()
            return op == OP_FRAME and resp is not None
        except Exception as e:
            logger.warning(f"Error sending activity to Discord: {e}")
            self.close()
            return False

    def clear_activity(self) -> bool:
        """Clears the current activity in Discord."""
        return self.set_activity(None)

    def close(self):
        """Closes the connection safely."""
        self.connected = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        if self._pipe:
            try:
                self._pipe.close()
            except Exception:
                pass
            self._pipe = None
