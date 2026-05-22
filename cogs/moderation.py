import discord
from discord import app_commands
from discord.ext import commands

from config import ALLOWED_USERS
from services import embeds


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Удаляет указанное количество сообщений")
    @app_commands.describe(amount="Количество сообщений для удаления (по умолчанию 10)")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int = 10):
        if amount <= 0:
            await interaction.response.send_message(
                embed=embeds.err("количество должно быть больше нуля", user=interaction.user),
                ephemeral=True,
            )
            return

        try:
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(
                embed=embeds.ok(
                    title="очистка",
                    description=f"удалено · **{len(deleted)}**",
                    user=interaction.user,
                ),
                ephemeral=True,
            )
        except discord.errors.Forbidden:
            await interaction.followup.send(
                embed=embeds.err("у бота нет прав в этом канале", user=interaction.user),
                ephemeral=True,
            )
        except Exception as e:
            print(f"Clear error: {e}")
            await interaction.followup.send(
                embed=embeds.err("что-то пошло не так", user=interaction.user),
                ephemeral=True,
            )

    @clear.error
    async def clear_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            msg = "недостаточно прав"
        else:
            print(f"Clear error: {error}")
            msg = "что-то пошло не так"
        await interaction.response.send_message(
            embed=embeds.err(msg, user=interaction.user),
            ephemeral=True,
        )

    @app_commands.command(name="disconnect", description="Отключает всех участников из войс-канала")
    @app_commands.describe(channel="Голосовой канал для отключения участников")
    @app_commands.guild_only()
    async def disconnect(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        if interaction.user.id not in ALLOWED_USERS:
            await interaction.response.send_message(
                embed=embeds.err("только для админов", user=interaction.user),
                ephemeral=True,
            )
            return

        if not channel.members:
            await interaction.response.send_message(
                embed=embeds.err(f"в {channel.mention} никого нет", user=interaction.user),
                ephemeral=True,
            )
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

        await interaction.followup.send(
            embed=embeds.mod(
                title="канал очищен",
                description=f"{channel.mention} · отключено **{disconnected}**",
                user=interaction.user,
            ),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
