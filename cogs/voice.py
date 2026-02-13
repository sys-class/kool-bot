import asyncio

import discord
from discord.ext import commands, tasks

from config import TARGET_VOICE_CHANNELS, SOURCE_CHANNEL_1
from services.cooldown import CooldownManager


class VoiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldown_manager = CooldownManager()

    async def cog_load(self):
        self.cleanup_task.start()

    async def cog_unload(self):
        self.cleanup_task.cancel()

    @tasks.loop(seconds=600)
    async def cleanup_task(self):
        """Фоновая задача для периодической очистки пустых каналов."""
        try:
            for guild in self.bot.guilds:
                await self.cleanup_empty_home_channels(guild)
        except Exception as e:
            print(f"Background cleanup error: {e}")

    @cleanup_task.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild_id = member.guild.id

        if guild_id in TARGET_VOICE_CHANNELS:
            target_channels = TARGET_VOICE_CHANNELS[guild_id]

            if after.channel and after.channel.id in target_channels:
                if not self.cooldown_manager.check_cooldown(member.id):
                    channel = self.bot.get_channel(SOURCE_CHANNEL_1)
                    if channel:
                        try:
                            await channel.send(f"Пользователь {member.name} атакует войсы!!")
                        except Exception as e:
                            print(f"Warning error: {e}")
                    return

                category = after.channel.category
                voice_channel = await self.create_custom_voice_channel(member.guild, category, member)

                if voice_channel:
                    try:
                        await member.move_to(voice_channel)
                        self.bot.channel_creators[voice_channel.id] = member.id
                        self.bot.bot_created_channels.add(voice_channel.id)
                    except Exception as e:
                        print(f"Move error: {e}")
                        try:
                            await voice_channel.delete()
                        except:
                            pass

        if before.channel and before.channel.id in self.bot.bot_created_channels:
            await self.check_and_cleanup_channel(before.channel)

    async def create_custom_voice_channel(self, guild, category, creator):
        """Создает кастомный голосовой канал"""
        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    connect=True,
                    view_channel=True
                ),
                creator: discord.PermissionOverwrite(
                    connect=True,
                    view_channel=True,
                    mute_members=True,
                    manage_channels=True
                )
            }

            voice_channel = await guild.create_voice_channel(
                name=f"/home/{creator.name}"[:100],
                category=category,
                overwrites=overwrites,
                reason="Автоматическое создание домашнего канала"
            )

            return voice_channel
        except Exception as e:
            print(f"Create channel error: {e}")
            return None

    async def check_and_cleanup_channel(self, channel):
        """Проверяет канал и удаляет его если он пустой и создан ботом"""
        if channel.id not in self.bot.bot_created_channels:
            return

        channel_obj = self.bot.get_channel(channel.id)
        if not channel_obj:
            self.bot.bot_created_channels.discard(channel.id)
            self.bot.channel_creators.pop(channel.id, None)
            return

        if channel_obj.members:
            return

        try:
            self.bot.bot_created_channels.discard(channel.id)
            self.bot.channel_creators.pop(channel.id, None)

            await channel_obj.delete(reason="Пустой канал созданный ботом")
            print(f"Удален пустой канал: {channel.name}")
        except discord.errors.NotFound:
            print(f"Канал {channel.name} уже удален.")
        except Exception as e:
            print(f"Cleanup error: {e}")

    async def cleanup_empty_home_channels(self, guild):
        """Удаляет все пустые войсы созданные ботом."""
        channels_to_clean = []

        for channel in guild.voice_channels:
            if channel.id in self.bot.bot_created_channels and not channel.members:
                channels_to_clean.append(channel)

        cleanup_tasks = []
        for channel in channels_to_clean:
            cleanup_tasks.append(self.check_and_cleanup_channel(channel))

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

    @commands.command(name="targets")
    async def show_targets(self, ctx):
        """Показывает целевые войс-каналы на этом сервере"""
        guild_id = ctx.guild.id

        if guild_id not in TARGET_VOICE_CHANNELS or not TARGET_VOICE_CHANNELS[guild_id]:
            await ctx.send("На этом сервере нет целевых войс-каналов.")
            return

        embed = discord.Embed(
            title="🎯 Целевые войс-каналы",
            description=f"Сервер: {ctx.guild.name}",
            color=discord.Color.green()
        )

        for i, channel_id in enumerate(TARGET_VOICE_CHANNELS[guild_id], 1):
            channel = ctx.guild.get_channel(channel_id)
            channel_name = channel.name if channel else f"Канал не найден ({channel_id})"
            embed.add_field(
                name=f"Канал #{i}",
                value=f"**ID:** {channel_id}\n**Имя:** {channel_name}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name="addtarget")
    @commands.has_permissions(administrator=True)
    async def add_target(self, ctx, channel_id: int):
        """Добавляет войс-канал в целевые"""
        channel = ctx.guild.get_channel(channel_id)
        if not channel:
            await ctx.send("Канал с таким ID не найден на этом сервере.")
            return

        if not isinstance(channel, discord.VoiceChannel):
            await ctx.send("Указанный канал не является голосовым каналом.")
            return

        guild_id = ctx.guild.id

        if guild_id not in TARGET_VOICE_CHANNELS:
            TARGET_VOICE_CHANNELS[guild_id] = []

        if channel_id in TARGET_VOICE_CHANNELS[guild_id]:
            await ctx.send(f"Канал {channel.name} уже добавлен в целевые.")
            return

        TARGET_VOICE_CHANNELS[guild_id].append(channel_id)
        await ctx.send(f"✅ Канал **{channel.name}** добавлен в целевые войс-каналы!")

    @add_target.error
    async def add_target_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("У вас недостаточно прав для использования этой команды.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Пожалуйста, укажите корректный ID канала.")
        else:
            await ctx.send("Произошла ошибка при выполнении команды.")
            print(f"Add target error: {error}")

    @commands.command(name="removetarget")
    @commands.has_permissions(administrator=True)
    async def remove_target(self, ctx, channel_id: int):
        """Удаляет войс-канал из целевых"""
        guild_id = ctx.guild.id

        if guild_id not in TARGET_VOICE_CHANNELS or not TARGET_VOICE_CHANNELS[guild_id]:
            await ctx.send("На этом сервере нет целевых войс-каналов.")
            return

        if channel_id not in TARGET_VOICE_CHANNELS[guild_id]:
            await ctx.send("Этот канал не является целевым на этом сервере.")
            return

        TARGET_VOICE_CHANNELS[guild_id].remove(channel_id)

        if not TARGET_VOICE_CHANNELS[guild_id]:
            del TARGET_VOICE_CHANNELS[guild_id]

        channel = ctx.guild.get_channel(channel_id)
        channel_name = channel.name if channel else f"Канал ({channel_id})"
        await ctx.send(f"✅ Канал **{channel_name}** удален из целевых войс-каналов!")

    @remove_target.error
    async def remove_target_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("У вас недостаточно прав для использования этой команды.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Пожалуйста, укажите корректный ID канала.")
        else:
            await ctx.send("Произошла ошибка при выполнении команды.")
            print(f"Remove target error: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceCog(bot))
