#!/usr/bin/env bash
set -e

echo "=== Antigravity Discord RPC Setup (Linux / macOS) ==="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH."
    exit 1
fi

PYTHON_BIN=$(command -v python3)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Python: $PYTHON_BIN"
echo "Project directory: $SCRIPT_DIR"

# Generate and install hooks
echo ""
echo "Configuring Antigravity hooks..."
"$PYTHON_BIN" "$SCRIPT_DIR/setup_hooks.py" --global

# Test Discord connection
echo ""
echo "Checking Discord connection..."
"$PYTHON_BIN" "$SCRIPT_DIR/main.py" --test || echo "Note: Discord is not currently active, but the daemon will connect automatically when Discord launches."

echo ""
echo "Setup complete!"
echo "To run the daemon in the background:"
echo "  nohup $PYTHON_BIN $SCRIPT_DIR/main.py >/dev/null 2>&1 &"
echo ""
echo "Or using systemd user service (Linux):"
echo "  mkdir -p ~/.config/systemd/user/"
echo "  sed \"s|%PROJECT_DIR%|$SCRIPT_DIR|g; s|%PYTHON_BIN%|$PYTHON_BIN|g\" $SCRIPT_DIR/antigravity-rpc.service > ~/.config/systemd/user/antigravity-rpc.service"
echo "  systemctl --user daemon-reload"
echo "  systemctl --user enable --now antigravity-rpc.service"
