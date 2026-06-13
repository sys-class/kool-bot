import asyncio
import logging
import math
import re

import discord
from discord.ext import commands, tasks

from config import (
    TOKEN,
    GUILD_ID,
    DATA_DIR,
    LOG_LEVEL,
    LOG_CHANNEL_ID,
    DISCORD_LOG_LEVEL,
    LOG_PING_USER_ID,
    SOURCE_CHANNEL_1,
    SOURCE_CHANNEL_2,
    TARGET_VOICE_CHANNELS,
    ALLOWED_USERS,
)
from services import embeds
from services.cooldown import CooldownManager
from services.discord_log import DiscordLogHandler
from services.health import write_heartbeat
from services.logger import resolve_level, setup_logging
from services.storage import read_json, write_json, write_json_sync
from services.webhook import WebhookService

GUILD = discord.Object(id=GUILD_ID)
TARGETS_FILE = DATA_DIR / "targets.json"
CHANNELS_FILE = DATA_DIR / "channels.json"

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
        super().__init__(
            command_prefix="$",
            intents=intents,
            help_command=None,
            # глобальный дефолт: чужой текст (вебхуки, /say) не должен пинговать сервер
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=True
            ),
        )

        self.channel_creators: dict[int, int] = {}
        self.bot_created_channels: set[int] = set()
        self.webhook_service = WebhookService()
        self.command_cooldown = CooldownManager()
        self._discord_log_handler: DiscordLogHandler | None = None

        self._load_targets()
        self._load_channels()

    @tasks.loop(seconds=30)
    async def _heartbeat(self) -> None:
        # пишем отметку живости, только пока соединение реально открыто —
        # её читает HEALTHCHECK образа (см. services/health.py).
        # is_closed() остаётся False во время авто-реконнекта гейтвея, так
        # что одного его мало: дополнительно требуем is_ready() и конечный
        # latency (во время обрыва он становится nan/inf), иначе отвалившийся
        # бот продолжал бы отчитываться как healthy
        if self.is_closed() or not self.is_ready():
            return
        if not math.isfinite(self.latency):
            return
        try:
            write_heartbeat()
        except Exception:
            log.exception("heartbeat write failed")

    def _load_targets(self) -> None:
        seed = {str(gid): list(cids) for gid, cids in TARGET_VOICE_CHANNELS.items()}
        data = read_json(TARGETS_FILE, seed)
        TARGET_VOICE_CHANNELS.clear()
        for gid_str, cids in data.items():
            TARGET_VOICE_CHANNELS[int(gid_str)] = list(cids)
        if not TARGETS_FILE.exists():
            write_json_sync(TARGETS_FILE, data)

    async def save_targets(self) -> None:
        data = {str(gid): list(cids) for gid, cids in TARGET_VOICE_CHANNELS.items()}
        await write_json(TARGETS_FILE, data)

    def _load_channels(self) -> None:
        data = read_json(CHANNELS_FILE, {})
        for cid_str, creator_id in data.items():
            cid = int(cid_str)
            self.bot_created_channels.add(cid)
            self.channel_creators[cid] = int(creator_id)

    async def save_channels(self) -> None:
        data = {
            str(cid): self.channel_creators.get(cid, 0)
            for cid in self.bot_created_channels
        }
        await write_json(CHANNELS_FILE, data)

    async def _setup_discord_logging(self) -> None:
        # заводим (или переиспользуем) вебхук в лог-канале и вешаем хендлер на
        # корневой логгер. вебхук бот достаёт сам, чтобы url не жил в окружении.
        # сбой настройки не должен мешать запуску бота — логи всё равно в консоли
        if not LOG_CHANNEL_ID:
            return
        try:
            channel = self.get_channel(LOG_CHANNEL_ID) or await self.fetch_channel(
                LOG_CHANNEL_ID
            )
            webhook = await self.webhook_service.get_or_create_webhook(
                channel, "kool-bot logs"
            )
        except Exception:
            log.exception("Discord log setup failed")
            return

        handler = DiscordLogHandler(
            sender=lambda **kw: webhook.send(wait=False, **kw),
            loop=asyncio.get_running_loop(),
            ping_user_id=LOG_PING_USER_ID,
            level=resolve_level(DISCORD_LOG_LEVEL, default=logging.WARNING),
        )
        handler.start()
        logging.getLogger().addHandler(handler)
        self._discord_log_handler = handler
        log.info("Discord-логи включены в канале %d", LOG_CHANNEL_ID)

    async def setup_hook(self):
        await self._setup_discord_logging()
        await self.load_extension("cogs.moderation")
        await self.load_extension("cogs.utility")
        await self.load_extension("cogs.anonymous")
        await self.load_extension("cogs.voice")
        await self.load_extension("cogs.fun")
        await self.load_extension("cogs.uwuify")
        await self.load_extension("cogs.social")
        await self.load_extension("cogs.reminders")
        await self.load_extension("cogs.stats")
        await self.load_extension("cogs.dev")

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

        if not self._heartbeat.is_running():
            self._heartbeat.start()

    async def on_ready(self):
        write_heartbeat()
        log.info("Login: %s", self.user.name)
        log.info("%s: Mrrp~ Meow! ^w^", self.user.name)
        log.info("готов к работе")

        await self.change_presence(
            status=discord.Status.online, activity=discord.Game("Mrrp~")
        )

        log.info(
            "Загружено целевых войс-каналов для %d серверов:",
            len(TARGET_VOICE_CHANNELS),
        )
        for guild_id, channels in TARGET_VOICE_CHANNELS.items():
            guild = self.get_guild(guild_id)
            guild_name = guild.name if guild else f"Unknown Guild ({guild_id})"
            log.info("  %s: %d каналов", guild_name, len(channels))

        try:  # pragma: no cover
            self.tree.copy_global_to(guild=GUILD)
            self.tree.clear_commands(guild=None)
            await self.tree.sync()
            synced = await self.tree.sync(guild=GUILD)
            log.info("Synced %d command(s) to guild %d", len(synced), GUILD_ID)
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


def main() -> None:
    setup_logging(LOG_LEVEL)
    if not TOKEN:
        raise SystemExit("TOKEN не задан: создай .env по образцу .env.example")
    bot = CoolBot()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
