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
- `data/` — состояние бота (json-файлы, heartbeat). Принадлежит `1000:1000`.
- `secrets/bot_token` — токен Discord одним файлом (без перевода строки). `0400`, владелец `1000:1000` — контейнер работает от uid 1000, а compose-секрет в не-swarm режиме это bind mount, который сохраняет права хостового файла.

Контейнер должен называться `kool-bot` (`container_name: kool-bot` в compose).

Токен передаётся как docker secret: compose монтирует `secrets/bot_token` в `/run/secrets/bot_token`, а переменная `TOKEN_FILE=/run/secrets/bot_token` говорит боту читать его из файла (`config.py`). Раньше токен жил в `.env` и торчал в `/proc/1/environ` и `docker inspect`; `env_file` из compose убран.

Состояние бота (json-файлы) пишется в `DATA_DIR` (по умолчанию `/app/data`), куда монтируется volume `./data:/app/data`. Каталог должен быть доступен на запись пользователю `bot` (uid 1000). Раньше бот писал в `/app` и состояние стиралось при каждом пересоздании контейнера.

Сервис в compose захарднен: `read_only: true` (единственные записываемые пути — volume `/app/data` и tmpfs `/tmp`), `cap_drop: [ALL]`, `no-new-privileges:true`, `pids_limit`, `mem_limit`. При добавлении новых путей записи в коде это нужно учитывать.

Опорный вид сервиса (host-конфиг, в репе не лежит):

```yaml
services:
  kool-bot:
    image: ghcr.io/sys-class/kool-bot:latest
    container_name: kool-bot
    restart: unless-stopped
    secrets:
      - bot_token
    environment:
      - TOKEN_FILE=/run/secrets/bot_token
    volumes:
      - ./data:/app/data
    read_only: true
    tmpfs:
      - /tmp
    cap_drop: [ALL]
    security_opt:
      - no-new-privileges:true
    pids_limit: 256
    mem_limit: 512m

secrets:
  bot_token:
    file: ./secrets/bot_token
```

## Ручной деплой

GitHub → Actions → CD → Run workflow.

В поле `image_tag` нужно указать конкретный тег (SHA коммита) уже существующего образа. Ручной запуск НЕ пересобирает код — он только повторно раскатывает указанный образ (это и есть откат). Поэтому поле обязательное.

## Модель тегов (принятое решение)

Прод-`docker-compose.yml` намеренно остаётся на `image: ...:latest`. Локальный тег `latest` на хосте — это указатель, которым управляет только CD: перед `up` он тянет ровно собранный образ по неизменяемому digest (на push) или по SHA-тегу (на dispatch) и перевешивает на него локальный `latest`. Registry-side `latest` на хост не попадает.

Альтернатива (compose закреплён на `@sha256:...`) отвергнута: тогда каждый деплой должен переписывать `image:` в host-конфиге, и рассинхрон CD со скриптом на хосте навсегда пиннил бы старый образ.

Следствие: для воспроизводимости раскатки опирайся на SHA-тег/digest из CD-логов, а не на `latest` в registry.

## Откат

### Через workflow_dispatch (рекомендуется)

1. Открыть https://github.com/sys-class/kool-bot/pkgs/container/kool-bot — найти предыдущий рабочий SHA.
2. Actions → CD → Run workflow → указать этот SHA в `image_tag`.

### Руками на сервере

```bash
ssh -p <DEPLOY_PORT> deploy@<DEPLOY_HOST>
cd /opt/kool-bot
# перевесить локальный latest на нужный образ, как это делает CD
docker pull ghcr.io/sys-class/kool-bot:<good-sha>
docker tag ghcr.io/sys-class/kool-bot:<good-sha> ghcr.io/sys-class/kool-bot:latest
docker compose up -d --force-recreate
docker logs kool-bot --tail 50
```

CD при фейле healthcheck откатывается сам: id предыдущего образа он запоминает через `docker inspect` перед раскаткой.

## Добавление новых переменных окружения

1. На хосте: добавить переменную в секцию `environment:` сервиса в `/opt/kool-bot/docker-compose.yml` (секреты — отдельными файлами через `secrets:`, по образцу `bot_token`).
2. Перезапустить: `cd /opt/kool-bot && docker compose up -d --force-recreate`.
3. Обновить `.env.example` в репе для документирования (без значения) — локально бот по-прежнему читает `.env`.

Если переменная нужна на этапе сборки (build args) — добавлять через Dockerfile + workflow, не через `.env`.

## Healthcheck

Образ содержит `HEALTHCHECK`, который запускает `healthcheck.py` и проверяет свежесть heartbeat-файла (`DATA_DIR/.heartbeat`). Живой процесс бота перезаписывает его каждые 30 секунд (`services/health.py`), пока открыто соединение с гейтвеем; если отметка старше 90 секунд — контейнер считается `unhealthy`.

CD-скрипт после `docker compose up -d` опрашивает `docker inspect kool-bot --format '{{.State.Health.Status}}'` и ждёт `healthy`. Раньше healthcheck грепал логи на строку готовности — её мог напечатать любой образ, поэтому проверка не отражала реальную живость и не давала откату сработать.
