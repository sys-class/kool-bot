import asyncio
import logging
from unittest.mock import AsyncMock

import discord
import pytest

from services.discord_log import (
    LEVEL_COLORS,
    DiscordLogHandler,
    build_embed,
)


def _record(level=logging.WARNING, msg="boom", name="test.mod"):
    return logging.LogRecord(name, level, __file__, 10, msg, None, None)


@pytest.mark.parametrize(
    "level", [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
)
def test_build_embed_color_per_level(level):
    embed = build_embed(_record(level), logging.Formatter("%(message)s").format)
    assert embed.color.value == LEVEL_COLORS[level]
    assert embed.title == logging.getLevelName(level)


def test_build_embed_puts_message_in_codeblock():
    embed = build_embed(
        _record(msg="привет %s"), logging.Formatter("%(message)s").format
    )
    assert "привет %s" in embed.description
    assert embed.description.startswith("```")


def test_build_embed_truncates_long_message():
    embed = build_embed(
        _record(msg="x" * 9000), logging.Formatter("%(message)s").format
    )
    assert len(embed.description) < 4096  # лимит дискорда


def test_filter_drops_own_and_discord_records():
    handler = DiscordLogHandler(sender=AsyncMock(), loop=asyncio.new_event_loop())
    # Handler.filter возвращает запись (истинно) при прохождении, иначе False
    assert handler.filter(_record(name="cogs.voice"))
    assert not handler.filter(_record(name="discord.gateway"))
    assert not handler.filter(_record(name="services.discord_log"))


def _run_handler(record, *, ping_user_id=None):
    """Гоняет одну запись через хендлер и возвращает мок-sender."""

    async def go():
        sender = AsyncMock()
        handler = DiscordLogHandler(
            sender=sender,
            loop=asyncio.get_running_loop(),
            ping_user_id=ping_user_id,
            level=logging.DEBUG,
        )
        handler.start()
        handler.emit(record)
        # даём отработать call_soon-колбэку emit, прежде чем ждать очередь
        await asyncio.sleep(0)
        await asyncio.wait_for(handler.queue.join(), timeout=1)
        await handler.aclose()
        return sender

    return asyncio.run(go())


def test_emit_delivers_embed_via_sender():
    sender = _run_handler(_record(logging.WARNING))
    assert sender.await_count == 1
    kwargs = sender.await_args.kwargs
    assert isinstance(kwargs["embed"], discord.Embed)
    assert kwargs["content"] is None  # warning не пингует


def test_error_pings_configured_user():
    sender = _run_handler(_record(logging.ERROR), ping_user_id=42)
    kwargs = sender.await_args.kwargs
    assert kwargs["content"] == "<@42>"
    mentioned = kwargs["allowed_mentions"].users
    assert [u.id for u in mentioned] == [42]


def test_warning_does_not_ping_even_with_user():
    sender = _run_handler(_record(logging.WARNING), ping_user_id=42)
    assert sender.await_args.kwargs["content"] is None


def test_send_failure_does_not_propagate():
    # падение отправки не должно валить воркера или ронять логирование
    async def go():
        sender = AsyncMock(side_effect=RuntimeError("discord down"))
        handler = DiscordLogHandler(
            sender=sender, loop=asyncio.get_running_loop(), level=logging.DEBUG
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        # глушим handleError, чтобы тест не сыпал в stderr
        handler.handleError = lambda record: None
        handler.start()
        handler.emit(_record(logging.ERROR))
        await asyncio.sleep(0)
        await asyncio.wait_for(handler.queue.join(), timeout=1)
        # воркер жив и готов принять следующую запись
        assert handler._task is not None and not handler._task.done()
        await handler.aclose()

    asyncio.run(go())
