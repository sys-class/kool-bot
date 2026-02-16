import discord
from discord import app_commands
from discord.ext import commands

from config import ALLOWED_USERS


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Удаляет указанное количество сообщений")
    @app_commands.describe(amount="Количество сообщений для удаления (по умолчанию 10)")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int = 10):
        if amount <= 0:
            await interaction.response.send_message("Сколько?", ephemeral=True)
            return

        try:
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"Я удалил {len(deleted)} сообщений для тебя~")
        except discord.errors.Forbidden:
            await interaction.followup.send("У тебя нет прав в канале")
        except Exception as e:
            print(f"Clear error: {e}")
            await interaction.followup.send("Произошла ошибка")

    @clear.error
    async def clear_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("У тебя нет прав", ephemeral=True)
        else:
            print(f"Clear error: {error}")
            await interaction.response.send_message("Произошла ошибка", ephemeral=True)

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
                    await ctx.send(f"Не удалось отключить {member.name}. У тебя нет прав.", delete_after=5)
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
