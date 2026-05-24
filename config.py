import os

import pytz
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN", "")
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
