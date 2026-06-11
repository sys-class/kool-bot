"""Вебхуки не должны пробивать @everyone и роли чужим текстом."""

import asyncio
from unittest.mock import AsyncMock

import discord

from services.webhook import SAFE_MENTIONS, WebhookService


def test_safe_mentions_block_everyone_and_roles():
    assert SAFE_MENTIONS.everyone is False
    assert SAFE_MENTIONS.roles is False
    assert SAFE_MENTIONS.users is True


def test_send_injects_safe_mentions_by_default():
    service = WebhookService()
    webhook = AsyncMock()
    service.get_or_create_webhook = AsyncMock(return_value=webhook)

    asyncio.run(service.send(AsyncMock(), "Webhook", content="@everyone хех"))

    assert webhook.send.await_args.kwargs["allowed_mentions"] is SAFE_MENTIONS


def test_send_keeps_explicit_mentions():
    service = WebhookService()
    webhook = AsyncMock()
    service.get_or_create_webhook = AsyncMock(return_value=webhook)
    none = discord.AllowedMentions.none()

    asyncio.run(
        service.send(AsyncMock(), "Webhook", content="x", allowed_mentions=none)
    )

    assert webhook.send.await_args.kwargs["allowed_mentions"] is none
