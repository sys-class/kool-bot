import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import timezones


class UtilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    COG_DISPLAY = {
        "UtilityCog": "\U0001f4ac  Общие",
        "AnonymousCog": "\U0001f4ac  Общие",
        "ModerationCog": "\U0001f6e1  Модерация",
        "VoiceCog": "\U0001f50a  Голосовые каналы",
        "FunCog": "\U0001f43e  Фан",
        "UwuifyCog": "\U0001f43e  Фан",
    }

    @app_commands.command(name="help", description="Выводит полный список команд")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Список команд",
            description="Все команды используют `/`",
            color=0x251530,
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        sections: dict[str, list[str]] = {}

        for cmd in self.bot.tree.get_commands():
            cog = getattr(cmd, "binding", None)
            cog_name = type(cog).__name__ if cog else None
            section = self.COG_DISPLAY.get(cog_name, "\U0001f4e6  Другое")

            line = f"`/{cmd.name}` — {cmd.description}"
            sections.setdefault(section, []).append(line)

        for section_name, lines in sections.items():
            embed.add_field(name=f"\u200b\n{section_name}", value="\n".join(lines), inline=False)

        embed.set_footer(text=f"Запросил {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="say", description="Отправляет сообщение от имени бота")
    @app_commands.describe(text="Текст сообщения")
    @app_commands.guild_only()
    async def say(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message(text)

    @app_commands.command(name="time", description="Показывает текущее время в разных часовых поясах")
    async def time(self, interaction: discord.Interaction):
        try:
            msk_time = datetime.datetime.now(timezones["msk"]).strftime("%H:%M:%S")
            ekb_time = datetime.datetime.now(timezones["ekb"]).strftime("%H:%M:%S")
            ny_time = datetime.datetime.now(timezones["ny"]).strftime("%H:%M:%S")

            await interaction.response.send_message(
                f"Время:\nМСК: {msk_time}\nЕКБ: {ekb_time}\nNew York: {ny_time}"
            )
        except Exception as e:
            print(f"Time error: {e}")
            await interaction.response.send_message("Ошибка при получении времени", ephemeral=True)

    @app_commands.command(name="avatar", description="Показывает аватар пользователя")
    @app_commands.describe(member="Пользователь (по умолчанию - ты)")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member = interaction.user

        try:
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed = discord.Embed(title=f"Аватар пользователя {member.name}", color=0x251530)
            embed.set_image(url=avatar_url)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(f"Avatar error: {e}")
            await interaction.response.send_message("Не удалось получить аватар", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))
