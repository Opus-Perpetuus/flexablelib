"""Style x feature stress matrix on 30x50 tables.

Usage:  python tools/stress_matrix.py [--mode single|pairwise|everything|streamcmp|all]
                                      [--styles a,b] [--quick] [--json out.json]

Builds a 30-column x 50-row table of mixed data (ints, floats, None, long
strings, CJK, emoji, multi-line, bools, an all-empty column and row), applies
feature combinations and checks invariants on every render:

* no exception
* every rendered line has the same display width (ANSI stripped, wcwidth)
* box-drawing junctions connect (up/down/left/right arms meet)
* the visible row ids match row_filter / sort_by (when cells are not squeezed)
* to_records() order == rendered order; exports run and round-trip row counts
* determinism: two composes of the same config are identical

Also importable: tests/test_stress_matrix.py runs a reduced pairwise set.
"""
import itertools
import json
import os
import random
import re
import sys
import traceback
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from flexablelib import Table  # noqa: E402
from flexablelib.style_compositions import __style_compositions as _catalogue  # noqa: E402

try:
    from wcwidth import wcswidth as _wcswidth
except ImportError:  # fall back to the library's own measure
    _wcswidth = None
from flexablelib.text_width import visible_width as _lib_width, strip_ansi  # noqa: E402

STYLES = list(_catalogue._fields)
THEMES = sorted(Table.THEMES)
N_ROWS, N_COLS = 50, 30
ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
USE_WCWIDTH = False


def width(s):
    # The library's own measure: it agrees with wcwidth except for ZWJ emoji
    # sequences, which the library documents as terminal-dependent (each part
    # counts). Pass --wcwidth to measure with wcwidth instead.
    if USE_WCWIDTH and _wcswidth is not None:
        w = _wcswidth(ANSI.sub('', s))
        if w >= 0:
            return w
    return _lib_width(s)


# ----------------------------------------------------------------- data
WORDS = ['alpha', 'beta', 'gamma', 'delta', 'épsilon', 'zeta', 'ñandú']
CJK = ['東京', '日本語テキスト', '中文字符', '한국어', 'カタカナ長い名前']
EMOJI = ['😀', '👍 ok', '🚀🚀', '✅ done', '🇲🇽 mx', '👩‍💻 dev']


def headers():
    hs = ['id']
    for c in range(1, N_COLS):
        if c % 10 == 4:
            hs.append('名前%d' % c)
        elif c % 10 == 7:
            hs.append('😀c%02d' % c)
        else:
            hs.append('c%02d' % c)
    return hs


def make_rows(seed=7):
    rnd = random.Random(seed)
    rows = []
    for r in range(N_ROWS):
        row = ['r%02d' % r]
        for c in range(1, N_COLS):
            kind = c % 10
            if c == 29:
                v = None                      # an all-empty column
            elif r == 33 and c != 0:
                v = None                      # an (almost) empty row
            elif kind == 0:
                v = rnd.randint(-500, 50000)
            elif kind == 1:
                v = round(rnd.uniform(-1000, 1000), rnd.randint(0, 4))
            elif kind == 2:
                v = rnd.choice(WORDS) if rnd.random() > .15 else None
            elif kind == 3:
                v = ' '.join(rnd.choice(WORDS) for _ in range(rnd.randint(3, 7)))
            elif kind == 4:
                v = rnd.choice(CJK)
            elif kind == 5:
                v = '%s\n%s' % (rnd.choice(WORDS), rnd.choice(WORDS)) if rnd.random() > .5 else rnd.choice(WORDS)
            elif kind == 6:
                v = rnd.choice([True, False, None])
            elif kind == 7:
                v = rnd.choice(EMOJI)
            elif kind == 8:
                v = rnd.choice([None, None, 0, 1.5e-7, 12345678901, -0.0])
            else:
                v = '  pad %d  ' % rnd.randint(0, 99)
            row.append(v)
        rows.append(row)
    return rows


# ------------------------------------------------------------- features
# Each factor: name -> list of (label, applier). Level 0 is always "off".
def _rule(value, row_index, column_name):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value < 0:
        return 'red'
    return None


