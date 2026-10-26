"""
Antigravity Discord RPC background daemon.
Listens for hook events and updates Discord Rich Presence via IPC.
"""

import os
import sys
import time
import select
import signal
import logging
import argparse
from typing import Optional

from . import config
from .discord_ipc import DiscordIPCConnection
from .ipc_channel import LocalIPCServer

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("antigravity_rpc.daemon")


class RPCDaemon:
    def __init__(self, client_id: str = config.CLIENT_ID, debug: bool = False):
        if debug:
            logger.setLevel(logging.DEBUG)
        self.client_id = client_id
        self.ipc = DiscordIPCConnection(client_id)
        self.ipc_server = LocalIPCServer(self.on_hook_event)
        self.running = False
        self.start_time = int(time.time())
        self.last_event_time = time.time()
        self.current_state = "idle"
        self.last_activity = None

    def on_hook_event(self, event: dict):
        """Called when hook.py sends an event via local IPC."""
        logger.debug(f"Received hook event: {event}")
        self.last_event_time = time.time()
        self.current_state = event.get("type", "thinking")

        state = event.get("state", "Вайбкодит")
        details = event.get("details", "")
        icon = event.get("icon", config.ASSETS["thinking_icon"])

        self.update_presence(state=state, details=details, small_icon=icon)

    def update_presence(self, state: str, details: str, small_icon: Optional[str] = None):
        """Formats activity payload and sends to Discord."""
        activity = {
            "state": state[:128],
            "timestamps": {
                "start": self.start_time,
            },
            "assets": {
                "large_image": config.ASSETS["large_image"],
                "large_text": config.ASSETS["large_text"],
            },
        }

        if details:
            activity["details"] = details[:128]

        if small_icon:
            activity["assets"]["small_image"] = small_icon
            activity["assets"]["small_text"] = state[:128]

        self.last_activity = activity
        success = self.ipc.set_activity(activity)
        if success:
            logger.info(f"Updated status: {state} | {details}")
        else:
            logger.debug(f"Presence update queued or Discord unavailable.")

    def check_idle(self):
        """Switches to idle status if no agent events received recently."""
        if self.current_state != "idle":
            elapsed = time.time() - self.last_event_time
            if elapsed >= config.IDLE_TIMEOUT_SECONDS:
                logger.info(f"Inactivity timeout ({config.IDLE_TIMEOUT_SECONDS}s). Switching to idle.")
                self.current_state = "idle"
                idle_cfg = config.STATUS_TEXTS["idle"]
                self.update_presence(
                    state=idle_cfg["state"],
                    details=idle_cfg["details"],
                    small_icon=config.ASSETS["idle_icon"],
                )

    def run(self):
        """Main service loop."""
        self.running = True
        self.ipc_server.start()

        # Connect to Discord initially
        logger.info(f"Starting Antigravity Discord RPC Daemon (Client ID: {self.client_id})...")
        if self.ipc.connect():
            # Initial idle status
            idle_cfg = config.STATUS_TEXTS["idle"]
            self.update_presence(
                state=idle_cfg["state"],
                details=idle_cfg["details"],
                small_icon=config.ASSETS["idle_icon"],
            )
        else:
            logger.info("Discord is not running yet. Daemon will auto-connect when Discord starts.")

        last_reconnect_attempt = 0
        last_idle_check = time.time()

        while self.running:
            try:
                # Poll IPC sockets with timeout
                readable_sockets = self.ipc_server.get_sockets()
                if readable_sockets:
                    r, _, _ = select.select(readable_sockets, [], [], 1.0)
                    for s in r:
                        self.ipc_server.handle_connection(s)
                else:
                    time.sleep(1.0)

                # Periodic check for idle status
                now = time.time()
                if now - last_idle_check >= 3.0:
                    self.check_idle()
                    last_idle_check = now

                # Auto-reconnect to Discord if disconnected
                if not self.ipc.connected and (now - last_reconnect_attempt >= 5.0):
                    last_reconnect_attempt = now
                    if self.ipc.connect() and self.last_activity:
                        self.ipc.set_activity(self.last_activity)

            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(1.0)

        self.shutdown()

    def shutdown(self):
        """Graceful shutdown."""
        logger.info("Stopping daemon and clearing presence...")
        self.running = False
        try:
            self.ipc.clear_activity()
            self.ipc.close()
        except Exception:
            pass
        self.ipc_server.close()
        logger.info("Daemon stopped.")


def main():
    parser = argparse.ArgumentParser(description="Antigravity Discord RPC Daemon")
    parser.add_argument("--client-id", default=config.CLIENT_ID, help="Discord Application Client ID")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--test", action="store_true", help="Send a single test presence and exit")
    args = parser.parse_args()

    daemon = RPCDaemon(client_id=args.client_id, debug=args.debug)

    if args.test:
        logger.info("Testing Discord connection...")
        if daemon.ipc.connect():
            daemon.update_presence(
                state="Вайбкодит (Тест)",
                details="Проверка работы Discord RPC",
                small_icon="coding",
            )
            print("Successfully updated Discord presence! Preserving for 5 seconds...")
            time.sleep(5)
            daemon.shutdown()
            sys.exit(0)
        else:
            print("Failed to connect to Discord IPC. Make sure Discord desktop is running.")
            sys.exit(1)

    # Setup signal handlers
    def _sig_handler(sig, frame):
        daemon.running = False

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    daemon.run()


if __name__ == "__main__":
    main()
