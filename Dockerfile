FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DISPLAY=:99

WORKDIR /app

# Chromium (usado por Scrapling/Playwright) más la pantalla virtual que se
# comparte con noVNC. El navegador sigue siendo headed para que el usuario
# pueda resolver un CAPTCHA desde la aplicación web.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        fonts-liberation \
        fonts-noto-color-emoji \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libglib2.0-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libx11-6 \
        libx11-xcb1 \
        libxcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        novnc \
        openbox \
        websockify \
        x11vnc \
        xauth \
        xdg-utils \
        xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn \
    && scrapling install

COPY . ./
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 5000 6080

ENTRYPOINT ["/app/docker-entrypoint.sh"]
