import os
from pathlib import Path

import pytz
from dotenv import load_dotenv

load_dotenv()


def _load_token() -> str:
    # TOKEN_FILE — путь к файлу с токеном (docker secret). имеет приоритет
    # над переменной TOKEN, чтобы секрет не светился в /proc/1/environ и
    # в выводе docker inspect. если файл задан, но не читается — возвращаем
    # пустую строку: бот упадёт с понятной ошибкой, а не уедет на старый
    # токен из окружения
    token_file = os.getenv("TOKEN_FILE")
    if token_file:
        try:
            return Path(token_file).read_text(encoding="utf-8").strip()
        except OSError:
            return ""
    return os.getenv("TOKEN", "")


TOKEN = _load_token()

# каталог для json-состояния бота. в докере сюда примонтирован volume
# (./data:/app/data), поэтому пишем именно туда, иначе состояние стирается
# при каждом пересоздании контейнера
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

# уровень логов для разработчиков: DEBUG / INFO / WARNING / ERROR (WARN тоже ок).
# на проде ставим повыше, локально опускаем до DEBUG. парсится в services.logger
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# дублирование логов эмбедами в дискан. вебхук бот заводит сам, поэтому в
# окружении только id канала и уровень (по умолчанию шлём от WARNING и выше).
# LOG_PING_USER_ID пингуется на ERROR и выше
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "1496392803092271204"))
DISCORD_LOG_LEVEL = os.getenv("DISCORD_LOG_LEVEL", "WARNING")
LOG_PING_USER_ID = 587208453018091538

GUILD_ID = 1496231771602419772
ALLOWED_USERS = [1043834316620304394, 587208453018091538]  # дискорд юзер айди

TARGET_VOICE_CHANNELS = {
    1496231771602419772: [1507420233101475901],  # voice
}

SOURCE_CHANNEL_1 = 1507418571809230958  # message forwarding
SOURCE_CHANNEL_2 = 1507418580667601088  # message forwarding

ANON_TARGET_CHANNEL_ID = 1499015391991566428

timezones = {
    "msk": pytz.timezone("Europe/Moscow"),
    "ekb": pytz.timezone("Asia/Yekaterinburg"),
    "ny": pytz.timezone("America/New_York"),
}
