"""
Tests for local IPC communication between hook and daemon.
"""

import os
import sys
import time
import socket
import select
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ipc_channel import LocalIPCServer, send_hook_event


class TestLocalIPC(unittest.TestCase):
    def test_send_and_receive_event(self):
        received_events = []

        def on_msg(payload):
            received_events.append(payload)

        server = LocalIPCServer(on_msg)
        server.start()

        # Allow socket to bind
        time.sleep(0.05)

        test_payload = {
            "type": "thinking",
            "state": "Вайбкодит",
            "details": "Тестирование IPC",
        }

        # Send event
        sent = send_hook_event(test_payload, timeout=1.0)
        self.assertTrue(sent, "Failed to send hook event via local IPC")

        # Process server connection
        readable = server.get_sockets()
        r, _, _ = select.select(readable, [], [], 1.0)
        for s in r:
            server.handle_connection(s)

        server.close()

        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0]["state"], "Вайбкодит")
        self.assertEqual(received_events[0]["details"], "Тестирование IPC")


if __name__ == "__main__":
    unittest.main()
