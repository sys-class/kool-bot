import pytz

from config import ALLOWED_USERS, TARGET_VOICE_CHANNELS, timezones


def test_timezones_are_real():
    for name, tz in timezones.items():
        assert isinstance(tz, pytz.tzinfo.BaseTzInfo), name


def test_allowed_users_are_ints():
    assert all(isinstance(u, int) for u in ALLOWED_USERS)


def test_target_voice_channels_shape():
    for guild_id, channels in TARGET_VOICE_CHANNELS.items():
        assert isinstance(guild_id, int)
        assert isinstance(channels, list)
        assert all(isinstance(c, int) for c in channels)
