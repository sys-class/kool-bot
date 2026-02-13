import json
import re
from pathlib import Path

import discord
from discord.ext import commands

UWUIFIED_FILE = Path("uwuified.json")

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


_LETTER_PATTERN = re.compile("[" + re.escape("".join(LETTER_MAP.keys())) + "]")


def felinid_accent(text: str) -> str:
    """Apply felinid accent transformations to text."""
    text = _WORD_PATTERN.sub(_word_replacer, text)
    text = _LETTER_PATTERN.sub(lambda m: LETTER_MAP[m.group(0)], text)
    return text


class UwuifyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.uwuified: dict[str, list[int]] = {}
        self._load()

    def _load(self):
        if UWUIFIED_FILE.exists():
            with open(UWUIFIED_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.uwuified = {k: list(v) for k, v in raw.items()}

    def _save(self):
        with open(UWUIFIED_FILE, "w", encoding="utf-8") as f:
            json.dump(self.uwuified, f)

    def is_uwuified(self, guild_id: int, user_id: int) -> bool:
        return user_id in self.uwuified.get(str(guild_id), [])

    @commands.command(name="uwuify")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def uwuify_cmd(self, ctx: commands.Context, member: discord.Member):
        guild_key = str(ctx.guild.id)
        users = self.uwuified.setdefault(guild_key, [])

        if member.id in users:
            users.remove(member.id)
            self._save()
            await ctx.send(f"Феленидский акцент снят с {member.mention}")
        else:
            users.append(member.id)
            self._save()
            await ctx.send(f"Феленидский акцент наложен на {member.mention}")

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

        webhook = await self.bot.webhook_service.get_or_create_webhook(
            message.channel, "uwuify"
        )

        content = felinid_accent(message.content)[:2000] if message.content else None

        files = []
        for attachment in message.attachments:
            try:
                files.append(await attachment.to_file())
            except Exception as e:
                print(f"Uwuify attachment error: {e}")

        if not content and not files:
            return

        try:
            await webhook.send(
                content=content,
                username=message.author.display_name[:80],
                avatar_url=message.author.avatar.url if message.author.avatar else None,
                files=files if files else discord.utils.MISSING,
            )
        except discord.NotFound:
            self.bot.webhook_service.invalidate(message.channel.id, "uwuify")
            webhook = await self.bot.webhook_service.get_or_create_webhook(
                message.channel, "uwuify"
            )
            await webhook.send(
                content=content,
                username=message.author.display_name[:80],
                avatar_url=message.author.avatar.url if message.author.avatar else None,
                files=files if files else discord.utils.MISSING,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(UwuifyCog(bot))
