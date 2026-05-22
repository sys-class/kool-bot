import asyncio
import json
import re
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

UWUIFIED_FILE = Path("uwuified.json")

PROTECTED_USERS = {1130462413087592528}

_URL_PATTERN = re.compile(r"https?://\S+")

WORD_MAP = {
    "you": "wu",
    "cute": "kawaii",
    "cat": "kitty",
    "kiss": "mwah",
    "good": "guwd",
    "no": "nuu",
    "ты": "ти",
    "маленький": "мавенки",
}

LETTER_MAP = {
    "р": "в",
    "л": "в",
    "Р": "В",
    "Л": "В",
    "r": "w",
    "l": "w",
    "R": "W",
    "L": "W",
}

_WORD_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in WORD_MAP) + r")\b",
    re.IGNORECASE,
)


def _word_replacer(match: re.Match) -> str:
    word = match.group(0)
    key = word.lower()
    replacement = WORD_MAP.get(key, word)
    if word[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


_LETTER_TRANSLATION = str.maketrans(LETTER_MAP)


def felinid_accent(text: str) -> str:
    """Apply felinid accent transformations to text."""
    parts = _URL_PATTERN.split(text)
    urls = _URL_PATTERN.findall(text)
    result = []
    for i, part in enumerate(parts):
        part = _WORD_PATTERN.sub(_word_replacer, part)
        part = part.translate(_LETTER_TRANSLATION)
        result.append(part)
        if i < len(urls):
            result.append(urls[i])
    return "".join(result)


class UwuifyCog(commands.Cog):
    _EMPTY: frozenset[int] = frozenset()

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.uwuified: dict[str, set[int]] = {}
        self._load()

    def _load(self):
        if UWUIFIED_FILE.exists():
            with open(UWUIFIED_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.uwuified = {k: set(v) for k, v in raw.items()}

    def _save(self):
        serializable = {k: list(v) for k, v in self.uwuified.items()}
        with open(UWUIFIED_FILE, "w", encoding="utf-8") as f:
            json.dump(serializable, f, separators=(",", ":"))

    def is_uwuified(self, guild_id: int, user_id: int) -> bool:
        return user_id in self.uwuified.get(str(guild_id), self._EMPTY)

    @app_commands.command(name="uwuify", description="Накладывает/снимает феленидский акцент с пользователя")
    @app_commands.describe(member="Пользователь для uwuify")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def uwuify_cmd(self, interaction: discord.Interaction, member: discord.Member):
        if member.id in PROTECTED_USERS:
            await interaction.response.send_message("Этого пользователя нельзя uwuify.", ephemeral=True)
            return

        guild_key = str(interaction.guild_id)
        users = self.uwuified.setdefault(guild_key, set())

        if member.id in users:
            users.discard(member.id)
            self._save()
            await interaction.response.send_message(f"Феленидский акцент снят с {member.mention}")
        else:
            users.add(member.id)
            self._save()
            await interaction.response.send_message(f"Феленидский акцент наложен на {member.mention}")

    @uwuify_cmd.error
    async def uwuify_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "У вас недостаточно прав для использования этой команды.",
                ephemeral=True
            )
        elif isinstance(error, app_commands.NoPrivateMessage):
            await interaction.response.send_message(
                "Эта команда работает только на сервере.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Произошла ошибка при выполнении команды.",
                ephemeral=True
            )
            print(f"Uwuify error: {error}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if message.content.startswith("$"):
            return
        if not self.is_uwuified(message.guild.id, message.author.id):
            return

        try:
            await message.delete()
        except discord.Forbidden:
            return

        content = felinid_accent(message.content)[:2000] if message.content else None

        files: list[discord.File] = []
        if message.attachments:
            results = await asyncio.gather(
                *(a.to_file() for a in message.attachments),
                return_exceptions=True,
            )
            for r in results:
                if isinstance(r, discord.File):
                    files.append(r)
                else:
                    print(f"Uwuify attachment error: {r}")

        if not content and not files:
            return

        try:
            await self.bot.webhook_service._send(
                message.channel,
                "uwuify",
                content=content,
                username=message.author.display_name[:80],
                avatar_url=message.author.display_avatar.url,
                files=files if files else discord.utils.MISSING,
            )
        except Exception as e:
            print(f"Uwuify webhook error: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(UwuifyCog(bot))
