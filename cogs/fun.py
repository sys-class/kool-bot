import random

import discord
from discord import app_commands
from discord.ext import commands


class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="furryrate", description="Показывает процент фуррь")
    @app_commands.describe(member="Пользователь для оценки (по умолчанию - ты)")
    async def furryrate(self, interaction: discord.Interaction, member: discord.Member = None):
        """Фуррирейт"""
        member = member or interaction.user
        random.seed(member.id + 42)
        rate = random.randint(0, 100)
        random.seed()

        bar_filled = round(rate / 10)
        bar = "\U0001f43e" * bar_filled + "\u2b1b" * (10 - bar_filled)

        if rate <= 10:
            comment = "Обычный человек... пока что"
        elif rate <= 30:
            comment = "Хвостик уже растёт"
        elif rate <= 50:
            comment = "Ушки пробиваются"
        elif rate <= 70:
            comment = "Почти фурри"
        elif rate <= 90:
            comment = "Полноценный фурри"
        else:
            comment = "Фуррь максимальный"

        embed = discord.Embed(title=f"{member.display_name}", color=0x9B59B6)
        embed.description = f"{bar} **{rate}%**\n{comment}"
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="femboyrate", description="Показывает процент фембой")
    @app_commands.describe(member="Пользователь для оценки (по умолчанию - ты)")
    async def femboyrate(self, interaction: discord.Interaction, member: discord.Member = None):
        """Фембойрейт"""
        member = member or interaction.user
        random.seed(member.id + 99)
        rate = random.randint(0, 100)
        random.seed()

        bar_filled = round(rate / 10)
        bar = "\U0001f338" * bar_filled + "\u2b1b" * (10 - bar_filled)

        if rate <= 10:
            comment = "Маскулинность зашкаливает"
        elif rate <= 30:
            comment = "Иногда носит оверсайз худи"
        elif rate <= 50:
            comment = "Юбочка уже в корзине"
        elif rate <= 70:
            comment = "Чулки надеты"
        elif rate <= 90:
            comment = "Полноценный фембой"
        else:
            comment = "Фембой максимальный"

        embed = discord.Embed(title=f"{member.display_name}", color=0xFFB6C1)
        embed.description = f"{bar} **{rate}%**\n{comment}"
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))
