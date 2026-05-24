from cogs.reminders import _fmt_remaining, _parse_duration


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