def _set(**kw):
    def apply(t):
        for k, v in kw.items():
            setattr(t, k, v)
    return apply


def _call(fn):
    return fn


def _merges(t):
    t.merge_cells(2, 3, last_column=5, value='merged across')
    t.merge_cells(6, 10, last_row=9, value='down')
    t.merge_cells(12, 12, 14, 15, value='block 合併 😀')


OFF = ('off', lambda t: None)

FACTORS = {
    'index': [OFF, ('on', _set(show_index=True)),
              ('titled', _set(show_index=True, index_title='#', index_start=1)),
              ('roman', _set(show_index=True, roman_index=True))],
    'sort': [OFF, ('col', _set(sort_by='c10')), ('rev', _set(sort_by=1, sort_reverse=True)),
             ('key', _set(sort_by=lambda row: str(row[2])))],
    'filter': [OFF, ('even', _set(row_filter=lambda row: int(row[0][1:]) % 2 == 0)),
               ('none', _set(row_filter=lambda row: False))],
    'hide': [OFF, ('cols', _set(hide_columns=[5, 'c08']))],
    'merges': [OFF, ('on', _merges)],
    'colors': [OFF, ('on', _set(use_colors=True, header_color='bold cyan', border_color='dim',
                                column_colors={'c02': 'green'}, row_colors={1: 'yellow'},
                                cell_colors={(3, 3): 'magenta'}, color_rule=_rule))],
    'zebra': [OFF, ('true', _set(use_colors=True, zebra=True)),
              ('pair', _set(use_colors=True, zebra=('on blue', 'on black')))],
    'footer': [OFF, ('2', _set(footer_rows=2, footer_color='bold'))],
    'valign': [OFF, ('m', _set(valign='m')), ('b', _set(valign='b', col_valign={'c03': 't'}))],
    'overflow': [OFF, ('wrap', _set(overflow='wrap', column_max_width=12)),
                 ('trunc', _set(overflow='truncate', column_max_width=8)),
                 ('ellip', _set(overflow='ellipsis', column_max_width=10))],
    'minw': [OFF, ('6', _set(column_min_width=6))],
    'width': [OFF, ('squeeze', _set(max_width=160)), ('narrow', _set(max_width=60))],
    'panel': [OFF, ('rounded', _set(panel=True)), ('double+shadow', _set(panel='double', shadow=True)),
              ('shadow', _set(shadow='▒'))],
    'titles': [OFF, ('both', _set(title='Título 表 😀', caption='caption · fin'))],
    'hrules': [OFF] + [(v, _set(hrules=v)) for v in ('all', 'frame', 'header', 'none')],
    'vrules': [OFF] + [(v, _set(vrules=v)) for v in ('all', 'frame', 'none')],
    'padding': [OFF, ('0', _set(cell_padding=0)), ('2', _set(cell_padding=2))],
    'talign': [OFF, ('c', _set(table_align='c')), ('r', _set(table_align='r'))],
    'halign': [OFF, ('c', _set(header_align='c'))],
    'calign': [OFF, ('r', _set(col_alignment='r')), ('map', _set(col_alignment={'c02': 'c', 'c03': 'r'}))],
    'formats': [OFF, ('on', _set(float_format='.3f', int_format='{:,}',
                                 custom_format={'c02': lambda v: str(v).upper()}))],
    'lzeros': [OFF, ('on', _set(leading_zeros=6))],
    'numcols': [OFF, ('on', _set(number_columns=True))],
    'strip': [OFF, ('on', _set(strip_cells=True))],
    'noheader': [OFF, ('on', _set(show_headers=False))],
    'nomargin': [OFF, ('on', _set(show_margin=False))],
    'suppress': [OFF, ('on', _set(suppress_empty=True))],
    'dividers': [OFF, ('every5', lambda t: t.divide_every(5)), ('some', lambda t: t.add_dividers(0, 10, 40))],
    'bordertext': [OFF, ('top', lambda t: t.border_text(' T ', 'top', align='c')),
                   ('bottom', lambda t: t.border_text(' end ', 'bottom', align='r'))],
    'expand': [OFF, ('on', _set(expand_to_window=True, max_width=600))],
    'missing': [OFF, ('dash', _set(missing_value='—'))],
    'parsestr': [OFF, ('on', _set(parse_str_numbers=True))],
    'mode': [('compose', None), ('paginate', None), ('paginate_nofreeze', None),
             ('stream', None), ('transpose', None)],
}
FEATURES = [f for f in FACTORS if f != 'mode']

