"""подгружаем все коги в чистый Bot и проверяем регистрацию команд."""

import asyncio

import discord
import pytest
from discord.ext import commands

from services.cooldown import CooldownManager
from services.webhook import WebhookService

COGS = [
    "cogs.moderation",
    "cogs.utility",
    "cogs.anonymous",
    "cogs.voice",
    "cogs.fun",
    "cogs.uwuify",
    "cogs.social",
    "cogs.reminders",
    "cogs.stats",
]


def _make_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)
    bot.channel_creators = {}
    bot.bot_created_channels = set()
    bot.webhook_service = WebhookService()
    bot.command_cooldown = CooldownManager()
    return bot


async def _load_all(bot: commands.Bot):
    for ext in COGS:
        await bot.load_extension(ext)


async def _unload_all(bot: commands.Bot):
    for ext in list(bot.extensions):
        await bot.unload_extension(ext)


async def _ready_noop(self=None):
    return None


@pytest.fixture
def bot(monkeypatch):
    monkeypatch.setattr(discord.Client, "wait_until_ready", _ready_noop)
    b = _make_bot()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_load_all(b))
        yield b
        loop.run_until_complete(_unload_all(b))
        pending = asyncio.all_tasks(loop)
        for t in pending:
            t.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def test_all_cogs_loaded(bot):
    assert len(bot.cogs) == len(COGS)


def test_slash_commands_have_descriptions(bot):
    missing = [
        cmd.qualified_name for cmd in bot.tree.walk_commands() if not cmd.description
    ]
    assert not missing, f"команды без описания: {missing}"


def test_slash_command_names_unique(bot):
    names = [cmd.qualified_name for cmd in bot.tree.walk_commands()]
    dupes = {n for n in names if names.count(n) > 1}
    assert not dupes, f"дубликаты: {dupes}"


def test_at_least_one_command_registered(bot):
    assert any(bot.tree.walk_commands())
