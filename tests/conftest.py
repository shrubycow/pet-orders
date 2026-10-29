import asyncio
import os
import sys
from pathlib import Path


def _load_test_env() -> None:
    path = Path(__file__).resolve().parents[1] / '.env.test'
    if not path.is_file():
        raise RuntimeError(f'Missing {path}')
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")


# pet_orders is imported only after this call: settings, the engine, and
# the Redis client are created at import.
_load_test_env()

# Selector loop on Windows. Closing the default Proactor loop waits on
# unfinished socket I/O and pytest sits there until it is interrupted.
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
