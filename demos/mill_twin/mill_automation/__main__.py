"""Module entrypoint — `python -m mill_automation` invokes this."""
import asyncio
import sys

from .main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
