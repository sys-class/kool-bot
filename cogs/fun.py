import random

import discord
from discord import app_commands
from discord.ext import commands

from services import embeds


class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="furryrate", description="Показывает процент фуррь")
    @app_commands.describe(member="Пользователь для оценки (по умолчанию - ты)")
    async def furryrate(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        rate = random.Random(member.id + 42).randint(0, 100)

        if rate <= 10:
            comment = "обычный человек... пока что"
        elif rate <= 30:
            comment = "хвостик уже растёт"
        elif rate <= 50:
            comment = "ушки пробиваются"
        elif rate <= 70:
            comment = "почти фурри"
        elif rate <= 90:
            comment = "полноценный фурри"
        else:
            comment = "фуррь максимальный"

        embed = embeds.fun(
            title=f"furryrate · {member.display_name.lower()}",
            description=f"`{embeds.bar(rate)}`  **{rate}%**\n{comment}",
            user=interaction.user,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="femboyrate", description="Показывает процент фембой")
    @app_commands.describe(member="Пользователь для оценки (по умолчанию - ты)")
    async def femboyrate(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        rate = random.Random(member.id + 99).randint(0, 100)

        if rate <= 10:
            comment = "маскулинность зашкаливает"
        elif rate <= 30:
            comment = "иногда носит оверсайз худи"
        elif rate <= 50:
            comment = "юбочка уже в корзине"
        elif rate <= 70:
            comment = "чулки надеты"
        elif rate <= 90:
            comment = "полноценный фембой"
        else:
            comment = "фембой максимальный"

        embed = embeds.fun(
            title=f"femboyrate · {member.display_name.lower()}",
            description=f"`{embeds.bar(rate)}`  **{rate}%**\n{comment}",
            user=interaction.user,
        )
        await interaction.response.send_message(embed=embed)

    EIGHTBALL_ANSWERS = [
        "да", "нет", "определённо да", "скорее всего", "не уверен",
        "даже не думай", "однозначно нет", "спроси позже", "звёзды говорят да",
        "звёзды говорят нет", "возможно", "ни за что", "абсолютно",
        "не рассчитывай на это", "без сомнений", "мой ответ — нет",
        "шансы хорошие", "весьма сомнительно", "да, но не сейчас", "нет, и не проси",
    ]

    @app_commands.command(name="8ball", description="Магический шар отвечает на твой вопрос")
    @app_commands.describe(question="Твой вопрос")
    async def eightball(self, interaction: discord.Interaction, question: str):
        answer = random.choice(self.EIGHTBALL_ANSWERS)
        embed = embeds.fun(
            title="шар",
            description=f"> {question}\n\n**{answer}**",
            user=interaction.user,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Подбрасывает монетку")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["орёл", "решка"])
        embed = embeds.fun(
            title="монетка",
            description=f"**{result}**",
            user=interaction.user,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))
