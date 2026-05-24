import time


class CooldownManager:
    """Менеджер кулдаунов для создания каналов"""

    _PRUNE_EVERY = 256

    def __init__(self):
        self.cooldowns: dict[int, float] = {}
        self.cooldown_time = 5
        self._ops_since_prune = 0

    def _maybe_prune(self, now: float) -> None:
        self._ops_since_prune += 1
        if self._ops_since_prune < self._PRUNE_EVERY:
            return
        self._ops_since_prune = 0
        cutoff = now - self.cooldown_time
        self.cooldowns = {uid: ts for uid, ts in self.cooldowns.items() if ts > cutoff}

    def is_ready(self, user_id: int) -> bool:
        last = self.cooldowns.get(user_id, 0.0)
        return time.monotonic() - last >= self.cooldown_time

    def consume(self, user_id: int) -> None:
        now = time.monotonic()
        self.cooldowns[user_id] = now
        self._maybe_prune(now)

    def check_cooldown(self, user_id: int) -> bool:
        if not self.is_ready(user_id):
            return False
        self.consume(user_id)
        return True

    def remaining(self, user_id: int) -> float:
        last = self.cooldowns.get(user_id, 0.0)
        left = self.cooldown_time - (time.monotonic() - last)
        return max(0.0, left)
