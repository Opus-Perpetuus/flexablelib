#!/usr/bin/env python3
"""
Convierte la captura de record.sh en el MP4 final (1920x1080, H.264 + pista
AAC en silencio), con capítulos incrustados, y escribe la lista de capítulos
con marcas de tiempo para la descripción del video.

    python examples/video/render.py /tmp/flexablelib-video/captura.mkv \\
        salida.mp4 capitulos.txt
"""

import json
import os
import subprocess
import sys

NAMES = {
    0: 'Introducción',
    1: 'Tablas: estilos, bordes, combinadas, colores, exportar, streaming y paginación',
    2: 'Grid y layout',
    3: 'Widgets: ProgressBar, Sparkline, BarChart, StatusBar, LogView, Live/Screen',
    4: 'Componentes',
    5: 'App TUI con teclado, ratón y foco',
    6: 'Accesibilidad: alto contraste, daltonismo, NO_COLOR, lector de pantalla, ASCII',
    7: 'Folios e identificadores',
    8: 'Imágenes: kitty, sixel, bloques, braille, ASCII y respaldo',
    9: 'Aceleración C y benchmark',
    10: 'Cierre e instalación',
}


def stamp(seconds):
    seconds = int(round(seconds))
    m, s = divmod(seconds, 60)
    return '{0}:{1:02d}'.format(m, s)


def main(capture, output, chapters_txt):
    work = os.path.dirname(capture)
    log = json.load(open(os.path.join(work, 'tiempos.json')))
    ff_start = float(open(os.path.join(work, 'ffmpeg.start')).read())
    offset = log['start'] - ff_start          # demo t=0 inside the capture
    marks = log['chapters']
    start = max(0.0, offset + marks[0]['t'] - 0.3)
    # The closing card stays up for at most 11 s.
    end = offset + min(marks[-1]['t'], marks[-2]['t'] + 11) + 0.3
    duration = end - start
    chapters = [(m['t'] + offset - start, m['n']) for m in marks if m['n'] >= 0]
    chapters[0] = (0.0, chapters[0][1])
    meta = os.path.join(work, 'chapters.ffmeta')
    with open(meta, 'w') as f:
        f.write(';FFMETADATA1\ntitle=flexablelib — demo completa\n')
        for i, (t, n) in enumerate(chapters):
            t_end = chapters[i + 1][0] if i + 1 < len(chapters) else duration
            f.write('[CHAPTER]\nTIMEBASE=1/1000\nSTART={0}\nEND={1}\ntitle={2}\n'.format(
                int(t * 1000), int(t_end * 1000), NAMES.get(n, str(n))))
    subprocess.run([
        'ffmpeg', '-loglevel', 'error', '-y', '-ss', '{0:.3f}'.format(start),
        '-t', '{0:.3f}'.format(duration), '-i', capture,
        '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',
        '-i', meta, '-map', '0:v', '-map', '1:a', '-map_metadata', '2',
        '-map_chapters', '2', '-c:v', 'libx264', '-preset', 'slow', '-crf', '20',
        '-tune', 'stillimage', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
        '-r', '30', '-g', '60', '-c:a', 'aac', '-b:a', '96k', '-shortest',
        '-movflags', '+faststart', output], check=True)
    with open(chapters_txt, 'w') as f:
        for t, n in chapters:
            f.write('{0} {1}\n'.format(stamp(t), NAMES.get(n, str(n))))
    print('duración {0} · {1} capítulos'.format(stamp(duration), len(chapters)))


if __name__ == '__main__':
    main(*sys.argv[1:4])
