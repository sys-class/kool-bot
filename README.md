# kool-bot

Отдельное спасибо [`mixed-soup/kool-bot`](https://github.com/mixed-soup/kool-bot) за исходный код, за то что вообще выложили бота в открытый доступ, и просто за то что создатель хороший человек. Без них этой репы никогда не было бы.

---

Дискорд бот под один конкретный сервер (в будущем исправим).

Умеет многое - смотри код.

## запуск

Через докер:

```bash
git clone https://github.com/sys-class/kool-bot.git
cd kool-bot
cp .env.example .env  # вписать TOKEN
docker build -t kool-bot .
docker run -d --name kool-bot --env-file .env -v $PWD/data:/app/data kool-bot
```

Локально:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## для любителей форков

Бот заточен под конкретный сервер, поэтому id-шники лежат прямо в `config.py`. Открываешь и правишь под свой сервер.

Из прав на сервере боту нужна отправка сообщений, управление сообщениями и вебхуками, подключение к войсу, перемещение участников, управление каналами. Из интентов надо `MESSAGE_CONTENT` и `GUILD_MEMBERS`.

## данные

Состояние лежит в json-файлах в рабочей директории, запись атомарная (см. `services/storage.py`), без баз данных. Если катаешь в докере, то желательно монтируй директорию как volume, иначе всё потеряется при пересоздании контейнера

## разработка

Не забудь запустить тесты, чтобы поймать ошибки до того как они дойдут в CI:

```bash
pytest tests/ -v --cov=.
ruff check . && ruff format --check .
python bench.py  # бенч горячих путей под cProfile
```

CI проверяет на 3.11 / 3.12 / 3.13. Продакшн на 3.13.

---

## Notice

This project as a whole is licensed under the [GNU Affero General Public License v3.0](LICENSE-AGPLv3).

It is a derivative work of the original [`mixed-soup/kool-bot`](https://github.com/mixed-soup/kool-bot) project, which is distributed under the [MIT License](https://raw.githubusercontent.com/mixed-soup/kool-bot/refs/heads/main/LICENSE). The original MIT license and copyright notice are retained for the portions of code derived from that project.

Modifications and additions made in this fork are licensed under AGPLv3. If you distribute this software or run it as a network service, you must comply with the terms of the AGPLv3, including providing access to the corresponding source code.
