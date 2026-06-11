"""Точка входа для докер-HEALTHCHECK.

Выходит с кодом 0, если heartbeat-файл свежий, иначе 1. Используется в
Dockerfile (HEALTHCHECK ... CMD python healthcheck.py).
"""

import sys

from services.health import is_healthy


def main() -> int:
    return 0 if is_healthy() else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