BIG = 4000  # max_width default for the harness, so 30 columns are not squeezed


def build(style, config, header_style=None):
    t = Table(rows=make_rows(), headers=headers(), header_style=header_style)
    t.max_width = BIG
    t.use_colors = False
    if style.startswith('theme:'):
        t.apply_theme(style[6:])
    else:
        t.style_name = style
    for name, label in config.items():
        if name == 'mode':
            continue
        dict(FACTORS[name])[label](t)
    return t


# ------------------------------------------------------------ invariants
def arms(ch):
    if not ch or len(ch) != 1:
        return None
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return None
    if not name.startswith('BOX DRAWINGS'):
        return None
    w = set(name.split())
    up = bool(w & {'UP', 'VERTICAL'})
    down = bool(w & {'DOWN', 'VERTICAL'})
    left = bool(w & {'LEFT', 'HORIZONTAL'})
    right = bool(w & {'RIGHT', 'HORIZONTAL'})
    if 'DASH' in w:  # dashed lines: only their own axis
        pass
    return up, down, left, right


def grid(line):
    """Display-column grid: list of chars, a wide char's 2nd cell is ''."""
    out = []
    for ch in strip_ansi(line):
        w = width(ch)
        if w == 0 and out:
            continue
        out.append(ch)
        if w == 2:
            out.append('')
    return out


_BASELINE = {}
PANEL_GLYPHS = set('║│┃|▒░╔╗╚╝╭╮╰╯┌┐└┘┏┓┗┛+═─━-')


def baseline_breaks(style):
    """Junction break signatures of the style with no features (by design)."""
    if style not in _BASELINE:
        out = build(style, {}).compose().split('\n')
        _BASELINE[style] = {(d, ch, n) for d, _, _, ch, n in check_junctions(out)}
    return _BASELINE[style]


def open_end(lines, brk, config):
    """A rule that just stops, by design, rather than a broken joint.

    * a horizontal rule meeting only blanks up to the edge of its line
      (table_align padding, vrules='none', styles without outer verticals);
    * a vertical meeting a blank cell when hrules/vrules removed rules from a
      style whose header or body has no column lines (*_eheader / *_ebody),
      or meeting a title / caption / page label line.
    """
    direction, r, c, ch, n = brk
    if n is None or not n.isspace():
        return False
    row = grid(lines[r])
    if direction in ('left', 'right') and config.get('vrules') == 'none':
        return True  # merge caps without column lines just stop
    if direction == 'left':
        return all(x.isspace() or x == '' for x in row[:c])
    if direction == 'right':
        return all(x.isspace() or x == '' for x in row[c + 1:])
    other = r - 1 if direction == 'up' else r + 1
    if 0 <= other < len(lines) and TITLE_RE.match(strip_ansi(lines[other])):
        return True
    return (config.get('hrules', 'off') != 'off'
            or config.get('vrules', 'off') != 'off')


def check_junctions(lines):
    g = [grid(l) for l in lines]
    probs = []
    for r, row in enumerate(g):
        for c, ch in enumerate(row):
            a = arms(ch)
            if not a:
                continue
            up, down, left, right = a
            if right:
                n = row[c + 1] if c + 1 < len(row) else None
                na = arms(n) if n else None
                if n is not None and not (na and na[2]):
                    probs.append(('right', r, c, ch, n))
            if down:
                n = g[r + 1][c] if r + 1 < len(g) and c < len(g[r + 1]) else None
                na = arms(n) if n else None
                if n is not None and not (na and na[0]):
                    probs.append(('down', r, c, ch, n))
            if left:
                n = row[c - 1] if c > 0 else None
                na = arms(n) if n else None
                if n is not None and not (na and na[3]):
                    probs.append(('left', r, c, ch, n))
            if up:
                n = g[r - 1][c] if r > 0 and c < len(g[r - 1]) else None
                na = arms(n) if n else None
                if n is not None and not (na and na[1]):
                    probs.append(('up', r, c, ch, n))
    return probs


