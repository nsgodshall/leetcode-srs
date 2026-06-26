"""TUI entrypoint."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.tui import NeetCodeApp


def _load_env() -> None:
    """Load key=value pairs from .env.local if it exists."""
    env_file = Path(__file__).parent / ".env.local"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> None:
    _load_env()
    NeetCodeApp().run()


if __name__ == "__main__":
    main()
