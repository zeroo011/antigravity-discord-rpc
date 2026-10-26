"""
Antigravity lifecycle hook runner.
Reads hook JSON from stdin, sanitizes sensitive data, and dispatches to RPC daemon.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

from . import config
from .ipc_channel import send_hook_event


def sanitize_filename(filepath: str) -> str:
    """Returns only the basename of a file to protect directory privacy."""
    if not filepath:
        return "файл"
    clean = filepath.strip("\"'").replace("\\", "/")
    return os.path.basename(clean) or "файл"


def sanitize_command(cmd: str, summary: str = "") -> str:
    """Returns a safe, high-level summary of a command without exposing secrets."""
    if summary:
        return summary[:40]
    if not cmd:
        return "команду"

    first_line = cmd.strip().split("\n")[0].strip()
    words = first_line.split()
    if not words:
        return "команду"

    # Avoid exposing sensitive arguments
    sensitive_keywords = {"token", "key", "password", "secret", "auth", "credential", "bearer"}
    safe_words = []
    for w in words:
        lower = w.lower()
        if any(k in lower for k in sensitive_keywords) and ("=" in w or ":" in w):
            safe_words.append("[скрыто]")
        else:
            safe_words.append(w)

    safe_str = " ".join(safe_words)
    return safe_str[:40] + ("..." if len(safe_str) > 40 else "")


def parse_payload(event_type: str, raw_json: Dict[str, Any]) -> Dict[str, Any]:
    """Parses Antigravity hook payload into a normalized RPC event."""
    model_name = raw_json.get("modelName", "")

    # PreInvocation: agent is thinking / vibecoding
    if event_type == "PreInvocation":
        return {
            "type": "thinking",
            "model": model_name,
            "state": config.STATUS_TEXTS["thinking"]["state"],
            "details": config.STATUS_TEXTS["thinking"]["details"],
            "icon": config.ASSETS["thinking_icon"],
        }

    # PreToolUse: agent is using a tool
    if event_type == "PreToolUse":
        tool_call = raw_json.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})

        if tool_name in ("edit_file", "write_file"):
            fname = sanitize_filename(tool_args.get("Path", ""))
            return {
                "type": "editing",
                "model": model_name,
                "state": config.STATUS_TEXTS["editing"]["state"],
                "details": config.STATUS_TEXTS["editing"]["details"].format(filename=fname),
                "icon": config.ASSETS["coding_icon"],
            }

        elif tool_name == "read_file":
            fname = sanitize_filename(tool_args.get("Path", ""))
            return {
                "type": "reading",
                "model": model_name,
                "state": config.STATUS_TEXTS["reading"]["state"],
                "details": config.STATUS_TEXTS["reading"]["details"].format(filename=fname),
                "icon": config.ASSETS["coding_icon"],
            }

        elif tool_name == "run_command":
            cmd = tool_args.get("CommandLine", "")
            summary = tool_args.get("toolSummary", "")
            safe_desc = sanitize_command(cmd, summary)
            return {
                "type": "terminal",
                "model": model_name,
                "state": config.STATUS_TEXTS["terminal"]["state"],
                "details": config.STATUS_TEXTS["terminal"]["details"].format(summary=safe_desc),
                "icon": config.ASSETS["terminal_icon"],
            }

        elif tool_name in ("search_web", "web_search"):
            return {
                "type": "research",
                "model": model_name,
                "state": config.STATUS_TEXTS["research"]["state"],
                "details": config.STATUS_TEXTS["research"]["details"],
                "icon": config.ASSETS["thinking_icon"],
            }

        elif tool_name == "invoke_subagent":
            role = tool_args.get("Role", "субагента")
            return {
                "type": "thinking",
                "model": model_name,
                "state": "Координирует субагента",
                "details": f"Роль: {role[:30]}",
                "icon": config.ASSETS["thinking_icon"],
            }

        else:
            return {
                "type": "thinking",
                "model": model_name,
                "state": config.STATUS_TEXTS["thinking"]["state"],
                "details": f"Инструмент: {tool_name[:25]}",
                "icon": config.ASSETS["thinking_icon"],
            }

    # Stop: agent finished its turn
    if event_type == "Stop":
        return {
            "type": "idle",
            "model": model_name,
            "state": config.STATUS_TEXTS["idle"]["state"],
            "details": config.STATUS_TEXTS["idle"]["details"],
            "icon": config.ASSETS["idle_icon"],
        }

    # Default fallback
    return {
        "type": "idle",
        "model": model_name,
        "state": config.STATUS_TEXTS["idle"]["state"],
        "details": config.STATUS_TEXTS["idle"]["details"],
        "icon": config.ASSETS["idle_icon"],
    }


def main():
    parser = argparse.ArgumentParser(description="Antigravity Discord RPC Hook Client")
    parser.add_argument("--event", required=True, help="Hook event type (PreInvocation, PreToolUse, Stop, etc.)")
    args = parser.parse_args()

    raw_input = {}
    try:
        if not sys.stdin.isatty():
            data = sys.stdin.read()
            if data.strip():
                raw_input = json.loads(data)
    except Exception:
        pass

    event_payload = parse_payload(args.event, raw_input)
    send_hook_event(event_payload)

    # Output valid response for Antigravity hook runner
    if args.event == "PreToolUse":
        print(json.dumps({"decision": "allow"}))
    else:
        print("{}")


if __name__ == "__main__":
    main()
