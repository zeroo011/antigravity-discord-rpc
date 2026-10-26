"""
Cross-platform process detection for Google Antigravity.
Detects if Antigravity IDE, desktop application, or language server is running.
"""

import os
import sys
import logging

logger = logging.getLogger("antigravity_rpc.process_monitor")

TARGET_KEYWORDS = ("antigravity", "language_server")


def is_antigravity_running() -> bool:
    """Checks whether any Antigravity application process is currently running."""

    # 1. Linux / procfs (fastest, zero-overhead, zero subprocesses)
    if os.path.exists("/proc"):
        try:
            for pid_dir in os.listdir("/proc"):
                if not pid_dir.isdigit():
                    continue
                try:
                    with open(f"/proc/{pid_dir}/cmdline", "rb") as f:
                        cmd = f.read().decode("utf-8", errors="ignore").lower()
                        # Ignore this RPC service itself
                        if "antigravity-discord-rpc" in cmd:
                            continue
                        if any(k in cmd for k in TARGET_KEYWORDS):
                            return True
                except (IOError, PermissionError):
                    continue
            return False
        except Exception as e:
            logger.debug(f"Error reading /proc: {e}")

    # 2. Windows implementation
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            TH32CS_SNAPPROCESS = 0x00000002

            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ("dwSize", wintypes.DWORD),
                    ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
                    ("th32ModuleID", wintypes.DWORD),
                    ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD),
                    ("szExeFile", ctypes.c_char * 260),
                ]

            snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            entry = PROCESSENTRY32()
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32)

            has_next = ctypes.windll.kernel32.Process32First(snapshot, ctypes.byref(entry))
            while has_next:
                exe_name = entry.szExeFile.decode("latin-1", errors="ignore").lower()
                if ("antigravity" in exe_name or "language_server" in exe_name) and "daemon" not in exe_name:
                    ctypes.windll.kernel32.CloseHandle(snapshot)
                    return True
                has_next = ctypes.windll.kernel32.Process32Next(snapshot, ctypes.byref(entry))
            ctypes.windll.kernel32.CloseHandle(snapshot)
            return False
        except Exception as e:
            logger.debug(f"Windows process snapshot failed: {e}")
            # Fallback to tasklist
            try:
                import subprocess
                out = subprocess.check_output('tasklist /FI "IMAGENAME eq Antigravity.exe"', shell=True, stderr=subprocess.DEVNULL)
                return b"Antigravity.exe" in out or b"antigravity.exe" in out
            except Exception:
                return True

    # 3. macOS / general POSIX fallback
    try:
        import subprocess
        out = subprocess.check_output(["pgrep", "-f", "antigravity"], stderr=subprocess.DEVNULL)
        pids = [p.strip() for p in out.decode().split() if p.strip()]
        # Check if any PID is not our daemon
        my_pid = str(os.getpid())
        active_pids = [p for p in pids if p != my_pid]
        return len(active_pids) > 0
    except Exception:
        return True
