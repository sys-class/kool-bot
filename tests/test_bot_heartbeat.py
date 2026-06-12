import asyncio

import bot as botmod


class _FakeBot:
    def __init__(
        self,
        closed: bool = False,
        ready: bool = True,
        latency: float = 0.05,
    ):
        self._closed = closed
        self._ready = ready
        self.latency = latency

    def is_closed(self) -> bool:
        return self._closed

    def is_ready(self) -> bool:
        return self._ready


def _run_heartbeat(fake) -> None:
    # вызываем корутину tasks.loop напрямую, как в test_reminders
    asyncio.run(botmod.CoolBot._heartbeat.coro(fake))


def test_heartbeat_writes_when_open(monkeypatch):
    calls = []
    monkeypatch.setattr(botmod, "write_heartbeat", lambda: calls.append(True))
    _run_heartbeat(_FakeBot())
    assert calls == [True]


def test_heartbeat_skips_when_closed(monkeypatch):
    calls = []
    monkeypatch.setattr(botmod, "write_heartbeat", lambda: calls.append(True))
    _run_heartbeat(_FakeBot(closed=True))
    assert calls == []


def test_heartbeat_skips_when_not_ready(monkeypatch):
    # во время авто-реконнекта is_closed() == False, но is_ready() == False —
    # heartbeat писаться не должен, иначе отвалившийся бот выглядит healthy
    calls = []
    monkeypatch.setattr(botmod, "write_heartbeat", lambda: calls.append(True))
    _run_heartbeat(_FakeBot(ready=False))
    assert calls == []


def test_heartbeat_skips_when_latency_not_finite(monkeypatch):
    calls = []
    monkeypatch.setattr(botmod, "write_heartbeat", lambda: calls.append(True))
    _run_heartbeat(_FakeBot(latency=float("nan")))
    _run_heartbeat(_FakeBot(latency=float("inf")))
    assert calls == []


def test_heartbeat_swallows_write_errors(monkeypatch):
    def _boom():
        raise OSError("disk full")

    monkeypatch.setattr(botmod, "write_heartbeat", _boom)
    # ошибка записи не должна ронять heartbeat-петлю
    _run_heartbeat(_FakeBot())
