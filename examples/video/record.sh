#!/bin/bash
# Graba el video demo: pantalla virtual 1920x1080 (Xvfb), kitty con el tema
# de kitty.conf ejecutando demo.py, y ffmpeg capturando la pantalla.
#
#   examples/video/record.sh [salida.mkv] [opciones de demo.py]
#
# Necesita Xvfb, kitty, xterm, xdotool y ffmpeg. La salida es una captura
# sin pérdidas visibles (x264 ultrafast); render.sh la convierte al MP4 final.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
OUT=${1:-/tmp/flexablelib-video/captura.mkv}; shift || true
DISP=${DISPLAY_NUM:-:79}
WORK=$(dirname "$OUT"); mkdir -p "$WORK"
SOCK=unix:$WORK/kitty.sock
rm -f "$WORK/kitty.sock" "$WORK/demo.done"

if ! xdpyinfo -display "$DISP" >/dev/null 2>&1; then
  Xvfb "$DISP" -screen 0 1920x1080x24 -ac +extension GLX +render -noreset >/dev/null 2>&1 &
  sleep 1
fi
export DISPLAY=$DISP
export PYTHONPATH=$ROOT:$ROOT/packages/tui:$ROOT/packages/components:$ROOT/packages/speedups
unset NO_COLOR FORCE_COLOR COLUMNS LINES
export LANG=C.UTF-8 KITTY_LISTEN_ON=$SOCK
# "python" en los comandos tecleados: el python3 del sistema si no hay otro.
if ! command -v python >/dev/null; then
  mkdir -p "$WORK/bin"; ln -sf "$(command -v python3)" "$WORK/bin/python"
  export PATH=$WORK/bin:$PATH
fi

cat > "$WORK/inner.sh" <<INNER
#!/bin/bash
cd "$ROOT"
sleep 1.5
python3 examples/video/demo.py --log "$WORK/tiempos.json" $*
touch "$WORK/demo.done"
INNER
chmod +x "$WORK/inner.sh"

date +%s.%N > "$WORK/ffmpeg.start"
ffmpeg -loglevel error -y -f x11grab -framerate 30 -video_size 1920x1080 -draw_mouse 1 \
  -i "$DISP" -c:v libx264 -preset ultrafast -crf 14 -pix_fmt yuv444p "$OUT" &
FF=$!
sleep 0.5
LIBGL_ALWAYS_SOFTWARE=1 kitty --config "$HERE/kitty.conf" --listen-on "$SOCK" \
  -o allow_remote_control=yes "$WORK/inner.sh" >"$WORK/kitty.log" 2>&1 &
KP=$!
while [ ! -f "$WORK/demo.done" ] && kill -0 $KP 2>/dev/null; do sleep 1; done
sleep 0.5
kill -INT $FF; wait $FF || true
kill $KP 2>/dev/null || true
echo "captura: $OUT"
