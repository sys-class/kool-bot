import datetime

import discord
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
    }

    @commands.command(name="h", aliases=["help"], help="Выводит полный список команд.")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="Список команд",
            description="Префикс: `$`",
            color=0x251530,
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        sections: dict[str, list[str]] = {}
        for cmd in sorted(self.bot.commands, key=lambda c: c.qualified_name):
            if cmd.hidden:
                continue
            cog_name = type(cmd.cog).__name__ if cmd.cog else None
            section = self.COG_DISPLAY.get(cog_name, "\U0001f4e6  Другое")

            signature = f"${cmd.qualified_name}"
            if cmd.signature:
                signature += f" {cmd.signature}"
            description = cmd.help or cmd.short_doc or ""
            line = f"`{signature}`"
            if description:
                line += f" — {description}"

            sections.setdefault(section, []).append(line)

        for section_name, lines in sections.items():
            embed.add_field(name=f"\u200b\n{section_name}", value="\n".join(lines), inline=False)

        embed.set_footer(text=f"Запросил {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @commands.command(name="say")
    async def say(self, ctx, *, text: str):
        try:
            await ctx.send(text)
            await ctx.message.delete()
        except discord.errors.Forbidden:
            pass
        except Exception as e:
            print(f"Say error: {e}")

    @commands.command(name="time")
    async def time(self, ctx):
        try:
            msk_time = datetime.datetime.now(timezones["msk"]).strftime("%H:%M:%S")
            ekb_time = datetime.datetime.now(timezones["ekb"]).strftime("%H:%M:%S")
            ny_time = datetime.datetime.now(timezones["ny"]).strftime("%H:%M:%S")

            await ctx.send(f"Время:\nМСК: {msk_time}\nЕКБ: {ekb_time}\nNew York: {ny_time}")
        except Exception as e:
            print(f"Time error: {e}")
            await ctx.send("Ошибка при получении времени")

    @commands.command(name="avatar")
    async def avatar(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        try:
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed = discord.Embed(title=f"Аватар пользователя {member.name}", color=0x251530)
            embed.set_image(url=avatar_url)
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"Avatar error: {e}")
            await ctx.send("Не удалось получить аватар")


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))
