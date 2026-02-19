import discord
from discord import app_commands
from discord.ext import commands

from config import ANON_TARGET_CHANNEL_ID


class AnonymousCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="anonsay", description="Анонимно отправляет сообщение в канал")
    @app_commands.describe(message="Текст сообщения")
    async def anonsay(self, interaction: discord.Interaction, message: str):
        if interaction.guild is not None:
            await interaction.response.send_message("Только в лс", ephemeral=True)
            return

        channel = self.bot.get_channel(ANON_TARGET_CHANNEL_ID)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(ANON_TARGET_CHANNEL_ID)
            except Exception:
                channel = None

        if not channel:
            await interaction.response.send_message("Не удалось найти канал для отправки сообщения.", ephemeral=True)
            return

        try:
            webhook = await self.bot.webhook_service.get_or_create_webhook(channel, "prikolbot-wh")

            await webhook.send(
                content=message[:2000],
                username=self.bot.user.name,
                avatar_url=self.bot.user.avatar.url if self.bot.user.avatar else None
            )
            await interaction.response.send_message("Сообщение отправлено!", ephemeral=True)
        except Exception as e:
            print(f"Anonsay error: {e}")
            await interaction.response.send_message("Произошла ошибка при отправке сообщения.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AnonymousCog(bot))
