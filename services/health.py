"""Файловый heartbeat для докер-healthcheck.

Бот периодически перезаписывает HEARTBEAT_FILE текущим unix-временем, пока
жив event loop и установлено соединение с гейтвеем. HEALTHCHECK в образе
читает этот файл и считает контейнер здоровым, только если отметка свежая.

Это заменяет греп логов на строку готовности (её мог напечатать любой образ)
на проверку реальной живости процесса для отката деплоя.
"""

from __future__ import annotations

import time
from pathlib import Path

from config import DATA_DIR

HEARTBEAT_FILE = DATA_DIR / ".heartbeat"

# контейнер считается нездоровым, если heartbeat не обновлялся дольше этого
MAX_AGE_SECONDS = 90


def write_heartbeat(path: Path = HEARTBEAT_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(time.time()), encoding="utf-8")


def is_healthy(path: Path = HEARTBEAT_FILE, max_age: float = MAX_AGE_SECONDS) -> bool:
    try:
        raw = path.read_text(encoding="utf-8").strip()
        last = float(raw)
    except (OSError, ValueError):
        return False
    return (time.time() - last) <= max_age
