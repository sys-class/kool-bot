import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import timezones
from services import embeds


class UtilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    COG_DISPLAY = {
        "UtilityCog": "общие",
        "AnonymousCog": "общие",
        "ModerationCog": "модерация",
        "VoiceCog": "голосовые",
        "FunCog": "фан",
        "UwuifyCog": "фан",
    }

    @app_commands.command(name="help", description="Выводит полный список команд")
    async def help_command(self, interaction: discord.Interaction):
        embed = embeds.info(title="справка", user=interaction.user)

        sections: dict[str, list[str]] = {}
        for cmd in self.bot.tree.get_commands():
            cog = getattr(cmd, "binding", None)
            cog_name = type(cog).__name__ if cog else None
            section = self.COG_DISPLAY.get(cog_name, "другое")
            sections.setdefault(section, []).append(f"`/{cmd.name}` — {cmd.description.lower()}")

        for section_name in sorted(sections):
            embed.add_field(
                name=section_name,
                value="\n".join(sorted(sections[section_name])),
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="say", description="Отправляет сообщение от имени бота")
    @app_commands.describe(text="Текст сообщения")
    @app_commands.guild_only()
    async def say(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message(text)

    @app_commands.command(name="time", description="Показывает текущее время в разных часовых поясах")
    async def time(self, interaction: discord.Interaction):
        try:
            rows = [
                ("мск", "msk"),
                ("екб", "ekb"),
                ("ny ", "ny"),
            ]
            lines = [
                f"`{label}`  {datetime.datetime.now(timezones[key]).strftime('%H:%M')}"
                for label, key in rows
            ]
            await interaction.response.send_message(
                embed=embeds.info(title="время", description="\n".join(lines), user=interaction.user)
            )
        except Exception as e:
            print(f"Time error: {e}")
            await interaction.response.send_message(
                embed=embeds.err("не удалось получить время", user=interaction.user),
                ephemeral=True,
            )

    @app_commands.command(name="avatar", description="Показывает аватар пользователя")
    @app_commands.describe(member="Пользователь (по умолчанию - ты)")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        try:
            avatar_url = (member.avatar or member.default_avatar).url
            embed = embeds.info(title=member.display_name, user=interaction.user)
            embed.set_image(url=avatar_url)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Avatar error: {e}")
            await interaction.response.send_message(
                embed=embeds.err("не удалось получить аватар", user=interaction.user),
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))
