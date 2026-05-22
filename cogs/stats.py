import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands, tasks

from services import embeds

STATS_FILE = Path("stats.json")
RETENTION_HOURS = 24 * 7
SPARK_CHARS = "▁▂▃▄▅▆▇█"


def _hour_key(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H")


def _now_hour() -> datetime:
    return datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)


def _sparkline(values: list[int]) -> str:
    if not values:
        return ""
    peak = max(values)
    if peak == 0:
        return SPARK_CHARS[0] * len(values)
    step = peak / (len(SPARK_CHARS) - 1)
    return "".join(SPARK_CHARS[min(len(SPARK_CHARS) - 1, int(v / step))] if step else SPARK_CHARS[0] for v in values)


class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # data["guilds"][guild_id]["hours"][hour_key] = total
        # data["guilds"][guild_id]["channels"][hour_key][channel_id] = count
        self.data: dict = self._load()
        self.dirty = False

    def _load(self) -> dict:
        if not STATS_FILE.exists():
            return {"guilds": {}}
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self) -> None:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, separators=(",", ":"))

    async def cog_load(self):
        self.flush.start()

    async def cog_unload(self):
        self.flush.cancel()
        if self.dirty:
            self._save()

    @tasks.loop(seconds=60)
    async def flush(self):
        self._prune()
        if self.dirty:
            self._save()
            self.dirty = False

    @flush.before_loop
    async def _before_flush(self):
        await self.bot.wait_until_ready()

    def _prune(self):
        cutoff = _now_hour() - timedelta(hours=RETENTION_HOURS)
        cutoff_key = _hour_key(cutoff)
        for guild in self.data.get("guilds", {}).values():
            for bucket in ("hours", "channels"):
                old = [k for k in guild.get(bucket, {}) if k < cutoff_key]
                for k in old:
                    del guild[bucket][k]
                    self.dirty = True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        gid = str(message.guild.id)
        cid = str(message.channel.id)
        hour = _hour_key(_now_hour())

        guild = self.data.setdefault("guilds", {}).setdefault(gid, {"hours": {}, "channels": {}})
        guild["hours"][hour] = guild["hours"].get(hour, 0) + 1
        guild["channels"].setdefault(hour, {})
        guild["channels"][hour][cid] = guild["channels"][hour].get(cid, 0) + 1
        self.dirty = True

    @app_commands.command(name="stats", description="Пульс сервера за последние сутки и неделю")
    @app_commands.guild_only()
    async def stats(self, interaction: discord.Interaction):
        guild = self.data.get("guilds", {}).get(str(interaction.guild_id))
        if not guild or not guild.get("hours"):
            await interaction.response.send_message(
                embed=embeds.info(description="данных пока нет · подожди", user=interaction.user),
                ephemeral=True,
            )
            return

        now = _now_hour()
        hours_24 = [
            guild["hours"].get(_hour_key(now - timedelta(hours=i)), 0)
            for i in range(23, -1, -1)
        ]
        total_24 = sum(hours_24)

        hours_7d = [
            guild["hours"].get(_hour_key(now - timedelta(hours=i)), 0)
            for i in range(RETENTION_HOURS)
        ]
        total_7d = sum(hours_7d)

        peak_idx = max(range(24), key=lambda i: hours_24[i])
        peak_hour = (now - timedelta(hours=23 - peak_idx)).hour

        channel_totals: dict[str, int] = defaultdict(int)
        cutoff_24 = _hour_key(now - timedelta(hours=23))
        for hkey, channels in guild.get("channels", {}).items():
            if hkey < cutoff_24:
                continue
            for cid, count in channels.items():
                channel_totals[cid] += count
        top_channels = sorted(channel_totals.items(), key=lambda x: -x[1])[:3]

        top_lines = []
        for cid, count in top_channels:
            ch = interaction.guild.get_channel(int(cid))
            mention = ch.mention if ch else f"`{cid}`"
            top_lines.append(f"{mention} · **{count}**")

        spark = _sparkline(hours_24)
        desc = (
            f"`{spark}`\n"
            f"`24ч       ` **{total_24}**\n"
            f"`7д        ` **{total_7d}**\n"
            f"`пик       ` {peak_hour:02d}:00 utc\n"
        )
        if top_lines:
            desc += "\n`топ каналы`\n" + "\n".join(top_lines)

        await interaction.response.send_message(
            embed=embeds.info(title="пульс сервера", description=desc, user=interaction.user)
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
