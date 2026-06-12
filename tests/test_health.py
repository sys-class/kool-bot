import time

from config import DATA_DIR
from services import health


def test_write_then_healthy(tmp_path):
    hb = tmp_path / ".heartbeat"
    health.write_heartbeat(hb)
    assert hb.exists()
    assert health.is_healthy(hb)


def test_write_creates_parent_dir(tmp_path):
    hb = tmp_path / "nested" / "dir" / ".heartbeat"
    health.write_heartbeat(hb)
    assert hb.exists()


def test_missing_file_is_unhealthy(tmp_path):
    hb = tmp_path / "does-not-exist"
    assert not health.is_healthy(hb)


def test_malformed_file_is_unhealthy(tmp_path):
    hb = tmp_path / ".heartbeat"
    hb.write_text("not-a-number", encoding="utf-8")
    assert not health.is_healthy(hb)


def test_stale_heartbeat_is_unhealthy(tmp_path):
    hb = tmp_path / ".heartbeat"
    hb.write_text(str(time.time() - 1000), encoding="utf-8")
    assert not health.is_healthy(hb, max_age=90)


def test_fresh_within_max_age(tmp_path):
    hb = tmp_path / ".heartbeat"
    hb.write_text(str(time.time() - 10), encoding="utf-8")
    assert health.is_healthy(hb, max_age=90)


def test_default_heartbeat_lives_under_data_dir():
    # heartbeat и всё состояние пишутся в DATA_DIR, иначе volume не подхватит
    assert health.HEARTBEAT_FILE.parent == DATA_DIR
