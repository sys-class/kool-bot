import asyncio


class CooldownManager:
    """Менеджер кулдаунов для создания каналов"""
    def __init__(self):
        self.cooldowns = {}
        self.cooldown_time = 5

    def check_cooldown(self, user_id: int) -> bool:
        current_time = asyncio.get_event_loop().time()
        last_time = self.cooldowns.get(user_id, 0)

        if current_time - last_time < self.cooldown_time:
            return False

        self.cooldowns[user_id] = current_time
        return True
