import json
import re
import time
import uuid
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands, tasks

from services import embeds

REMINDERS_FILE = Path("reminders.json")
MAX_TEXT = 500
MAX_PER_USER = 25
MIN_SECONDS = 10
MAX_SECONDS = 60 * 60 * 24 * 30  # 30 дней

_DURATION_TOKEN = re.compile(r"(\d+)\s*([smhdwу]|сек|мин|ч|д|нед)", re.IGNORECASE)
_UNIT_SECONDS = {
    "s": 1, "сек": 1,
    "m": 60, "мин": 60,
    "h": 3600, "ч": 3600,
    "d": 86400, "д": 86400,
    "w": 604800, "нед": 604800,
    "у": 1,  # ignore stray
}


def _parse_duration(text: str) -> int | None:
    total = 0
    matched = 0
    for m in _DURATION_TOKEN.finditer(text):
        unit = m.group(2).lower()
        secs = _UNIT_SECONDS.get(unit)
        if not secs:
            continue
        total += int(m.group(1)) * secs
        matched += 1
    if matched == 0 or total <= 0:
        return None
    return total


def _fmt_remaining(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} сек"
    if seconds < 3600:
        return f"{seconds // 60} мин"
    if seconds < 86400:
        h, m = divmod(seconds, 3600)
        m //= 60
        return f"{h} ч {m} мин" if m else f"{h} ч"
    d, rem = divmod(seconds, 86400)
    h = rem // 3600
    return f"{d} д {h} ч" if h else f"{d} д"


class RemindersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminders: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if not REMINDERS_FILE.exists():
            return []
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self) -> None:
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.reminders, f, ensure_ascii=False, separators=(",", ":"))

    async def cog_load(self):
        self.tick.start()

    async def cog_unload(self):
        self.tick.cancel()

    @tasks.loop(seconds=15)
    async def tick(self):
        now = time.time()
        due = [r for r in self.reminders if r["due"] <= now]
        if not due:
            return
        for r in due:
            await self._deliver(r)
        self.reminders = [r for r in self.reminders if r["due"] > now]
        self._save()

    @tick.before_loop
    async def _before_tick(self):
        await self.bot.wait_until_ready()

    async def _deliver(self, r: dict):
        embed = embeds.info(
            title="напоминание",
            description=r["text"],
        )
        embed.set_footer(text="remind")
        user = self.bot.get_user(r["user_id"])
        try:
            channel = self.bot.get_channel(r["channel_id"]) or await self.bot.fetch_channel(r["channel_id"])
        except Exception:
            channel = None
        content = f"<@{r['user_id']}>"
        if channel is not None:
            try:
                await channel.send(content=content, embed=embed)
                return
            except Exception as e:
                print(f"Remind deliver error: {e}")
        if user is not None:
            try:
                await user.send(embed=embed)
            except Exception as e:
                print(f"Remind DM fallback error: {e}")

    @app_commands.command(name="remind", description="Напомнить через время")
    @app_commands.describe(when="через · `30m` `2h` `1d` `1h30m`", text="текст напоминания")
    async def remind(self, interaction: discord.Interaction, when: str, text: str):
        seconds = _parse_duration(when)
        if seconds is None:
            await interaction.response.send_message(
                embed=embeds.err("формат · `30m` `2h` `1d` `1h30m`", user=interaction.user),
                ephemeral=True,
            )
            return
        if seconds < MIN_SECONDS or seconds > MAX_SECONDS:
            await interaction.response.send_message(
                embed=embeds.err(f"границы · от 10 сек до 30 дней", user=interaction.user),
                ephemeral=True,
            )
            return
        if len(text) > MAX_TEXT:
            await interaction.response.send_message(
                embed=embeds.err(f"текст · максимум {MAX_TEXT} символов", user=interaction.user),
                ephemeral=True,
            )
            return

        user_count = sum(1 for r in self.reminders if r["user_id"] == interaction.user.id)
        if user_count >= MAX_PER_USER:
            await interaction.response.send_message(
                embed=embeds.err(f"лимит · {MAX_PER_USER} напоминаний", user=interaction.user),
                ephemeral=True,
            )
            return

        self.reminders.append({
            "id": uuid.uuid4().hex[:8],
            "user_id": interaction.user.id,
            "channel_id": interaction.channel_id,
            "due": time.time() + seconds,
            "text": text,
        })
        self._save()

        await interaction.response.send_message(
            embed=embeds.ok(
                title="напоминание",
                description=f"через · **{_fmt_remaining(seconds)}**\n> {text}",
                user=interaction.user,
            ),
            ephemeral=True,
        )

    @app_commands.command(name="reminders", description="Список твоих напоминаний")
    async def list_reminders(self, interaction: discord.Interaction):
        mine = sorted(
            (r for r in self.reminders if r["user_id"] == interaction.user.id),
            key=lambda r: r["due"],
        )
        if not mine:
            await interaction.response.send_message(
                embed=embeds.info(description="пусто", user=interaction.user),
                ephemeral=True,
            )
            return
        now = time.time()
        lines = [
            f"`{r['id']}` · через {_fmt_remaining(int(r['due'] - now))} · {r['text'][:60]}"
            for r in mine
        ]
        await interaction.response.send_message(
            embed=embeds.info(title="напоминания", description="\n".join(lines), user=interaction.user),
            ephemeral=True,
        )

    @app_commands.command(name="forget", description="Удалить напоминание по id")
    @app_commands.describe(reminder_id="id из /reminders")
    async def forget(self, interaction: discord.Interaction, reminder_id: str):
        before = len(self.reminders)
        self.reminders = [
            r for r in self.reminders
            if not (r["id"] == reminder_id and r["user_id"] == interaction.user.id)
        ]
        if len(self.reminders) == before:
            await interaction.response.send_message(
                embed=embeds.err("не найдено", user=interaction.user),
                ephemeral=True,
            )
            return
        self._save()
        await interaction.response.send_message(
            embed=embeds.ok(description=f"удалено · `{reminder_id}`", user=interaction.user),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(RemindersCog(bot))
