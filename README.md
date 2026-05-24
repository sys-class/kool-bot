# Kool Bot :3

[![CI](https://github.com/sys-class/kool-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/sys-class/kool-bot/actions/workflows/ci.yml)
[![CD](https://github.com/sys-class/kool-bot/actions/workflows/cd.yml/badge.svg)](https://github.com/sys-class/kool-bot/actions/workflows/cd.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPLv3%20%2F%20MIT-purple)](LICENSE-AGPLv3)

> nuh uh

Discord бот для одного сервера. Функции включают в себя: фан, модерация **(скоро)**, статистика, напоминания, авто-создание персональных войс-каналов и щепотка "акцента". Форк [`mixed-soup/kool-bot`](https://github.com/mixed-soup/kool-bot), переписанный на структуру `cogs/` + `services/`, с тестами, бенчмарком, ruff-линтом и CI/CD-пайплайном с healthcheck и rollback’ом.

-----

## ✨ Возможности

|Cog         |Что делает                                                                                    |
|------------|----------------------------------------------------------------------------------------------|
|`fun`       |Фан-команды: рейты, кубики, шар, монетка, выбор из списка, пинг                               |
|`moderation`|Очистка сообщений, массовый дисконнект из войса                                               |
|`utility`   |Справка, время в часовых поясах, аватар, отправка от имени бота                               |
|`voice`     |Авто-создание персональных каналов `/home/<user>` при заходе в hub-канал, авто-удаление пустых|
|`anonymous` |Анонимная отправка сообщения в канал через ЛС бота (через webhook)                            |
|`uwuify`    |Перехватывает сообщения отмеченных юзеров и пересылает их через webhook с феленидским акцентом|
|`social`    |Настроение пользователя, `whois`-карточка                                                     |
|`reminders` |Напоминания с парсингом `1h30m` / `2д` / `30мин`, лимиты, фоновая доставка                    |
|`stats`     |Пульс сервера: счётчик сообщений по часам с спарклайном, топ-каналы, retention 7 дней         |

Плюс пара пасхалок в `on_message`:

- триггер `ерп` (по границам кириллических слов) → `**Ну давай~ @user**`;
- зеркальный форвардинг между двумя текстовыми каналами через webhook с сохранением аватара и ника автора **(возможно сломан)**;

-----

## 🧰 Стек

- **Python** 3.11 / 3.12 / 3.13 (тестируется на всех трёх)
- [`discord.py`](https://github.com/Rapptz/discord.py) `>= 2.0` (slash-команды, cogs, tasks)
- `pytz` для часовых поясов, `python-dotenv` для конфига
- **Хранение:** атомарные JSON-файлы (`tempfile` + `os.fsync` + `os.replace`) — без БД
- **Тесты:** `pytest`, `pytest-asyncio`, `pytest-cov` → Codecov
- **Линт:** `ruff check` + `ruff format --check` (mypy сознательно выпилен — см. комментарий в `ci.yml`)
- **Деплой:** Docker → GHCR → SSH `docker compose pull && up -d` с healthcheck по логам и автоматическим rollback’ом

-----

## 🚀 Быстрый старт

### Через Docker (рекомендуется)

```bash
git clone https://github.com/sys-class/kool-bot.git
cd kool-bot
cp .env.example .env
# отредактируй .env и при необходимости config.py — см. ниже
docker build -t kool-bot .
docker run -d --name kool-bot --env-file .env -v $PWD/data:/app/data kool-bot
```

Или используй готовый образ из GHCR (если есть доступ):

```bash
docker pull ghcr.io/sys-class/kool-bot:latest
docker run -d --name kool-bot --env-file .env ghcr.io/sys-class/kool-bot:latest
```

### Локально

```bash
git clone https://github.com/sys-class/kool-bot.git
cd kool-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# отредактируй .env
python bot.py
```

-----

## ⚙️ Конфигурация

### Переменные окружения (`.env`)

|Переменная|Описание                                                                            |
|----------|------------------------------------------------------------------------------------|
|`TOKEN`   |Bot token из [Discord Developer Portal](https://discord.com/developers/applications)|

Шаблон лежит в `.env.example`.

### Хардкод в `config.py`

Бот заточен под один конкретный сервер, поэтому ID-шники прямо в коде. Если форкаешь то правь эти значения:

|Константа                             |Что это                                                                                                                                                                                               |
|--------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|`GUILD_ID`                            |ID основного гильдии для синка slash-команд                                                                                                                                                           |
|`ALLOWED_USERS`                       |Список user ID с админ-привилегиями (обход кулдауна, доступ к `/disconnect`)                                                                                                                          |
|`TARGET_VOICE_CHANNELS`               |`{guild_id: [hub_channel_id, ...]}` — войс-каналы, при заходе в которые бот создаёт персональный `/home/<user>`. Сидируется в `targets.json`, потом редактируется через `/addtarget` и `/removetarget`|
|`SOURCE_CHANNEL_1`, `SOURCE_CHANNEL_2`|Пара текстовых каналов для зеркального форвардинга через webhook                                                                                                                                      |
|`ANON_TARGET_CHANNEL_ID`              |Канал, куда падают анонимные сообщения от `/anonsay`                                                                                                                                                  |
|`timezones`                           |Словарь часовых поясов для `/time`                                                                                                                                                                    |

### Права у бота на сервере

Минимально нужно: `Send Messages`, `Manage Messages` (для `/clear` и `uwuify`-удаления), `Manage Webhooks`, `Connect`, `Move Members`, `Manage Channels` (для создания `/home/<user>`), `Read Message History`. Intents: `MESSAGE_CONTENT` и `GUILD_MEMBERS` (включены в коде, не забудь включить в Developer Portal).

-----

## 📜 Команды

Все команды — slash. Глобальный кулдаун 1 на пользователя (юзеры из `ALLOWED_USERS` его обходят).

### Общие

|Команда             |Описание                                                                         |
|--------------------|---------------------------------------------------------------------------------|
|`/help`             |Полный список команд, сгруппированный по cog’ам                                  |
|`/ping`             |Задержка до Discord Gateway                                                      |
|`/time`             |Текущее время в `мск` / `екб` / `ny`                                             |
|`/avatar [member]`  |Аватар пользователя                                                              |
|`/anonsay <message>`|Анонимная отправка через webhook в `ANON_TARGET_CHANNEL_ID`. **Только в ЛС бота**|

### Социальное

|Команда          |Описание                                                          |
|-----------------|------------------------------------------------------------------|
|`/whois [member]`|Карточка: дата создания / захода, верхняя роль, настроение, ID    |
|`/mood [text]`   |Установить настроение (до 40 символов). Пустой аргумент — сбросить|

### Фан

|Команда               |Описание                                                        |
|----------------------|----------------------------------------------------------------|
|`/furryrate [member]` |Процент фуррьки (детерминирован от `member.id`)                 |
|`/femboyrate [member]`|Процент фембойности (то же самое)                               |
|`/8ball <question>`   |Магический шар, 20 вариантов ответа                             |
|`/dice [roll]`        |Кубики в формате `NdM` (`N` 1–20, `M` 2–100). По умолчанию `1d6`|
|`/choose <options>`   |Выбор из списка через запятую (2–20 вариантов)                  |
|`/coinflip`           |Орёл / решка                                                    |

### Напоминания

|Команда                |Описание                                                                                                                                                                                           |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|`/remind <when> <text>`|Напоминание. `when` парсится как `30s` / `5m` / `2h` / `1d` / `1w` / `1h30m`, поддерживает русские суффиксы (`сек`, `мин`, `ч`, `д`, `нед`). Лимиты: 10 сек – 30 дней, до 500 символов, 25 на юзера|
|`/reminders`           |Список твоих напоминаний с ID                                                                                                                                                                      |
|`/forget <reminder_id>`|Удалить напоминание по ID из `/reminders`                                                                                                                                                          |

Доставка фоновая, тик каждые 15 секунд. Если канал недоступен — fallback в ЛС.

### Статистика

|Команда |Описание                                                                                                         |
|--------|-----------------------------------------------------------------------------------------------------------------|
|`/stats`|Пульс сервера: сообщения за 24ч (с unicode-спарклайном `▁▂▃▄▅▆▇█`), 7д, час пика, топ-3 каналов. Retention 7 дней|

### Модерация

|Команда                |Права            |Описание                                                 |
|-----------------------|-----------------|---------------------------------------------------------|
|`/clear [amount]`      |`Manage Messages`|Удаляет до `amount` (по умолчанию 10) последних сообщений|
|`/say <text>`          |`Manage Messages`|Отправляет сообщение от имени бота                       |
|`/disconnect <channel>`|`ALLOWED_USERS`  |Кикает всех из войс-канала                               |
|`/uwuify <member>`     |`Administrator`  |Включает/выключает "акцент" для пользователя             |

### Войс-каналы

|Команда                  |Права          |Описание                          |
|-------------------------|---------------|----------------------------------|
|`/targets`               |—              |Список hub-каналов на этом сервере|
|`/addtarget <channel>`   |`Administrator`|Добавить hub-канал                |
|`/removetarget <channel>`|`Administrator`|Удалить hub-канал                 |

При заходе участника в hub-канал бот создаёт ему персональный войс `/home/<username>` в той же категории и переносит туда. Создатель получает права mute/manage. Канал удаляется автоматически, когда пустеет (плюс фоновая чистка раз в 10 минут на случай пропущенных событий).

-----

## 💾 Хранение данных

Состояние пишется в JSON-файлы в рабочей директории. Запись **атомарная** — `tempfile.mkstemp` + `fsync` + `os.replace` (см. `services/storage.py`), чтобы крэш или kill -9 не оставил битый файл.

|Файл            |Cog        |Что внутри                                                                                       |
|----------------|-----------|-------------------------------------------------------------------------------------------------|
|`targets.json`  |`voice`    |`{guild_id: [hub_channel_id, ...]}`                                                              |
|`channels.json` |`voice`    |`{voice_channel_id: creator_user_id}` — каналы, созданные ботом, чтобы переживать рестарт        |
|`uwuified.json` |`uwuify`   |`{guild_id: [user_id, ...]}`                                                                     |
|`reminders.json`|`reminders`|Список объектов `{id, user_id, channel_id, due, text}`                                           |
|`mood.json`     |`social`   |`{guild_id: {user_id: mood_text}}`                                                               |
|`stats.json`    |`stats`    |`{guilds: {guild_id: {hours: {yyyymmddhh: count}, channels: {yyyymmddhh: {channel_id: count}}}}}`|

При деплое в Docker монтируй директорию с этими файлами как volume, иначе данные потеряются.

-----

## 🗂 Архитектура

```
.
├── bot.py                  # entry point, CoolBot(commands.Bot)
├── config.py               # ID-шники, токены, часовые пояса
├── bench.py                # синтетический бенч hot paths под cProfile
├── Dockerfile              # python:3.13-slim, непривилегированный юзер `bot`
├── requirements.txt
├── cogs/                   # фичи, каждая — отдельный Cog
│   ├── anonymous.py
│   ├── fun.py
│   ├── moderation.py
│   ├── reminders.py
│   ├── social.py
│   ├── stats.py
│   ├── utility.py
│   ├── uwuify.py
│   └── voice.py
├── services/               # переиспользуемая инфраструктура
│   ├── cooldown.py         # CooldownManager с периодической чисткой
│   ├── embeds.py           # фабрика эмбедов (info/err/ok/...) + bar()
│   ├── storage.py          # атомарный read_json/write_json
│   └── webhook.py          # кэш вебхуков, прокси-отправка от имени автора
├── tests/                  # pytest
├── docs/
│   └── DEPLOYMENT.md       # CI/CD, секреты, rollback
├── .github/workflows/
│   ├── ci.yml              # ruff + pytest matrix
│   └── cd.yml              # build → GHCR → SSH deploy
├── LICENSE-AGPLv3
└── LICENSE-MIT
```

Каждый cog подключается явно в `CoolBot.setup_hook()`. В `bot.py` также висит глобальный `interaction_check` на дереве команд — кулдаун из `services.cooldown.CooldownManager` (5 секунд), который пропускает `ALLOWED_USERS`.

-----

## 🧪 Разработка

### Запуск тестов

```bash
pip install pytest pytest-asyncio pytest-cov
pytest tests/ -v --cov=. --cov-report=term
```

В CI прогоняется матрица 3.11 / 3.12 / 3.13, coverage с 3.13 заливается в Codecov.

### Линт и форматирование

```bash
pip install ruff
ruff check .
ruff format --check .
# или с фиксом:
ruff check --fix .
ruff format .
```

### Бенчмарк

`bench.py` гоняет `felinid_accent`, `CooldownManager`, `is_uwuified`, async-сохранение и `on_message`-маппинг под `cProfile`. Discord не дёргается, токен мокается. Удобно для сравнения до/после оптимизаций:

```bash
python bench.py
```

### Добавить новый cog

1. Создать `cogs/<name>.py` с классом-наследником `commands.Cog` и `async def setup(bot)`.
1. Зарегистрировать в `CoolBot.setup_hook()` через `await self.load_extension("cogs.<name>")`.
1. Если будет в `/help` — добавить отображаемое имя в `UtilityCog.COG_DISPLAY`.
1. Эмбеды строить через `services.embeds` (`info` / `err` / `ok` / `fun` / `mod` / `voice` — это семантические алиасы одного цвета, чтобы код читался по месту вызова).
1. Если нужно персистентное состояние — `services.storage.read_json` / `write_json`.

-----

## 🚢 Деплой

CD пайплайн собирает образ на каждый push в `main`, пушит в `ghcr.io/sys-class/kool-bot`, заходит по SSH на прод-хост, делает `docker compose pull && up -d`, ждёт 30 секунд и проверяет логи на признаки успешного старта. Если healthcheck не прошёл — автоматический rollback на образ, который крутился до этого, плюс уведомление в Discord-вебхук.

Подробности (секреты, структура `/opt/kool-bot/` на хосте, ручной rollback, добавление env vars) — в [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

-----

## Notice

This project as a whole is licensed under the [GNU Affero General Public License v3.0](LICENSE-AGPLv3).

It is a derivative work of the original [`mixed-soup/kool-bot`](https://github.com/mixed-soup/kool-bot) project, which is distributed under the [MIT License](https://raw.githubusercontent.com/mixed-soup/kool-bot/refs/heads/main/LICENSE). The original MIT license and copyright notice are retained for the portions of code derived from that project.

Modifications and additions made in this fork are licensed under AGPLv3. If you distribute this software or run it as a network service, you must comply with the terms of the AGPLv3, including providing access to the corresponding source code.