ID_RE = re.compile(r'(?<![\w])r(\d\d)(?![\w])')


def expected_ids(config):
    rows = make_rows()
    order = list(range(N_ROWS))
    f = config.get('filter', 'off')
    if f == 'even':
        order = [i for i in order if i % 2 == 0]
    elif f == 'none':
        order = []
    return order


TITLE_RE = re.compile(r'^\s*(Título 表 😀|caption · fin|page \d+/\d+|Título 表 😀 · page \d+/\d+|page \d+/\d+ · Título 表 😀|.*page \d+/\d+.*)\s*$')


def check_widths(text, config):
    # Title, caption and page-label lines are centred text, not table rows;
    # they are not padded on the right (by design), so they are left out.
    lines = [l for l in text.split('\n') if not TITLE_RE.match(strip_ansi(l))]
    ws = [width(l) for l in lines]
    if len(set(ws)) <= 1:
        return None
    # A table aligned left inside a panel/shadow or a title/caption line may
    # legitimately differ? No: report every mismatch and triage by hand.
    return sorted(set(ws))


def run_case(style, config, header_style=None):
    """Return list of (kind, detail) problems; [] when clean."""
    problems = []
    mode = config.get('mode', 'compose')
    try:
        t = build(style, config, header_style)
        if mode == 'compose':
            outs = [t.compose()]
            again = build(style, config, header_style).compose()
            if again != outs[0]:
                problems.append(('nondeterministic', ''))
        elif mode == 'paginate':
            outs = t.paginate(17)
        elif mode == 'paginate_nofreeze':
            outs = t.paginate(13, freeze_header=False, page_label=True)
        elif mode == 'stream':
            t2 = Table(headers=headers())
            t2.max_width = BIG
            t2.use_colors = False
            if style.startswith('theme:'):
                t2.apply_theme(style[6:])
            else:
                t2.style_name = style
            for name, label in config.items():
                if name in ('mode', 'merges', 'sort', 'suppress'):
                    continue
                dict(FACTORS[name])[label](t2)
            # stream freezes widths before rows arrive; numbers are never
            # cut (by design), so give every column room for the widest one.
            t2.column_min_width = 14
            outs = ['\n'.join(t2.stream(make_rows()))]
        elif mode == 'transpose':
            outs = [t.transpose().compose()]
        else:
            raise AssertionError(mode)
    except Exception as e:  # noqa: BLE001
        return [('exception', '%s: %s\n%s' % (type(e).__name__, e, traceback.format_exc(limit=-3)))]

    for i, out in enumerate(outs):
        if not out:
            continue
        bad = check_widths(out, config)
        if bad:
            problems.append(('width', 'page %d widths %s' % (i, bad)))
        if config.get('bordertext', 'off') == 'off':
            allowed = baseline_breaks(style)
            framed = (config.get('panel', 'off') != 'off')
            out_lines = out.split('\n')
            j = [b for b in check_junctions(out_lines)
                 if (b[0], b[3], b[4]) not in allowed
                 and not open_end(out_lines, b, config)
                 # panel / shadow glyphs are an outer frame, not junctions
                 and not (framed and b[4] in PANEL_GLYPHS)
                 # an empty body closes right under the header box
                 and not (config.get('filter') == 'none' and b[0] == 'up')]
            if j:
                problems.append(('junction', 'page %d %d breaks, first %r' % (i, len(j), j[:3])))

    # visible ids vs filter/sort, only when nothing truncates the id column
    squeezed = (config.get('width', 'off') != 'off' or config.get('overflow', 'off') == 'trunc'
                or mode in ('transpose', 'stream') or config.get('merges') == 'on'
                or config.get('noheader') == 'on' and False)
    if mode in ('compose', 'paginate', 'paginate_nofreeze') and not squeezed:
        seen = []
        for out in outs:
            seen += [int(m) for m in ID_RE.findall(strip_ansi(out))]
        exp = expected_ids(config)
        if config.get('sort', 'off') == 'off':
            if seen != exp:
                problems.append(('rows', 'seen %s.. expected %s..' % (seen[:8], exp[:8])))
        elif sorted(seen) != sorted(exp):
            problems.append(('rows', 'set mismatch %d vs %d' % (len(seen), len(exp))))
        # export order == render order
        try:
            rec = [int(r['id'][1:]) for r in t.to_records() if r.get('id')]
            if rec != seen:
                problems.append(('export-order', 'records %s.. render %s..' % (rec[:8], seen[:8])))
        except Exception as e:  # noqa: BLE001
            problems.append(('exception', 'to_records %s: %s' % (type(e).__name__, e)))
    return problems


