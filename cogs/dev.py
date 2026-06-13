import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import ALLOWED_USERS
from services import embeds

log = logging.getLogger(__name__)

# уровни для /logtest. None значит «прогнать все по очереди»
_LEVELS = ("debug", "info", "warning", "error")


class DevCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="logtest", description="Тест логирования: шлёт записи разных уровней"
    )
    @app_commands.describe(level="Уровень (по умолчанию прогоняет все)")
    @app_commands.choices(
        level=[app_commands.Choice(name=lvl, value=lvl) for lvl in _LEVELS]
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def logtest(
        self,
        interaction: discord.Interaction,
        level: app_commands.Choice[str] | None = None,
    ):
        if interaction.user.id not in ALLOWED_USERS:
            await interaction.response.send_message(
                embed=embeds.err("только для админов", user=interaction.user),
                ephemeral=True,
            )
            return

        levels = [level.value] if level is not None else list(_LEVELS)
        who = interaction.user
        for lvl in levels:
            if lvl == "error":
                # настоящий эксепшен, чтобы проверить и трейсбек, и пинг на ERROR
                try:
                    raise RuntimeError("тестовая ошибка из /logtest")
                except RuntimeError:
                    log.exception("logtest error от %s", who)
            else:
                log.log(
                    logging.getLevelName(lvl.upper()),
                    "logtest %s от %s",
                    lvl,
                    who,
                )

        await interaction.response.send_message(
            embed=embeds.ok(
                title="logtest",
                description=f"отправил уровни: {', '.join(levels)}",
                user=who,
            ),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(DevCog(bot))
