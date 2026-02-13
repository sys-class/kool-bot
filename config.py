import pytz

TOKEN = "" # nuh uh
ALLOWED_USERS = [587208453018091538, 890939158279884827, 1043834316620304394]  # дискорд юзер айди

TARGET_VOICE_CHANNELS = {
    1269661143400714240: [1329890064569729124], # voice
    1454496288677560373: [1454500792022339584], # voice
}

SOURCE_CHANNEL_1 = 1411253833144733696 # message forwarding
SOURCE_CHANNEL_2 = 1330134606141329471 # message forwarding

ANON_TARGET_CHANNEL_ID = 1471935892032716904

timezones = {
    "msk": pytz.timezone("Europe/Moscow"),
    "ekb": pytz.timezone("Asia/Yekaterinburg"),
    "ny": pytz.timezone("America/New_York"),
}
