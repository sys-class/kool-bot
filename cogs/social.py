import datetime
import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from services import embeds

MOOD_FILE = Path("mood.json")
MAX_MOOD_LEN = 40


def _load() -> dict[str, dict[str, str]]:
    if not MOOD_FILE.exists():
        return {}
    with open(MOOD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict[str, dict[str, str]]) -> None:
    with open(MOOD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def _relative(ts: datetime.datetime) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=datetime.timezone.utc)
    delta = now - ts
    days = delta.days
    if days < 1:
        hours = delta.seconds // 3600
        if hours < 1:
            return "только что"
        return f"{hours} ч назад"
    if days < 30:
        return f"{days} д назад"
    if days < 365:
        return f"{days // 30} мес назад"
    years = days // 365
    return f"{years} г назад"


def _fmt_date(ts: datetime.datetime) -> str:
    return ts.strftime("%d.%m.%Y")


class SocialCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.moods: dict[str, dict[str, str]] = _load()

    def get_mood(self, guild_id: int, user_id: int) -> str | None:
        return self.moods.get(str(guild_id), {}).get(str(user_id))

    @app_commands.command(name="mood", description="Установить настроение (пусто — сбросить)")
    @app_commands.describe(text="одно-два слова · оставь пустым чтобы сбросить")
    @app_commands.guild_only()
    async def mood(self, interaction: discord.Interaction, text: str = ""):
        guild_key = str(interaction.guild_id)
        user_key = str(interaction.user.id)
        text = text.strip().lower()

        if not text:
            if guild_key in self.moods and user_key in self.moods[guild_key]:
                del self.moods[guild_key][user_key]
                if not self.moods[guild_key]:
                    del self.moods[guild_key]
                _save(self.moods)
            await interaction.response.send_message(
                embed=embeds.ok(description="настроение сброшено", user=interaction.user),
                ephemeral=True,
            )
            return

        if len(text) > MAX_MOOD_LEN:
            await interaction.response.send_message(
                embed=embeds.err(f"максимум {MAX_MOOD_LEN} символов", user=interaction.user),
                ephemeral=True,
            )
            return

        self.moods.setdefault(guild_key, {})[user_key] = text
        _save(self.moods)
        await interaction.response.send_message(
            embed=embeds.ok(description=f"настроение · **{text}**", user=interaction.user),
            ephemeral=True,
        )

    @app_commands.command(name="whois", description="Карточка пользователя")
    @app_commands.describe(member="пользователь · по умолчанию ты")
    @app_commands.guild_only()
    async def whois(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        lines = [
            f"`создан    ` {_fmt_date(member.created_at)} · {_relative(member.created_at)}",
        ]
        if member.joined_at:
            lines.append(f"`вошёл     ` {_fmt_date(member.joined_at)} · {_relative(member.joined_at)}")

        top = member.top_role
        if top and top.name != "@everyone":
            lines.append(f"`роль      ` {top.mention}")

        mood = self.get_mood(interaction.guild_id, member.id)
        if mood:
            lines.append(f"`настроение` {mood}")

        lines.append(f"`id        ` `{member.id}`")

        embed = embeds.info(
            title=member.display_name,
            description="\n".join(lines),
            user=interaction.user,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SocialCog(bot))
