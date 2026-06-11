import asyncio

import bot as botmod


class _FakeBot:
    def __init__(self, closed: bool):
        self._closed = closed

    def is_closed(self) -> bool:
        return self._closed


def _run_heartbeat(fake) -> None:
    # вызываем корутину tasks.loop напрямую, как в test_reminders
    asyncio.run(botmod.CoolBot._heartbeat.coro(fake))


def test_heartbeat_writes_when_open(monkeypatch):
    calls = []
    monkeypatch.setattr(botmod, "write_heartbeat", lambda: calls.append(True))
    _run_heartbeat(_FakeBot(closed=False))
    assert calls == [True]


def test_heartbeat_skips_when_closed(monkeypatch):
    calls = []
    monkeypatch.setattr(botmod, "write_heartbeat", lambda: calls.append(True))
    _run_heartbeat(_FakeBot(closed=True))
    assert calls == []


def test_heartbeat_swallows_write_errors(monkeypatch):
    def _boom():
        raise OSError("disk full")

    monkeypatch.setattr(botmod, "write_heartbeat", _boom)
    # ошибка записи не должна ронять heartbeat-петлю
    _run_heartbeat(_FakeBot(closed=False))
