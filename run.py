"""TUI entrypoint."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.tui import NeetCodeApp


def _load_env() -> None:
    """Load key=value pairs from .env then .env.local (latter wins).

    A real value already in the process environment always takes precedence over
    both files.
    """
    root = Path(__file__).parent
    for name in (".env", ".env.local"):
        env_file = root / name
        if not env_file.exists():
            continue
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and not os.environ.get(key):
                os.environ[key] = value


def main() -> None:
    _load_env()
    NeetCodeApp().run()


if __name__ == "__main__":
    main()
