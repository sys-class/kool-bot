"""Synthetic benchmark of the bot's hot paths.

Runs each hot function many times under cProfile so we can compare
before/after numbers. Does not connect to Discord.
"""
import cProfile
import json
import pstats
import random
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))

# Force a sample token so config.py doesn't blow up on missing env.
import os
os.environ.setdefault("TOKEN", "x")

from cogs.uwuify import felinid_accent, UwuifyCog
from services.cooldown import CooldownManager

SAMPLE_MESSAGES = [
    "Hello world this is a test",
    "Привет мир, как дела маленький котик",
    "Look at this link https://example.com/foo and react",
    "you are so cute, kiss the cat",
    "Plain ASCII no replacements at all here today",
    "Mixed Русский and English with l and р letters",
    "" ,
    "RLRLRLrlrl рлрлрл",
    "good kitty no bad kitty",
    "ты маленький cute cat",
]


def bench_felinid_accent(n=50_000):
    for i in range(n):
        felinid_accent(SAMPLE_MESSAGES[i % len(SAMPLE_MESSAGES)])


def bench_cooldown(n=200_000):
    cm = CooldownManager()
    for i in range(n):
        cm.check_cooldown(i % 1000)


def bench_is_uwuified(n=200_000):
    # Matches production: _load() builds sets from the JSON file.
    cog = UwuifyCog.__new__(UwuifyCog)
    container_type = set if isinstance(getattr(UwuifyCog, "_EMPTY", None), frozenset) else list
    cog.uwuified = {"123": container_type(range(500))}
    for i in range(n):
        cog.is_uwuified(123, 999_999)


def bench_uwuify_save(n=500):
    cog = UwuifyCog.__new__(UwuifyCog)
    container_type = set if isinstance(getattr(UwuifyCog, "_EMPTY", None), frozenset) else list
    cog.uwuified = {"123": container_type(range(200)), "456": container_type(range(150))}
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "uwuified.json"
        import cogs.uwuify as mod
        mod.UWUIFIED_FILE = target
        for _ in range(n):
            cog._save()


def bench_on_message_channel_map(n=200_000):
    # Mimic the dict-rebuild inside on_message
    from config import SOURCE_CHANNEL_1, SOURCE_CHANNEL_2
    ids = [SOURCE_CHANNEL_1, SOURCE_CHANNEL_2, 999, 1234]
    for i in range(n):
        channel_map = {SOURCE_CHANNEL_1: SOURCE_CHANNEL_2, SOURCE_CHANNEL_2: SOURCE_CHANNEL_1}
        _ = ids[i % 4] in channel_map


def run_all():
    bench_felinid_accent()
    bench_cooldown()
    bench_is_uwuified()
    bench_uwuify_save()
    bench_on_message_channel_map()


if __name__ == "__main__":
    import asyncio
    async def main():
        run_all()
    t0 = time.perf_counter()
    pr = cProfile.Profile()
    pr.enable()
    asyncio.run(main())
    pr.disable()
    wall = time.perf_counter() - t0
    print(f"\n=== total wall time: {wall*1000:.1f} ms ===\n")
    stats = pstats.Stats(pr).sort_stats("cumulative")
    stats.print_stats(25)
