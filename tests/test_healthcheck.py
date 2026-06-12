import subprocess
import sys
import time
from pathlib import Path

import healthcheck

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_main_returns_zero_when_healthy(monkeypatch):
    monkeypatch.setattr(healthcheck, "is_healthy", lambda: True)
    assert healthcheck.main() == 0


def test_main_returns_one_when_unhealthy(monkeypatch):
    monkeypatch.setattr(healthcheck, "is_healthy", lambda: False)
    assert healthcheck.main() == 1


def _run(env_data_dir: Path) -> int:
    # запускаем скрипт ровно как docker HEALTHCHECK, с DATA_DIR во временной папке
    env = {"PATH": "/usr/bin:/bin", "DATA_DIR": str(env_data_dir)}
    proc = subprocess.run(
        [sys.executable, "healthcheck.py"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
    )
    return proc.returncode


def test_script_exit_zero_on_fresh_heartbeat(tmp_path):
    (tmp_path / ".heartbeat").write_text(str(time.time()), encoding="utf-8")
    assert _run(tmp_path) == 0


def test_script_exit_one_on_missing_heartbeat(tmp_path):
    assert _run(tmp_path) == 1


def test_script_exit_one_on_stale_heartbeat(tmp_path):
    (tmp_path / ".heartbeat").write_text(str(time.time() - 1000), encoding="utf-8")
    assert _run(tmp_path) == 1
