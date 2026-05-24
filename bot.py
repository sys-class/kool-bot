import logging
import math
import re

import discord
from discord.ext import commands

from config import (
    TOKEN,
    SOURCE_CHANNEL_1,
    SOURCE_CHANNEL_2,
    TARGET_VOICE_CHANNELS,
    ALLOWED_USERS,
)
from services import embeds
from services.cooldown import CooldownManager
from services.webhook import WebhookService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

_FORWARD_MAP = {
    SOURCE_CHANNEL_1: SOURCE_CHANNEL_2,
    SOURCE_CHANNEL_2: SOURCE_CHANNEL_1,
}

# whole-word match, кириллические границы
_ERP_RE = re.compile(r"(?:(?<=^)|(?<=[^\w]))ерп(?=$|[^\w])", re.IGNORECASE)


class CoolBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="$", intents=intents, help_command=None)

        self.channel_creators = {}
        self.bot_created_channels = set()
        self.webhook_service = WebhookService()
        self.command_cooldown = CooldownManager()

    async def setup_hook(self):
        await self.load_extension("cogs.moderation")
        await self.load_extension("cogs.utility")
        await self.load_extension("cogs.anonymous")
        await self.load_extension("cogs.voice")
        await self.load_extension("cogs.fun")
        await self.load_extension("cogs.uwuify")
        await self.load_extension("cogs.social")
        await self.load_extension("cogs.reminders")
        await self.load_extension("cogs.stats")

        async def global_slash_cooldown(interaction: discord.Interaction) -> bool:
            if interaction.user.id in ALLOWED_USERS:
                return True
            if not self.command_cooldown.check_cooldown(interaction.user.id):
                left = math.ceil(self.command_cooldown.remaining(interaction.user.id))
                await interaction.response.send_message(
                    embed=embeds.err(
                        f"подожди **{left} сек**",
                        title="кулдаун",
                        user=interaction.user,
                    ),
                    ephemeral=True,
                )
                return False
            return True

        self.tree.interaction_check = global_slash_cooldown

    async def on_ready(self):
        log.info("Login: %s", self.user.name)
        log.info("%s: Mrrp~ Meow! ^w^", self.user.name)
        log.info("готов к работе")

        await self.change_presence(
            status=discord.Status.idle, activity=discord.Game("Mrrp~")
        )

        log.info(
            "Загружено целевых войс-каналов для %d серверов:",
            len(TARGET_VOICE_CHANNELS),
        )
        for guild_id, channels in TARGET_VOICE_CHANNELS.items():
            guild = self.get_guild(guild_id)
            guild_name = guild.name if guild else f"Unknown Guild ({guild_id})"
            log.info("  %s: %d каналов", guild_name, len(channels))

        try:
            synced = await self.tree.sync()
            log.info("Synced %d command(s)", len(synced))
        except Exception:
            log.exception("Sync error")

    async def on_message(self, message):
        if message.author.bot:
            return

        if _ERP_RE.search(message.content):
            try:
                await message.channel.send(f"**Ну давай~ {message.author.mention} **")
            except Exception:
                log.exception("Trigger error")

        target_id = _FORWARD_MAP.get(message.channel.id)
        if target_id is not None:
            target_channel = self.get_channel(target_id)
            if not target_channel:
                try:
                    target_channel = await self.fetch_channel(target_id)
                except Exception:
                    target_channel = None
            if target_channel:
                await self.webhook_service.send_webhook_message(target_channel, message)

        if message.content.startswith("$"):
            await message.channel.send(
                "Бот перешёл на слэш-команды. Используй `/` вместо `$`.", delete_after=5
            )

    async def on_disconnect(self):
        log.info("Бот отключен")


bot = CoolBot()
bot.run(TOKEN)
