#!/usr/bin/env bash
set -euo pipefail

WIDTH="${SCREEN_WIDTH:-1920}"
HEIGHT="${SCREEN_HEIGHT:-1080}"
export DISPLAY="${DISPLAY:-:99}"

mkdir -p /data/profile /data/work /tmp/runtime
chmod 700 /data/profile

Xvfb "$DISPLAY" -screen 0 "${WIDTH}x${HEIGHT}x24" -ac +extension RANDR +extension GLX &
sleep 0.4
openbox >/tmp/openbox.log 2>&1 &
x11vnc -display "$DISPLAY" -forever -shared -rfbport 5900 -nopw -xkb -repeat -ncache 10 >/tmp/x11vnc.log 2>&1 &

NOVNC_WEB="/usr/share/novnc"
if [[ ! -d "$NOVNC_WEB" ]]; then
  NOVNC_WEB="/usr/share/novnc/utils/.."
fi
websockify --web="$NOVNC_WEB" 6080 127.0.0.1:5900 >/tmp/novnc.log 2>&1 &

exec python -m agent.main
