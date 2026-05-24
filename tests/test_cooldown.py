import time
from unittest.mock import patch

from services.cooldown import CooldownManager


def test_first_call_allowed():
    cm = CooldownManager()
    assert cm.check_cooldown(1) is True


def test_second_call_blocked():
    cm = CooldownManager()
    cm.check_cooldown(1)
    assert cm.check_cooldown(1) is False


def test_cooldown_expires():
    cm = CooldownManager()
    with patch("services.cooldown.time.monotonic") as m:
        m.return_value = 100.0
        assert cm.check_cooldown(1) is True
        m.return_value = 100.0 + cm.cooldown_time + 0.01
        assert cm.check_cooldown(1) is True


def test_per_user_isolation():
    cm = CooldownManager()
    assert cm.check_cooldown(1) is True
    assert cm.check_cooldown(2) is True


def test_remaining_zero_when_unused():
    cm = CooldownManager()
    assert cm.remaining(42) == 0.0


def test_remaining_positive_after_use():
    cm = CooldownManager()
    cm.check_cooldown(1)
    r = cm.remaining(1)
    assert 0.0 < r <= cm.cooldown_time


def test_remaining_clamped_to_zero():
    cm = CooldownManager()
    cm.cooldowns[1] = time.monotonic() - 999
    assert cm.remaining(1) == 0.0
