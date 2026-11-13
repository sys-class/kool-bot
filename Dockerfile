# базовый образ закреплён по digest, а не только по тегу: тег 3.13-slim
# подвижный, digest гарантирует тот же самый образ при каждой сборке
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

RUN useradd --create-home --uid 1000 --shell /bin/bash bot

WORKDIR /app

COPY requirements.txt ./
# pip в рантайме не нужен, а его вендоренные msgpack/urllib3/setuptools
# trivy ловит как HIGH — сносим после установки зависимостей
RUN pip install --no-cache-dir --require-hashes -r requirements.txt \
    && pip uninstall -y pip

COPY . .

# каталог состояния (сюда монтируется volume), владелец — пользователь bot
RUN mkdir -p /app/data && chown -R bot:bot /app

USER bot

# реальный healthcheck вместо грепа логов: проверяет свежесть heartbeat-файла,
# который пишет живой процесс бота (см. services/health.py)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "healthcheck.py"]

CMD ["python", "bot.py"]
