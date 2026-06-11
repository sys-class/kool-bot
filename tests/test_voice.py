import asyncio
from types import SimpleNamespace

import discord

from cogs.voice import VoiceCog


class FakeChannel:
    def __init__(self, error=None):
        self.id = 123
        self.name = "/home/test"
        self.members = []
        self.error = error
        self.deleted = False

    async def delete(self, reason=None):
        if self.error:
            raise self.error
        self.deleted = True


def _make_cog(channel):
    cog = VoiceCog.__new__(VoiceCog)

    async def save_channels():
        pass

    cog.bot = SimpleNamespace(
        bot_created_channels={channel.id},
        channel_creators={channel.id: 1},
        get_channel=lambda cid: channel,
        save_channels=save_channels,
    )
    return cog


def _run_cleanup(cog, channel):
    asyncio.run(cog.check_and_cleanup_channel(channel))


def test_cleanup_removes_tracking_on_success():
    channel = FakeChannel()
    cog = _make_cog(channel)
    _run_cleanup(cog, channel)
    assert channel.deleted
    assert channel.id not in cog.bot.bot_created_channels
    assert channel.id not in cog.bot.channel_creators


def test_cleanup_removes_tracking_on_not_found():
    response = SimpleNamespace(status=404, reason="Not Found")
    channel = FakeChannel(error=discord.errors.NotFound(response, "gone"))
    cog = _make_cog(channel)
    _run_cleanup(cog, channel)
    assert channel.id not in cog.bot.bot_created_channels
    assert channel.id not in cog.bot.channel_creators


def test_cleanup_keeps_tracking_on_delete_error():
    channel = FakeChannel(error=RuntimeError("api down"))
    cog = _make_cog(channel)
    _run_cleanup(cog, channel)
    assert channel.id in cog.bot.bot_created_channels
    assert channel.id in cog.bot.channel_creators


def test_cleanup_skips_channel_with_members():
    channel = FakeChannel()
    channel.members = [object()]
    cog = _make_cog(channel)
    _run_cleanup(cog, channel)
    assert not channel.deleted
    assert channel.id in cog.bot.bot_created_channels
