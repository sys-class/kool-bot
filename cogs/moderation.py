import discord
from discord.ext import commands

from config import ALLOWED_USERS


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        if amount <= 0:
            await ctx.send("Сколько?")
            return

        try:
            deleted = await ctx.channel.purge(limit=amount + 1, check=lambda m: m != ctx.message)
            await ctx.send(f"Я удалил {len(deleted)} сообщений для тебя~", delete_after=5)
        except discord.errors.Forbidden:
            await ctx.send("Нет прав в канале")
        except Exception as e:
            print(f"Clear error: {e}")

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Нет прав")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Сколько?")
        else:
            print(f"Clear error: {error}")

    @commands.command(name="disconnect")
    async def disconnect(self, ctx, channel_id: int):
        """Отключает всех участников из войса по айди."""
        if ctx.author.id not in ALLOWED_USERS:
            await ctx.send("Вы не админ.")
            return

        try:
            channel = self.bot.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.VoiceChannel):
                await ctx.send("Указан неверный айди войса.")
                return

            disconnected = 0
            for member in channel.members:
                try:
                    await member.move_to(None)
                    disconnected += 1
                except discord.errors.Forbidden:
                    await ctx.send(f"Не удалось отключить {member.name}. Нет прав.", delete_after=5)
                except Exception as e:
                    print(f"Disconnect member error: {e}")

            if disconnected > 0:
                await ctx.send(f"Отключено {disconnected} пользователей.")
            else:
                await ctx.send("В канале нет пользователей для отключения.")

        except Exception as e:
            print(f"Disconnect error: {e}")
            await ctx.send("Произошла ошибка при выполнении команды.")

    @disconnect.error
    async def disconnect_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Неверный айди войса.")
        else:
            print(f"Disconnect error: {error}")
            await ctx.send("Произошла ошибка при выполнении команды.")


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
