"""
Tests for Antigravity hook payload parsing and privacy sanitization.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.hook import sanitize_filename, sanitize_command, parse_payload


class TestHookSanitization(unittest.TestCase):
    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("/home/user/workspace/src/app.py"), "app.py")
        self.assertEqual(sanitize_filename(r"C:\Users\Admin\Project\index.ts"), "index.ts")
        self.assertEqual(sanitize_filename(""), "файл")

    def test_sanitize_command(self):
        # Normal command
        self.assertEqual(sanitize_command("npm test"), "npm test")

        # Command with sensitive token
        cmd_with_token = "curl -H 'Authorization: token=ghp_secret12345' https://api.github.com"
        sanitized = sanitize_command(cmd_with_token)
        self.assertNotIn("ghp_secret12345", sanitized)
        self.assertIn("[скрыто]", sanitized)

        # Uses toolSummary if provided
        self.assertEqual(sanitize_command("rm -rf something", summary="Clean build cache"), "Clean build cache")


class TestHookPayloadParsing(unittest.TestCase):
    def test_pre_invocation(self):
        res = parse_payload("PreInvocation", {"modelName": "Gemini 3.8 Flash"})
        self.assertEqual(res["type"], "thinking")
        self.assertEqual(res["state"], "Вайбкодит")

    def test_pre_tool_use_edit(self):
        raw = {
            "toolCall": {
                "name": "edit_file",
                "args": {
                    "Path": "/home/developer/project/server.py"
                }
            }
        }
        res = parse_payload("PreToolUse", raw)
        self.assertEqual(res["type"], "editing")
        self.assertEqual(res["state"], "Редактирует код")
        self.assertIn("server.py", res["details"])
        self.assertNotIn("/home/developer", res["details"])  # Privacy check!

    def test_pre_tool_use_run_command(self):
        raw = {
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": "pytest -v",
                    "toolSummary": "Run test suite"
                }
            }
        }
        res = parse_payload("PreToolUse", raw)
        self.assertEqual(res["type"], "terminal")
        self.assertEqual(res["state"], "Запускает команду")
        self.assertIn("Run test suite", res["details"])

    def test_stop_event(self):
        res = parse_payload("Stop", {"terminationReason": "NO_TOOL_CALL"})
        self.assertEqual(res["type"], "idle")
        self.assertEqual(res["state"], "В режиме ожидания")


if __name__ == "__main__":
    unittest.main()
