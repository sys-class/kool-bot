import random

import discord
from discord.ext import commands


class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="furryrate")
    async def furryrate(self, ctx, member: discord.Member = None):
        """Фуррирейт"""
        member = member or ctx.author
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
        await ctx.send(embed=embed)

    @commands.command(name="femboyrate")
    async def femboyrate(self, ctx, member: discord.Member = None):
        """Фембойрейт"""
        member = member or ctx.author
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
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))
