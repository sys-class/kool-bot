"""Доставка логов в дискорд эмбедами через вебхук.

Хендлер логгинга синхронный, а отправка в дискорд асинхронная, поэтому
``emit`` не шлёт сам, а лишь кладёт запись в asyncio-очередь (не блокируясь),
а фоновый воркер её разбирает и постит через вебхук. Так логирование никогда
не тормозит вызывающий код и не зависит от состояния шлюза: вебхук это обычный
http-post по своему токену, он работает даже когда бот переподключается.

Цвет эмбеда зависит от уровня. ERROR и выше пингуют ответственного.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from collections.abc import Awaitable, Callable

import discord

# цвета эмбедов по уровню, чтобы уровень читался с одного взгляда
LEVEL_COLORS = {
    logging.DEBUG: 0x95A5A6,  # серый
    logging.INFO: 0x3498DB,  # синий
    logging.WARNING: 0xE67E22,  # оранжевый
    logging.ERROR: 0xE74C3C,  # красный
    logging.CRITICAL: 0x992D22,  # тёмно-красный
}
_DEFAULT_COLOR = 0x3A3340

# дискордовские лимиты на эмбед, с запасом под обрамление код-блока
_MAX_DESC = 3900
_MAX_FOOTER = 2048

# размер буфера: если за раз накопилось больше, лишнее тихо роняем, чтобы
# всплеск логов не съел память и не устроил очередь на минуты
_QUEUE_MAXSIZE = 1000


def build_embed(
    record: logging.LogRecord, format_message: Callable[..., str]
) -> discord.Embed:
    """Собирает эмбед из записи лога. ``format_message`` форматирует тело."""
    body = format_message(record)
    embed = discord.Embed(
        title=record.levelname,
        description=f"```\n{body[:_MAX_DESC]}\n```",
        color=LEVEL_COLORS.get(record.levelno, _DEFAULT_COLOR),
        timestamp=datetime.datetime.fromtimestamp(
            record.created, tz=datetime.timezone.utc
        ),
    )
    embed.set_footer(
        text=f"{record.name} · {record.module}:{record.lineno}"[:_MAX_FOOTER]
    )
    return embed


class DiscordLogHandler(logging.Handler):
    """Шлёт записи лога эмбедами в дисканал через переданный sender.

    ``sender`` — корутина-отправитель (обычно ``webhook.send``), принимает
    ``content``, ``embed``, ``allowed_mentions``. Хендлер не знает про вебхук
    напрямую, поэтому его легко тестировать с моком.
    """

    def __init__(
        self,
        *,
        sender: Callable[..., Awaitable[object]],
        loop: asyncio.AbstractEventLoop,
        ping_user_id: int | None = None,
        level: int = logging.WARNING,
    ) -> None:
        super().__init__(level=level)
        self._sender = sender
        self._loop = loop
        self._ping_user_id = ping_user_id
        self.queue: asyncio.Queue[logging.LogRecord] = asyncio.Queue(_QUEUE_MAXSIZE)
        self._task: asyncio.Task | None = None
        self.setFormatter(logging.Formatter("%(message)s"))
        # не зацикливаемся: записи самого хендлера и болтливого http дискорда
        # (рейтлимиты и т.п.) в дискорд не шлём, иначе ошибка отправки породит
        # новую отправку и так до бесконечности
        self.addFilter(lambda r: not r.name.startswith(("discord", __name__)))

    def start(self) -> None:
        """Запускает фонового воркера. Вызывать внутри работающего loop."""
        if self._task is None:
            self._task = self._loop.create_task(self._worker())

    async def aclose(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def emit(self, record: logging.LogRecord) -> None:
        # синхронный путь: только кладём запись в очередь, не блокируясь.
        # из любого потока безопасно через call_soon_threadsafe
        if self._loop.is_closed():
            return
        try:
            self._loop.call_soon_threadsafe(self._enqueue, record)
        except RuntimeError:
            # loop закрылся между проверкой и вызовом — теряем запись, но не падаем
            pass

    def _enqueue(self, record: logging.LogRecord) -> None:
        try:
            self.queue.put_nowait(record)
        except asyncio.QueueFull:
            # очередь забита: роняем запись, логирование важнее доставки в дискорд
            pass

    async def _worker(self) -> None:
        while True:
            record = await self.queue.get()
            try:
                await self._deliver(record)
            except Exception:
                # ошибку доставки пишем в stderr, а НЕ через logging, иначе
                # снова попадём сюда же
                self.handleError(record)
            finally:
                self.queue.task_done()

    async def _deliver(self, record: logging.LogRecord) -> None:
        embed = build_embed(record, self.format)
        content: str | None = None
        allowed = discord.AllowedMentions.none()
        if record.levelno >= logging.ERROR and self._ping_user_id is not None:
            content = f"<@{self._ping_user_id}>"
            allowed = discord.AllowedMentions(
                users=[discord.Object(id=self._ping_user_id)]
            )
        await self._sender(content=content, embed=embed, allowed_mentions=allowed)
