"""Централизованная настройка логов для разработчиков (не дискорд-логи).

Все модули уже берут свой логгер через ``logging.getLogger(__name__)`` и
пишут в корневой логгер. Здесь мы один раз настраиваем этот корень: уровень,
формат и цвет в консоли. Уровень берётся из LOG_LEVEL, чтобы на проде можно
было поднять до WARNING, а локально опустить до DEBUG без правки кода.

Уровни: DEBUG / INFO / WARNING / ERROR. WARN принимается как синоним WARNING.
"""

from __future__ import annotations

import logging
import sys

# принимаем WARN как привычный синоним стандартного WARNING
_ALIASES = {"WARN": "WARNING"}

# ansi-цвета по уровню, только для tty (в файле/пайпе цвет превратился бы в мусор)
_COLORS = {
    logging.DEBUG: "\033[36m",  # cyan
    logging.INFO: "\033[32m",  # green
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[1;31m",  # bright red
}
_RESET = "\033[0m"

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

# discord.py очень болтлив на INFO (heartbeat, реконнекты, gateway). держим его
# на ступень выше корня, иначе наши логи тонут в служебном шуме библиотеки
_NOISY_LOGGERS = ("discord", "discord.http", "discord.gateway")

# имя нашего хендлера, чтобы при повторном setup_logging найти его и не дублировать
_HANDLER_NAME = "kool_bot"


def resolve_level(level: str | int | None, default: int = logging.INFO) -> int:
    """Превращает имя уровня ('debug', 'WARN', ...) или число в logging.*.

    Неизвестное значение не роняет бота, а откатывается к default — кривой
    LOG_LEVEL в окружении не должен мешать запуску.
    """
    if level is None:
        return default
    if isinstance(level, int):
        return level
    name = level.strip().upper()
    name = _ALIASES.get(name, name)
    resolved = logging.getLevelName(name)
    # getLevelName для неизвестного имени возвращает строку 'Level XXX'
    return resolved if isinstance(resolved, int) else default


class _ColorFormatter(logging.Formatter):
    """Подкрашивает уровень, когда пишем в терминал."""

    def format(self, record: logging.LogRecord) -> str:
        color = _COLORS.get(record.levelno)
        if color:
            # подменяем только на время форматирования, чтобы не портить record
            # для других хендлеров
            original = record.levelname
            record.levelname = f"{color}{original}{_RESET}"
            try:
                return super().format(record)
            finally:
                record.levelname = original
        return super().format(record)


def setup_logging(level: str | int | None = None, *, stream=None) -> logging.Logger:
    """Настраивает корневой логгер один раз и возвращает его.

    Повторный вызов не плодит хендлеры (актуально для тестов и горячей
    перезагрузки), а лишь обновляет уровень.
    """
    if stream is None:
        stream = sys.stderr

    root = logging.getLogger()
    resolved = resolve_level(level)
    root.setLevel(resolved)

    handler = next(
        (h for h in root.handlers if h.get_name() == _HANDLER_NAME),
        None,
    )
    if handler is None:
        handler = logging.StreamHandler(stream)
        handler.set_name(_HANDLER_NAME)  # метка «наш», чтобы не дублировать при повторе
        root.addHandler(handler)

    use_color = hasattr(stream, "isatty") and stream.isatty()
    formatter_cls = _ColorFormatter if use_color else logging.Formatter
    handler.setFormatter(formatter_cls(_FORMAT, datefmt=_DATEFMT))

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(max(resolved, logging.WARNING))

    return root
