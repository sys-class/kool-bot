import pytz

import config
from config import ALLOWED_USERS, TARGET_VOICE_CHANNELS, timezones


def test_load_token_from_file(monkeypatch, tmp_path):
    token_file = tmp_path / "bot_token"
    token_file.write_text("secret-from-file\n", encoding="utf-8")
    monkeypatch.setenv("TOKEN_FILE", str(token_file))
    monkeypatch.setenv("TOKEN", "secret-from-env")
    # файл имеет приоритет над переменной окружения, значение стрипается
    assert config._load_token() == "secret-from-file"


def test_load_token_unreadable_file_does_not_fall_back(monkeypatch, tmp_path):
    monkeypatch.setenv("TOKEN_FILE", str(tmp_path / "missing"))
    monkeypatch.setenv("TOKEN", "secret-from-env")
    # заданный, но нечитаемый TOKEN_FILE — ошибка конфигурации, а не повод
    # тихо уехать на токен из окружения
    assert config._load_token() == ""


def test_load_token_falls_back_to_env(monkeypatch):
    monkeypatch.delenv("TOKEN_FILE", raising=False)
    monkeypatch.setenv("TOKEN", "secret-from-env")
    assert config._load_token() == "secret-from-env"


def test_load_token_empty_when_nothing_set(monkeypatch):
    monkeypatch.delenv("TOKEN_FILE", raising=False)
    monkeypatch.delenv("TOKEN", raising=False)
    assert config._load_token() == ""


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