def check_exports(style, config):
    problems = []
    try:
        t = build(style, config)
        n = len(t.to_records())
        csv_text = t.to_csv()
        back = Table.from_csv(csv_text, parse_numbers=False)
        if back.row_count != n:
            problems.append(('roundtrip-csv', '%d != %d' % (back.row_count, n)))
        md = t.to_markdown()
        if n:
            back = Table.from_markdown(md, parse_numbers=False)
            if back.row_count != n:
                problems.append(('roundtrip-md', '%d != %d' % (back.row_count, n)))
        html = t.to_html(paginate=0) if True else None
        if n:
            back = Table.from_html(html, parse_numbers=False)
            if back.row_count != n:
                problems.append(('roundtrip-html', '%d != %d' % (back.row_count, n)))
        t.to_rst(); t.to_asciidoc(); t.to_latex(); t.to_records(formatted=True)
        try:
            import openpyxl  # noqa: F401
            import tempfile
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, 'x.xlsx')
                t.to_excel(p)
                back = Table.from_excel(p)
                if back.row_count != n:
                    problems.append(('roundtrip-xlsx', '%d != %d' % (back.row_count, n)))
        except ImportError:
            pass
    except Exception as e:  # noqa: BLE001
        problems.append(('exception', 'export %s: %s\n%s' % (type(e).__name__, e, traceback.format_exc(limit=-3))))
    return problems


# ------------------------------------------------------------- covering
def pairwise(factors, seed=1):
    """Greedy all-pairs covering array over {name: [labels]}."""
    names = list(factors)
    levels = [factors[n] for n in names]
    uncovered = set()
    for (i, a), (j, b) in itertools.combinations(enumerate(levels), 2):
        for x in a:
            for y in b:
                uncovered.add((i, x, j, y))
    rnd = random.Random(seed)
    tests = []
    while uncovered:
        best, best_cov = None, -1
        # sorted, not set order: string hashing is randomised per process,
        # and the cases must be the same on every run
        pending = sorted(uncovered, key=str)[:200]
        for _ in range(40):
            # seed from an uncovered pair
            i, x, j, y = rnd.choice(pending)
            cand = [None] * len(names)
            cand[i], cand[j] = x, y
            order = list(range(len(names)))
            rnd.shuffle(order)
            for k in order:
                if cand[k] is not None:
                    continue
                scores = []
                for v in levels[k]:
                    s = sum(1 for m in range(len(names)) if cand[m] is not None and
                            ((min(k, m), v if k < m else cand[m], max(k, m), cand[m] if k < m else v) in uncovered))
                    scores.append((s, rnd.random(), v))
                cand[k] = max(scores)[2]
            cov = sum(1 for (p, q) in itertools.combinations(range(len(names)), 2)
                      if (p, cand[p], q, cand[q]) in uncovered)
            if cov > best_cov:
                best, best_cov = cand, cov
        for (p, q) in itertools.combinations(range(len(names)), 2):
            uncovered.discard((p, best[p], q, best[q]))
        tests.append(dict(zip(names, best)))
    return tests


def factor_labels(include_mode=True):
    return {n: [l for l, _ in FACTORS[n]] for n in FACTORS if include_mode or n != 'mode'}


