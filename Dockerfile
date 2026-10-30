# базовый образ закреплён по digest, а не только по тегу: тег 3.13-slim
# подвижный, digest гарантирует тот же самый образ при каждой сборке
FROM python:3.14-slim@sha256:cd89c30eda26ee911a4611b18680086e0ea42e6f5f8cbe653d07fa7958c9cec8

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
