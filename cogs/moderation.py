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

    @app_commands.command(name="disconnect", description="Отключает всех участников из войс-канала")
    @app_commands.describe(channel="Голосовой канал для отключения участников")
    @app_commands.guild_only()
    async def disconnect(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        if interaction.user.id not in ALLOWED_USERS:
            await interaction.response.send_message("Вы не админ.", ephemeral=True)
            return

        if not channel.members:
            await interaction.response.send_message("В канале нет пользователей для отключения.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        disconnected = 0
        for member in channel.members:
            try:
                await member.move_to(None)
                disconnected += 1
            except discord.errors.Forbidden:
                pass
            except Exception as e:
                print(f"Disconnect member error: {e}")

        await interaction.followup.send(f"Отключено {disconnected} пользователей из {channel.name}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
