#!/usr/bin/env python3
"""
Antigravity Discord RPC - Universal Entrypoint.
Usage:
  python main.py             # Start RPC daemon
  python main.py --test      # Test connection to Discord
  python main.py --hook ...  # Internal hook dispatch
"""

import sys
from src.daemon import main as daemon_main
from src.hook import main as hook_main

if __name__ == "__main__":
    if "--hook" in sys.argv:
        sys.argv.remove("--hook")
        hook_main()
    else:
        daemon_main()
