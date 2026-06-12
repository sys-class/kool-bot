# базовый образ закреплён по digest, а не только по тегу: тег 3.13-slim
# подвижный, digest гарантирует тот же самый образ при каждой сборке
FROM python:3.13-slim@sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74

RUN useradd --create-home --uid 1000 --shell /bin/bash bot

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

COPY . .

# каталог состояния (сюда монтируется volume), владелец — пользователь bot
RUN mkdir -p /app/data && chown -R bot:bot /app

USER bot

# реальный healthcheck вместо грепа логов: проверяет свежесть heartbeat-файла,
# который пишет живой процесс бота (см. services/health.py)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "healthcheck.py"]

CMD ["python", "bot.py"]
