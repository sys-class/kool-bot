# Deployment

## Архитектура

CD pipeline для kool-bot устроен так:

1. **CI** (`.github/workflows/ci.yml`) — линт + тесты на push/PR.
2. **CD** (`.github/workflows/cd.yml`) — на push в `main` или ручной запуск:
   - Ждёт успешного завершения CI (`wait-for-ci`).
   - Собирает Docker-образ и пушит в GitHub Container Registry (GHCR) с тегами `latest` и `<commit-sha>`.
   - По SSH заходит на прод-хост, тянет образ по неизменяемому digest той сборки (`docker pull ...@sha256:...`), перевешивает на него локальный тег `latest` и делает `docker compose up -d --force-recreate`.
   - Проверяет состояние контейнера через `docker inspect ... .State.Health.Status` (образ отдаёт HEALTHCHECK по живому heartbeat процесса).
   - При фейле — автоматический rollback на предыдущий образ.
   - Шлёт уведомления в Discord webhook.

3. **Security** (`.github/workflows/security.yml`, `codeql.yml`) — секрет-скан (gitleaks), скан зависимостей и образа (trivy), статанализ (CodeQL). Обновления зависимостей и экшенов — через `dependabot.yml`.

Образ: `ghcr.io/sys-class/kool-bot:<tag>`. Все сторонние GitHub Actions закреплены по commit-SHA, базовый образ в `Dockerfile` — по digest, python-зависимости пиннятся с хешами в `requirements.txt` (из `requirements.in`).

## GitHub Secrets

| Secret | Назначение |
|---|---|
| `DEPLOY_HOST` | IP/hostname прод-сервера |
| `DEPLOY_USER` | SSH-юзер для деплоя (обычно `deploy`) |
| `DEPLOY_PORT` | SSH-порт (нестандартный) |
| `DEPLOY_SSH_KEY` | Приватный SSH-ключ (PEM) |
| `DISCORD_WEBHOOK` | Webhook URL для уведомлений о деплое |
| `CODECOV_TOKEN` | Токен Codecov (используется в CI) |

`GITHUB_TOKEN` создаётся автоматически — отдельно настраивать не нужно.

## Что лежит на хосте

В `/opt/kool-bot/`:

- `docker-compose.yml` — host-specific конфиг, тянет образ из GHCR. В репу НЕ коммитится.
- `.env` — секреты бота (токен Discord и т.п.). В репу НЕ коммитится.
- `.last-known-good` — создаётся CD-скриптом, хранит имя предыдущего образа (для rollback).

Контейнер должен называться `kool-bot` (`container_name: kool-bot` в compose).

Состояние бота (json-файлы) пишется в `DATA_DIR` (по умолчанию `/app/data`), куда монтируется volume `./data:/app/data`. Каталог должен быть доступен на запись пользователю `bot` (uid 1000). Раньше бот писал в `/app` и состояние стиралось при каждом пересоздании контейнера.

## Ручной деплой

GitHub → Actions → CD → Run workflow.

В поле `image_tag` нужно указать конкретный тег (SHA коммита) уже существующего образа. Ручной запуск НЕ пересобирает код — он только повторно раскатывает указанный образ (это и есть откат). Поэтому поле обязательное.

## Known limitations

- `latest` на прод-хосте перевешивается CD на digest текущей раскатки. На стороне registry тег `latest` по-прежнему указывает на последнюю сборку из `main` — для воспроизводимости раскатки опирайся на SHA-тег/digest, а не на `latest`.
- Прод-`docker-compose.yml` тянет образ по тегу `latest` (CD ретегает его локально на нужный digest перед `up`). Полное закрепление по digest на стороне compose требует правок host-конфига в `/opt/kool-bot/` (вне репозитория).

## Откат

### Через workflow_dispatch (рекомендуется)

1. Открыть https://github.com/sys-class/kool-bot/pkgs/container/kool-bot — найти предыдущий рабочий SHA.
2. Actions → CD → Run workflow → указать этот SHA в `image_tag`.

### Руками на сервере

```bash
ssh -p <DEPLOY_PORT> deploy@<DEPLOY_HOST>
cd /opt/kool-bot
docker compose down
# править docker-compose.yml: image: ghcr.io/sys-class/kool-bot:<good-sha>
docker compose pull
docker compose up -d
docker logs kool-bot --tail 50
```

Либо использовать `.last-known-good`:

```bash
cd /opt/kool-bot
PREV=$(cat .last-known-good)
sed -i "s|image: .*|image: $PREV|" docker-compose.yml
docker compose up -d
```

## Добавление новых переменных окружения

1. На хосте: добавить переменную в `/opt/kool-bot/.env`.
2. Убедиться, что в `docker-compose.yml` сервис её подхватывает (`env_file: .env` или `environment:` секция).
3. Перезапустить: `cd /opt/kool-bot && docker compose up -d`.
4. Обновить `.env.example` в репе для документирования (без значения).

Если переменная нужна на этапе сборки (build args) — добавлять через Dockerfile + workflow, не через `.env`.

## Healthcheck

Образ содержит `HEALTHCHECK`, который запускает `healthcheck.py` и проверяет свежесть heartbeat-файла (`DATA_DIR/.heartbeat`). Живой процесс бота перезаписывает его каждые 30 секунд (`services/health.py`), пока открыто соединение с гейтвеем; если отметка старше 90 секунд — контейнер считается `unhealthy`.

CD-скрипт после `docker compose up -d` опрашивает `docker inspect kool-bot --format '{{.State.Health.Status}}'` и ждёт `healthy`. Раньше healthcheck грепал логи на строку готовности — её мог напечатать любой образ, поэтому проверка не отражала реальную живость и не давала откату сработать.
