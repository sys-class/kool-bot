# Deployment

## Архитектура

CD pipeline для kool-bot устроен так:

1. **CI** (`.github/workflows/ci.yml`) — линт + тесты на push/PR.
2. **CD** (`.github/workflows/cd.yml`) — на push в `main` или ручной запуск:
   - Ждёт успешного завершения CI (`wait-for-ci`).
   - Собирает Docker-образ и пушит в GitHub Container Registry (GHCR) с тегами `latest` и `<commit-sha>`.
   - По SSH заходит на прод-хост, делает `docker compose pull && docker compose up -d`.
   - Проверяет логи контейнера на признаки успешного подключения к Discord.
   - При фейле — автоматический rollback на предыдущий образ.
   - Шлёт уведомления в Discord webhook.

Образ: `ghcr.io/sys-class/kool-bot:<tag>`.

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

## Ручной деплой

GitHub → Actions → CD → Run workflow.

В поле `image_tag` можно указать конкретный тег (SHA коммита). Если оставить пустым — будет использован SHA текущего HEAD ветки `main`.

## Known limitations

- **`workflow_dispatch` с `image_tag` НЕ откатывается на старую сборку.** Текущий pipeline всегда выполняет `build-and-push` из чекаута `main` и тегает результат значением `image_tag`. Если указать туда SHA уже существующего образа — образ под этим тегом в GHCR будет перезаписан новой сборкой из текущего кода `main`, и на хост уедет именно она. Для настоящего отката используй ручной путь на сервере (см. ниже) либо временно откатывай сам `main` (revert-коммит) и дай pipeline отработать заново.
- `latest` всегда указывает на последнюю сборку из `main`, даже если запуск был ручным с другим `image_tag`.
- Healthcheck-регэксп зашит в `cd.yml` — при изменении формата стартовых логов бота нужно править workflow.

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

После `docker compose up -d` CD-скрипт ждёт 30 секунд и проверяет логи контейнера регэкспом:

```
Logged in as|Bot is ready|on_ready|готов к работе
```

Если бот не успевает залогиниться за 30 секунд или пишет в логи что-то другое — деплой считается провалившимся и происходит rollback. При изменении формата лог-сообщения о готовности бота нужно обновить регэксп в `.github/workflows/cd.yml`.
