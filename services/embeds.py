from __future__ import annotations

import discord

ACCENT = 0x7A6680
ERROR = 0x7A3A4A
MUTED = 0x3A3340

BAR_FILLED = "▰"
BAR_EMPTY = "▱"
SEP = " · "


def _stamp(embed: discord.Embed, user: discord.abc.User | None) -> discord.Embed:
    if user is not None:
        embed.set_footer(
            text=user.display_name.lower(),
            icon_url=user.display_avatar.url,
        )
    return embed


def _build(color: int, title: str | None, description: str | None, user) -> discord.Embed:
    embed = discord.Embed(color=color)
    if title is not None:
        embed.title = title.lower()
    if description is not None:
        embed.description = description
    return _stamp(embed, user)


def ok(title: str | None = None, description: str | None = None, *, user=None) -> discord.Embed:
    return _build(ACCENT, title, description, user)


def err(description: str, *, title: str = "ошибка", user=None) -> discord.Embed:
    return _build(ERROR, title, description, user)


def info(title: str | None = None, description: str | None = None, *, user=None) -> discord.Embed:
    return _build(ACCENT, title, description, user)


def fun(title: str | None = None, description: str | None = None, *, user=None) -> discord.Embed:
    return _build(ACCENT, title, description, user)


def mod(title: str | None = None, description: str | None = None, *, user=None) -> discord.Embed:
    return _build(ACCENT, title, description, user)


def voice(title: str | None = None, description: str | None = None, *, user=None) -> discord.Embed:
    return _build(ACCENT, title, description, user)


def bar(rate: int, width: int = 10) -> str:
    filled = round(rate / 100 * width)
    return BAR_FILLED * filled + BAR_EMPTY * (width - filled)
