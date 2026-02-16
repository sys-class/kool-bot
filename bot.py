import discord
from discord import app_commands
from discord.ext import commands

from config import TOKEN, SOURCE_CHANNEL_1, SOURCE_CHANNEL_2, TARGET_VOICE_CHANNELS, ALLOWED_USERS
from services.cooldown import CooldownManager
from services.webhook import WebhookService


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

        @self.before_invoke
        async def global_cooldown(ctx):
            if ctx.author.id in ALLOWED_USERS:
                return
            if not self.command_cooldown.check_cooldown(ctx.author.id):
                raise commands.CommandOnCooldown(
                    commands.Cooldown(1, self.command_cooldown.cooldown_time),
                    self.command_cooldown.cooldown_time,
                    commands.BucketType.user
                )

        async def global_slash_cooldown(interaction: discord.Interaction) -> bool:
            if interaction.user.id in ALLOWED_USERS:
                return True
            if not self.command_cooldown.check_cooldown(interaction.user.id):
                await interaction.response.send_message(
                    f"Подожди {self.command_cooldown.cooldown_time} сек. перед следующей командой.",
                    ephemeral=True
                )
                return False
            return True

        self.tree.interaction_check = global_slash_cooldown

    async def on_ready(self):
        print(f"Login: {self.user.name}")
        print(f"{self.user.name}: Mrrp~\nMeow! ^w^")

        await self.change_presence(
            status=discord.Status.idle,
            activity=discord.Game("Mrrp~")
        )

        print(f"Загружено целевых войс-каналов для {len(TARGET_VOICE_CHANNELS)} серверов:")
        for guild_id, channels in TARGET_VOICE_CHANNELS.items():
            guild = self.get_guild(guild_id)
            guild_name = guild.name if guild else f"Unknown Guild ({guild_id})"
            print(f"  {guild_name}: {len(channels)} каналов")

        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Sync error: {e}")

    async def on_message(self, message):
        if message.author.bot:
            return

        if "ерп" in message.content.lower():
            try:
                await message.channel.send(f"**Ну давай~ {message.author.mention} **")
            except Exception as e:
                print(f"Trigger error: {e}")

        channel_map = {
            SOURCE_CHANNEL_1: SOURCE_CHANNEL_2,
            SOURCE_CHANNEL_2: SOURCE_CHANNEL_1
        }

        if message.channel.id in channel_map:
            target_channel = self.get_channel(channel_map[message.channel.id])
            if not target_channel:
                try:
                    target_channel = await self.fetch_channel(channel_map[message.channel.id])
                except Exception:
                    target_channel = None
            if target_channel:
                await self.webhook_service.send_webhook_message(target_channel, message)

        await self.process_commands(message)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"Подожди {error.retry_after:.1f} сек. перед следующей командой.",
                delete_after=3
            )
            return
        await super().on_command_error(ctx, error)

    async def on_disconnect(self):
        print("Бот отключен")


bot = CoolBot()
bot.run(TOKEN)
