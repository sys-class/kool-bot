import asyncio
import time

from cogs.reminders import (
    MAX_DELIVERY_ATTEMPTS,
    RemindersCog,
    _fmt_remaining,
    _parse_duration,
)


def test_parse_seconds():
    assert _parse_duration("30s") == 30
    assert _parse_duration("45сек") == 45


def test_parse_minutes():
    assert _parse_duration("5m") == 300
    assert _parse_duration("10мин") == 600


def test_parse_hours():
    assert _parse_duration("2h") == 7200
    assert _parse_duration("3ч") == 10800


def test_parse_days():
    assert _parse_duration("1d") == 86400
    assert _parse_duration("2д") == 86400 * 2


def test_parse_weeks():
    assert _parse_duration("1w") == 604800
    assert _parse_duration("1нед") == 604800


def test_parse_compound():
    assert _parse_duration("1h30m") == 5400
    assert _parse_duration("1д 2ч") == 86400 + 7200


def test_parse_invalid():
    assert _parse_duration("") is None
    assert _parse_duration("nope") is None
    assert _parse_duration("0m") is None


def test_fmt_seconds():
    assert _fmt_remaining(45) == "45 сек"


def test_fmt_minutes():
    assert _fmt_remaining(120) == "2 мин"


def test_fmt_hours_round():
    assert _fmt_remaining(3600) == "1 ч"


def test_fmt_hours_with_minutes():
    assert _fmt_remaining(3600 + 600) == "1 ч 10 мин"


def test_fmt_days_round():
    assert _fmt_remaining(86400) == "1 д"


def test_fmt_days_with_hours():
    assert _fmt_remaining(86400 + 7200) == "1 д 2 ч"


def _make_cog(reminders):
    cog = RemindersCog.__new__(RemindersCog)
    cog.bot = None
    cog.reminders = reminders

    async def _save():
        pass

    cog._save = _save
    return cog


def _reminder(**extra):
    return {
        "id": "abc12345",
        "user_id": 1,
        "channel_id": 2,
        "due": time.time() - 5,
        "text": "тест",
        **extra,
    }


def _run_tick(cog):
    asyncio.run(RemindersCog.tick.coro(cog))


def test_tick_keeps_reminder_on_failed_delivery():
    cog = _make_cog([_reminder()])

    async def _deliver(r):
        return False

    cog._deliver = _deliver
    _run_tick(cog)
    assert len(cog.reminders) == 1
    assert cog.reminders[0]["attempts"] == 1


def test_tick_drops_reminder_after_max_attempts():
    cog = _make_cog([_reminder(attempts=MAX_DELIVERY_ATTEMPTS - 1)])

    async def _deliver(r):
        return False

    cog._deliver = _deliver
    _run_tick(cog)
    assert cog.reminders == []


def test_tick_removes_delivered_reminder():
    cog = _make_cog([_reminder()])

    async def _deliver(r):
        return True

    cog._deliver = _deliver
    _run_tick(cog)
    assert cog.reminders == []
