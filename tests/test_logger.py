import io
import logging

import pytest

from services.logger import (
    _ColorFormatter,
    resolve_level,
    setup_logging,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("debug", logging.DEBUG),
        ("INFO", logging.INFO),
        ("Warning", logging.WARNING),
        ("warn", logging.WARNING),  # синоним WARNING
        ("error", logging.ERROR),
        ("  info  ", logging.INFO),  # лишние пробелы стрипаются
        (logging.ERROR, logging.ERROR),  # число проходит как есть
    ],
)
def test_resolve_level_known(value, expected):
    assert resolve_level(value) == expected


def test_resolve_level_none_uses_default():
    assert resolve_level(None) == logging.INFO
    assert resolve_level(None, default=logging.ERROR) == logging.ERROR


def test_resolve_level_garbage_falls_back():
    # кривой LOG_LEVEL не должен ронять запуск, откатываемся к default
    assert resolve_level("nonsense") == logging.INFO
    assert resolve_level("nonsense", default=logging.DEBUG) == logging.DEBUG


@pytest.fixture
def clean_root():
    # сохраняем и восстанавливаем состояние корневого логгера, чтобы тесты
    # не подтекали друг в друга
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    root.handlers = []
    yield root
    root.handlers = saved_handlers
    root.setLevel(saved_level)


def test_setup_logging_sets_level_and_handler(clean_root):
    stream = io.StringIO()
    root = setup_logging("DEBUG", stream=stream)
    assert root.level == logging.DEBUG
    ours = [h for h in root.handlers if h.get_name() == "kool_bot"]
    assert len(ours) == 1


def test_setup_logging_is_idempotent(clean_root):
    stream = io.StringIO()
    setup_logging("INFO", stream=stream)
    setup_logging("WARNING", stream=stream)
    ours = [h for h in clean_root.handlers if h.get_name() == "kool_bot"]
    # повторный вызов не плодит хендлеры, но обновляет уровень
    assert len(ours) == 1
    assert clean_root.level == logging.WARNING


def test_setup_logging_emits_formatted_message(clean_root):
    stream = io.StringIO()
    setup_logging("INFO", stream=stream)
    logging.getLogger("test.module").info("hello %s", "world")
    out = stream.getvalue()
    assert "hello world" in out
    assert "INFO" in out
    assert "test.module" in out


def test_setup_logging_respects_level(clean_root):
    stream = io.StringIO()
    setup_logging("ERROR", stream=stream)
    logging.getLogger("quiet").info("should be hidden")
    assert stream.getvalue() == ""


def test_setup_logging_quiets_discord(clean_root):
    setup_logging("DEBUG", stream=io.StringIO())
    # болтливые логгеры библиотеки не должны опускаться ниже WARNING
    assert logging.getLogger("discord").level == logging.WARNING


def test_color_formatter_wraps_levelname_for_tty():
    formatter = _ColorFormatter("%(levelname)s %(message)s")
    record = logging.LogRecord("n", logging.ERROR, __file__, 1, "boom", None, None)
    out = formatter.format(record)
    assert "\033[31m" in out  # цвет ERROR
    assert "\033[0m" in out
    # record не испорчен для других хендлеров
    assert record.levelname == "ERROR"
