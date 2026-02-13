import discord


class WebhookService:
    def __init__(self):
        self.cache = {}

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

    async def send_webhook_message(self, target_channel: discord.TextChannel, original_message: discord.Message):
        """Отправка сообщений через вебхук с сохранением автора"""
        content = original_message.content[:2000] if original_message.content else None

        files = []
        for attachment in original_message.attachments:
            try:
                files.append(await attachment.to_file())
            except Exception as e:
                print(f"Attachment error: {e}")

        if not content and not files:
            return

        webhook_name = "Webhook"
        try:
            webhook = await self.get_or_create_webhook(target_channel, webhook_name)
            await webhook.send(
                content=content,
                username=original_message.author.display_name[:80],
                avatar_url=original_message.author.avatar.url if original_message.author.avatar else None,
                files=files if files else discord.utils.MISSING,
            )
        except discord.NotFound:
            self.invalidate(target_channel.id, webhook_name)
            try:
                webhook = await self.get_or_create_webhook(target_channel, webhook_name)
                await webhook.send(
                    content=content,
                    username=original_message.author.display_name[:80],
                    avatar_url=original_message.author.avatar.url if original_message.author.avatar else None,
                    files=files if files else discord.utils.MISSING,
                )
            except Exception as e:
                print(f"Webhook retry error: {e}")
        except Exception as e:
            print(f"Webhook error: {e}")
