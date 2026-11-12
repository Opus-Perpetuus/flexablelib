"""
Child process for the real Windows console test (tests/test_v340_input.py).

Runs in a console of its own (CREATE_NEW_CONSOLE): injects input records with
WriteConsoleInputW, reads them back through flexablelib_tui (raw records,
virtual-terminal input mode and the Terminal class) and writes what it saw
to the JSON file named on the command line.
"""

import ctypes
import json
import sys
import time
import traceback


def conin():
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateFileW.restype = ctypes.c_void_p
    handle = kernel32.CreateFileW('CONIN$', 0xC0000000, 3, None, 3, 0, None)
    return handle


def drain(console, translator, want, seconds=5.0):
    keys = []
    deadline = time.monotonic() + seconds
    while len(keys) < want and time.monotonic() < deadline:
        keys.extend(translator.feed(console.read(0.2)))
        if translator.pending and not console.pending():
            keys.extend(translator.flush())
    return keys


def main(path):
    from flexablelib_tui import Terminal, wincon
    result = {}
    handle = conin()
    writer = wincon.ConsoleInput(handle=handle)

    # 1. Raw records: what we write is what ReadConsoleInputW returns.
    records = [('key', True, 1, 0x41, 'a', 0),
               ('key', True, 1, 0x26, '', wincon.LEFT_CTRL),
               ('key', True, 1, 0x7C, '', 0),
               ('key', True, 1, 0x09, '\t', wincon.SHIFT),
               ('mouse', 4, 2, 1, 0, 0), ('mouse', 4, 2, 0, 0, 0),
               ('mouse', 4, 2, 120 << 16, 0, wincon.MOUSE_WHEELED),
               ('size', 100, 30), ('focus', True)]
    reader = wincon.ConsoleInput(handle=handle)
    result['start_records'] = reader.start(mouse=True, vt=False)
    reader.read(0)                       # drop anything queued at startup
    writer.write(records)
    got = []
    deadline = time.monotonic() + 5
    while len(got) < len(records) and time.monotonic() < deadline:
        got.extend(reader.read(0.2))
    result['records'] = [list(r) for r in got
                         if r[0] in ('key', 'mouse', 'size', 'focus')]
    result['expected_records'] = [list(r) for r in records]
    translator = wincon.ConsoleInputTranslator()
    result['translated'] = [str(k) for k in translator.feed(got)]
    reader.stop()

    # 2. Virtual-terminal input mode (falls back to records if unsupported).
    reader = wincon.ConsoleInput(handle=handle)
    result['start_vt'] = reader.start(mouse=False, vt=True)
    result['vt_supported'] = reader.vt
    reader.read(0)
    writer.write([('key', True, 1, 0x26, '', 0), ('key', False, 1, 0x26, '', 0),
                  ('key', True, 1, 0x42, 'b', 0), ('key', False, 1, 0x42, 'b', 0),
                  ('key', True, 1, 0x70, '', wincon.SHIFT)])
    translator = wincon.ConsoleInputTranslator(vt=reader.vt)
    result['vt_keys'] = [str(k) for k in drain(reader, translator, 3)]
    result['expected_vt'] = ['up', 'b', 'shift+f1']
    reader.stop()

    # 3. The Terminal class on the process's own console stdin.
    with Terminal(mouse=True) as term:
        result['terminal_protocol'] = term.protocol
        term.read_keys(timeout=0.05)
        writer.write([('key', True, 1, 0x26, '', wincon.LEFT_CTRL),
                      ('key', True, 1, 0x87, '', 0),
                      ('key', True, 1, 0x43, '\x03', wincon.LEFT_CTRL),
                      ('mouse', 3, 1, 1, 0, 0), ('mouse', 3, 1, 0, 0, 0)])
        keys = []
        deadline = time.monotonic() + 5
        while len(keys) < 5 and time.monotonic() < deadline:
            keys.extend(term.read_keys(timeout=0.2))
        result['terminal'] = [str(k) for k in keys]
        result['terminal_raw'] = [repr(getattr(k, 'raw', '')) for k in keys]
        result['terminal_mouse'] = [list(k.mouse) for k in keys if k.mouse]
    # Windows' VT input mode has no sequences for F13-F24 (conhost drops
    # them), so those keys only arrive through records mode (part 4).
    expected = ['ctrl+up', 'f24', 'ctrl+c', 'mouse', 'mouse']
    if result['terminal_protocol'] == 'windows-vt':
        expected.remove('f24')
    result['expected_terminal'] = expected

    # 4. The Terminal class forced to console records.
    with Terminal(mouse=True, windows='records') as term:
        result['records_protocol'] = term.protocol
        term.read_keys(timeout=0.05)
        writer.write([('key', True, 1, 0x87, '', 0),
                      ('key', True, 1, 0x26, '', wincon.SHIFT),
                      ('mouse', 4, 2, 1, 0, 0)])
        keys = []
        deadline = time.monotonic() + 5
        while len(keys) < 3 and time.monotonic() < deadline:
            keys.extend(term.read_keys(timeout=0.2))
        result['records_terminal'] = [str(k) for k in keys]
    result['expected_records_terminal'] = ['f24', 'shift+up', 'mouse']
    return result


if __name__ == '__main__':
    out = sys.argv[1]
    try:
        data = main(out)
        code = 0
    except Exception:
        data = {'error': traceback.format_exc()}
        code = 1
    with open(out, 'w', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=1)
    sys.exit(code)
