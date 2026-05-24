"""все модули должны импортироваться без сайд-эффектов (кроме bot.py — там bot.run)."""

import importlib
import pkgutil

import pytest

import cogs
import services


def _iter_submodules(pkg):
    return [m.name for m in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + ".")]


@pytest.mark.parametrize("module_name", _iter_submodules(cogs))
def test_cog_imports(module_name):
    importlib.import_module(module_name)


@pytest.mark.parametrize("module_name", _iter_submodules(services))
def test_service_imports(module_name):
    importlib.import_module(module_name)


def test_config_imports():
    import config

    assert hasattr(config, "TOKEN")
    assert hasattr(config, "ALLOWED_USERS")
    assert hasattr(config, "TARGET_VOICE_CHANNELS")
    assert hasattr(config, "timezones")
