import importlib

import pytest

from config import DATA_DIR

# каждый модуль и имя константы с путём к json-состоянию
CASES = [
    ("cogs.social", "MOOD_FILE"),
    ("cogs.reminders", "REMINDERS_FILE"),
    ("cogs.uwuify", "UWUIFIED_FILE"),
    ("cogs.stats", "STATS_FILE"),
]


@pytest.mark.parametrize("module_name, attr", CASES)
def test_state_file_under_data_dir(module_name, attr):
    module = importlib.import_module(module_name)
    path = getattr(module, attr)
    # состояние должно лежать в DATA_DIR, иначе при пересоздании контейнера
    # данные стираются — volume монтируется именно в DATA_DIR (#10)
    assert path.parent == DATA_DIR
