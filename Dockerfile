FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends chromium chromium-driver fonts-liberation fonts-noto-color-emoji ca-certificates tini && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN mkdir -p /data/chrome-profile && useradd -m -u 10001 bot && chown -R bot:bot /app /data
USER bot
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "app.main"]
