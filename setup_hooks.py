#!/usr/bin/env python3
"""
Setup script for Antigravity Discord RPC hooks.
Generates and merges hooks configuration for Antigravity on Linux, macOS, and Windows.
"""

import os
import sys
import json
import argparse


def get_default_config_path(global_install: bool = True) -> str:
    """Returns path to Antigravity hooks.json."""
    if global_install:
        home = os.path.expanduser("~")
        return os.path.join(home, ".gemini", "config", "hooks.json")
    else:
        return os.path.join(os.getcwd(), ".agents", "hooks.json")


def generate_hook_config(project_dir: str, python_cmd: str = None, is_example: bool = False) -> dict:
    """Generates the hooks configuration dictionary."""
    if is_example:
        python_cmd = "python3"
        main_script = "<PATH_TO_ANTIGRAVITY_DISCORD_RPC>/main.py"
    else:
        if not python_cmd:
            python_cmd = sys.executable
        main_script = os.path.abspath(os.path.join(project_dir, "main.py"))

    # Escape paths for shell safety
    def make_cmd(event: str) -> str:
        return f'"{python_cmd}" "{main_script}" --hook --event {event}'

    return {
        "antigravity-discord-rpc": {
            "enabled": True,
            "SessionStart": [
                {
                    "type": "command",
                    "command": make_cmd("SessionStart"),
                    "timeout": 5,
                }
            ],
            "PreInvocation": [
                {
                    "type": "command",
                    "command": make_cmd("PreInvocation"),
                    "timeout": 5,
                }
            ],
            "PreToolUse": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": make_cmd("PreToolUse"),
                            "timeout": 5,
                        }
                    ],
                }
            ],
            "Stop": [
                {
                    "type": "command",
                    "command": make_cmd("Stop"),
                    "timeout": 5,
                }
            ],
        }
    }


def install_hooks(target_file: str, hook_config: dict):
    """Installs or merges hook config into target hooks.json."""
    os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)

    existing = {}
    if os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    existing.update(hook_config)

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    print(f"Hooks successfully configured in: {target_file}")


def main():
    parser = argparse.ArgumentParser(description="Configure Antigravity Discord RPC hooks")
    parser.add_argument("--global", dest="is_global", action="store_true", default=True,
                        help="Install into ~/.gemini/config/hooks.json (default)")
    parser.add_argument("--workspace", dest="is_global", action="store_false",
                        help="Install into current project .agents/hooks.json")
    parser.add_argument("--path", default=None, help="Custom target hooks.json path")
    args = parser.parse_args()

    project_dir = os.path.dirname(os.path.abspath(__file__))

    # Generate a generic template for git/distribution
    example_cfg = generate_hook_config(
        project_dir="",
        is_example=True
    )
    example_path = os.path.join(project_dir, "hooks.example.json")
    with open(example_path, "w", encoding="utf-8") as f:
        json.dump(example_cfg, f, indent=2, ensure_ascii=False)

    # Generate active configuration with current python and path
    cfg = generate_hook_config(project_dir)
    target = args.path if args.path else get_default_config_path(args.is_global)
    install_hooks(target, cfg)


if __name__ == "__main__":
    main()
