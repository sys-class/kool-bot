FROM python:3.13-slim

RUN useradd --create-home --uid 1000 --shell /bin/bash bot

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R bot:bot /app

USER bot

CMD ["python", "bot.py"]