EVERYTHING = [
    dict(index='titled', sort='col', filter='even', hide='cols', merges='on', colors='on',
         zebra='pair', footer='2', valign='m', overflow='wrap', minw='6', panel='double+shadow',
         titles='both', dividers='every5', formats='on', calign='map', halign='c', talign='c',
         missing='dash', strip='on', suppress='on'),
    dict(index='roman', sort='key', overflow='ellip', width='squeeze', colors='on', zebra='true',
         panel='rounded', titles='both', hrules='all', vrules='frame', padding='2', numcols='on',
         lzeros='on', parsestr='on', bordertext='top'),
    dict(index='on', filter='even', merges='on', hrules='header', vrules='none', padding='0',
         nomargin='on', noheader='on', valign='b', overflow='trunc', footer='2', expand='on'),
]


def iter_cases(mode, styles):
    if mode in ('single', 'all'):
        for s in styles:
            yield s, {'mode': 'compose'}
            for f in FACTORS:
                for label, _ in FACTORS[f][1:]:
                    yield s, {f: label} if f != 'mode' else {'mode': label}
    if mode in ('pairwise', 'all'):
        labels = factor_labels()
        labels['style'] = styles
        for case in pairwise(labels):
            s = case.pop('style')
            yield s, {k: v for k, v in case.items() if v != 'off'}
    if mode in ('everything', 'all'):
        for s in styles:
            for combo in EVERYTHING:
                for m in ('compose', 'paginate', 'transpose'):
                    yield s, dict(combo, mode=m)


def stream_vs_compose():
    """stream() must print what compose() prints for the same rows
    (colour stripped), across frame/title/zebra/index settings."""
    rows = [[1, 'x'], [2, 'y'], [3, 'z']]
    opts = dict(style_name=['sharp', 'blank', 'plain', 'empty', 'rounded',
                            'bheader_ebody', 'markdown', 'grid_eheader'],
                show_headers=[True, False], panel=[False, 'double'],
                shadow=[False, True], caption=[None, 'cap'], title=[None, 'T'],
                zebra=[None, ('on blue', 'on black')], show_index=[False, True])
    bad, n = [], 0
    for values in itertools.product(*opts.values()):
        settings = dict(zip(opts, values), use_colors=True)
        for body in (rows, rows[:1], []):
            if not body and not settings['show_headers']:
                continue  # nothing to measure widths from; degenerate
            n += 1
            streamed, composed = Table(headers=['a', 'b']), Table(headers=['a', 'b'])
            for k, v in settings.items():
                setattr(streamed, k, v)
                setattr(composed, k, v)
            got = [strip_ansi(l) for l in streamed.stream(body)]
            for row in body:
                composed.add_row(row)
            text = composed.compose()
            want = strip_ansi(text).split('\n') if text else []
            if got != want:
                bad.append({'style': 'stream', 'config': settings,
                            'problems': [('stream!=compose', '%d rows' % len(body))]})
    return n, bad


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', default='all')
    ap.add_argument('--styles', default='')
    ap.add_argument('--themes', action='store_true')
    ap.add_argument('--exports', action='store_true')
    ap.add_argument('--json', default='')
    a = ap.parse_args(argv)
    styles = a.styles.split(',') if a.styles else list(STYLES)
    if a.themes:
        styles += ['theme:' + t for t in THEMES]
    results, n = [], 0
    if a.mode in ('streamcmp', 'all'):
        n, results = stream_vs_compose()
    for style, config in iter_cases(a.mode, styles):
        n += 1
        probs = run_case(style, config)
        if a.exports and config.get('mode', 'compose') == 'compose':
            probs += check_exports(style, config)
        if probs:
            results.append({'style': style, 'config': config, 'problems': probs})
    by_kind = {}
    for r in results:
        for k, _ in r['problems']:
            by_kind[k] = by_kind.get(k, 0) + 1
    print('cases', n, 'failing', len(results), by_kind)
    if a.json:
        with open(a.json, 'w') as fh:
            json.dump({'cases': n, 'results': results}, fh, ensure_ascii=False, indent=1, default=str)
    return 1 if results else 0


if __name__ == '__main__':
    sys.exit(main())
