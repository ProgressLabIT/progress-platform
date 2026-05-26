"""Module entrypoint — `python -m sparkplug_bridge.historian` invokes this.

Required by deploy/compose/sparkplug.yaml `command: ["python", "-m", "sparkplug_bridge.historian"]`.
Mirrors backend/sparkplug_bridge/main.py:623-628.
"""
import asyncio
import sys

from .ingester import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
