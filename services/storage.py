from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _atomic_write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def write_json_sync(path: Path, data: Any) -> None:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    _atomic_write(path, payload)


async def write_json(path: Path, data: Any) -> None:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    await asyncio.to_thread(_atomic_write, path, payload)
