from discord.ext import commands

from config import ANON_TARGET_CHANNEL_ID


class AnonymousCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="s")
    async def anonsay(self, ctx, *, message_content: str):
        """Анонимно отправляет сообщение в указанный канал"""
        if ctx.guild is not None:
            await ctx.send("Только в лс", delete_after=5)
            return

        channel = self.bot.get_channel(ANON_TARGET_CHANNEL_ID)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(ANON_TARGET_CHANNEL_ID)
            except Exception:
                channel = None

        if not channel:
            await ctx.send("Не удалось найти канал для отправки сообщения.")
            return

        try:
            webhook = await self.bot.webhook_service.get_or_create_webhook(channel, "prikolbot-wh")

            await webhook.send(
                content=message_content[:2000],
                username=self.bot.user.name,
                avatar_url=self.bot.user.avatar.url if self.bot.user.avatar else None
            )
            await ctx.send("Сообщение отправлено!", delete_after=3)
        except Exception as e:
            print(f"Anonsay error: {e}")
            await ctx.send("Произошла ошибка при отправке сообщения.")


async def setup(bot: commands.Bot):
    await bot.add_cog(AnonymousCog(bot))
