import time


class CooldownManager:
    """Менеджер кулдаунов для создания каналов"""
    def __init__(self):
        self.cooldowns: dict[int, float] = {}
        self.cooldown_time = 5

    def check_cooldown(self, user_id: int) -> bool:
        now = time.monotonic()
        last = self.cooldowns.get(user_id, 0.0)

        if now - last < self.cooldown_time:
            return False

        self.cooldowns[user_id] = now
        return True
