#!/bin/sh
set -eu

# Xvfb mantiene una pantalla persistente. Esto permite que x11vnc y Chromium
# compartan la misma sesión durante todo el trabajo de scraping.
Xvfb :99 -screen 0 "${SCREEN_RESOLUTION:-1440x900x24}" -nolisten tcp &
openbox-session >/tmp/openbox.log 2>&1 &

# El servidor VNC sólo escucha dentro del contenedor; noVNC es el único
# componente que se publica y lo reenvía a través de WebSocket.
x11vnc -display :99 -localhost -forever -shared -nopw -rfbport 5900 \
  >/tmp/x11vnc.log 2>&1 &
websockify --web=/usr/share/novnc 6080 localhost:5900 \
  >/tmp/novnc.log 2>&1 &

exec gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 4 run:app
