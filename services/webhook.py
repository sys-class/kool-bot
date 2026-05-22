import asyncio

import discord


class WebhookService:
    def __init__(self):
        self.cache: dict[str, discord.Webhook] = {}

    async def get_or_create_webhook(self, channel: discord.TextChannel, name: str) -> discord.Webhook:
        webhook_key = f"{channel.id}_{name}"
        webhook = self.cache.get(webhook_key)

        if not webhook:
            webhooks = await channel.webhooks()
            for wh in webhooks:
                if wh.name == name:
                    webhook = wh
                    break

            if not webhook:
                webhook = await channel.create_webhook(name=name)

            self.cache[webhook_key] = webhook

        return webhook

    def invalidate(self, channel_id: int, name: str):
        self.cache.pop(f"{channel_id}_{name}", None)

    async def _send(self, channel: discord.TextChannel, name: str, **kwargs):
        try:
            webhook = await self.get_or_create_webhook(channel, name)
            await webhook.send(**kwargs)
        except discord.NotFound:
            self.invalidate(channel.id, name)
            webhook = await self.get_or_create_webhook(channel, name)
            await webhook.send(**kwargs)

    async def send_webhook_message(self, target_channel: discord.TextChannel, original_message: discord.Message):
        """Отправка сообщений через вебхук с сохранением автора"""
        content = original_message.content[:2000] if original_message.content else None

        files: list[discord.File] = []
        if original_message.attachments:
            results = await asyncio.gather(
                *(a.to_file() for a in original_message.attachments),
                return_exceptions=True,
            )
            for r in results:
                if isinstance(r, discord.File):
                    files.append(r)
                else:
                    print(f"Attachment error: {r}")

        if not content and not files:
            return

        author = original_message.author
        kwargs = dict(
            content=content,
            username=author.display_name[:80],
            avatar_url=author.display_avatar.url,
            files=files if files else discord.utils.MISSING,
        )
        try:
            await self._send(target_channel, "Webhook", **kwargs)
        except Exception as e:
            print(f"Webhook error: {e}")
