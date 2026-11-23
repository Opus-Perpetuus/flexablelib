"""3.7.6: pictures -- kitty placeholders for very tall or wide pictures,
mono half blocks next to transparency, the name of a URL picture, named
background colours and upper-case URL schemes."""

import pytest

g = pytest.importorskip('flexablelib_tui.graphics')
fc = pytest.importorskip('flexablelib_components')

from flexablelib import _images as I
from flexablelib_tui import accessibility as a11y


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for name in ('FLEXABLELIB_IMAGE', 'NO_COLOR', 'TMUX', 'FORCE_COLOR'):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('FLEXABLELIB_NO_BROWSER', '1')
    g.reset_cache()
    with a11y.configure(screen_reader=False, ascii=False,
                        reduced_motion=False):
        yield
    g.reset_cache()


def info(**kw):
    base = dict(color='truecolor', unicode=True, cell=(10, 20),
                cell_known=True, order=['kitty', 'iterm', 'sixel'])
    base.update(kw)
    return g.GraphicsInfo(**base)


def use(monkeypatch, gi):
    monkeypatch.setattr(g, 'detect', lambda *a, **k: gi)


def blank(w, h):
    return I.Bitmap(w, h, bytes([90, 120, 200, 255]) * (w * h))


class TestKittyPlaceholderLimit:
    """Placeholder cells number rows and columns with combining marks, and
    there are only len(DIACRITICS) of them: a bigger picture is shrunk to
    fit instead of failing with IndexError."""

    @pytest.mark.parametrize('tmux', [False, True])
    def test_tall_picture(self, monkeypatch, tmux):
        use(monkeypatch, info(kitty=True, kitty_placeholders=not tmux,
                              tmux=tmux))
        img = fc.Image(blank(100, 8000), alt='Alta')
        lines = img.render(10).split('\n')
        limit = len(g.DIACRITICS)
        assert img.used_method == 'kitty'
        assert len(lines) == limit
        assert lines[0].count(g.PLACEHOLDER) <= 10

    def test_wide_picture(self, monkeypatch):
        use(monkeypatch, info(kitty=True, kitty_placeholders=True))
        img = fc.Image(blank(4000, 20), alt='Ancha')
        lines = img.render(320).split('\n')
        limit = len(g.DIACRITICS)
        assert img.used_method == 'kitty'
        assert max(l.count(g.PLACEHOLDER) for l in lines) == limit

    @pytest.mark.parametrize('fit', ['fill', 'cover', 'none'])
    def test_other_fits(self, monkeypatch, fit):
        use(monkeypatch, info(kitty=True, kitty_placeholders=True))
        img = fc.Image(blank(100, 8000), alt='Alta', fit=fit, height=400)
        lines = img.render(10, 400).split('\n')
        assert img.used_method == 'kitty'
        assert len(lines) <= len(g.DIACRITICS)

    def test_direct_kitty_and_sixel_keep_the_size(self, monkeypatch):
        for gi in (info(kitty=True, kitty_placeholders=False),
                   info(sixel=True)):
            use(monkeypatch, gi)
            img = fc.Image(blank(100, 8000), alt='Alta')
            assert len(img.render(10).split('\n')) == 400


BACKENDS = I.available()


class TestMonoHalfBlocks:
    """Without colour a half block is lit only for a light pixel: a
    transparent half is unlit like a dark one, so a dark pixel next to
    transparency no longer shows as a lit block."""

    BLACK, WHITE, CLEAR = (bytes([0, 0, 0, 255]), bytes([255] * 4),
                           bytes(4))

    @pytest.mark.parametrize('backend', BACKENDS)
    @pytest.mark.parametrize('top, bottom, want', [
        ('BLACK', 'CLEAR', ' '), ('CLEAR', 'BLACK', ' '),
        ('WHITE', 'CLEAR', '▀'), ('CLEAR', 'WHITE', '▄'),
        ('CLEAR', 'CLEAR', ' '), ('BLACK', 'WHITE', '▄'),
        ('WHITE', 'BLACK', '▀'), ('WHITE', 'WHITE', '█'),
        ('BLACK', 'BLACK', ' '),
    ])
    def test_cell(self, backend, top, bottom, want):
        fn = I._PYTHON['cells'] if backend == 'python' else I._C.cells
        data = getattr(self, top) + getattr(self, bottom)
        assert fn(data, 1, 2, 'half', 'none', 128) == [want]

    def test_colour_keeps_the_pixel_colour(self):
        for backend in BACKENDS:
            fn = I._PYTHON['cells'] if backend == 'python' else I._C.cells
            line = fn(self.BLACK + self.CLEAR, 1, 2, 'half', 'truecolor',
                      128)[0]
            assert '▀' in line and '38;2;0;0;0' in line


class TestUrlName:
    """The name of a URL picture is its file name: without the query (a
    signed URL's token) or the fragment, and decoded."""

    @pytest.mark.parametrize('url, want', [
        ('https://ex.com/fotos/silla.png?token=SECRETO#x', 'silla.png'),
        ('https://ex.com/fotos/silla.png#vista', 'silla.png'),
        ('https://ex.com/fotos/silla%20roja.png', 'silla roja.png'),
        ('https://ex.com/fotos/a%C3%B1o.png', 'año.png'),
        ('https://ex.com/fotos/', 'fotos'),
        ('https://ex.com/', 'ex.com'),
        ('https://ex.com/?id=7', 'ex.com'),
        ('file:///tmp/mi%20foto.png', 'mi foto.png'),
    ])
    def test_name(self, url, want):
        assert fc.Image(url).name == want

    def test_warning_does_not_show_the_query(self, monkeypatch):
        use(monkeypatch, info())
        monkeypatch.setattr(g, 'browser_available',
                            lambda *a, **k: (False, 'sin pantalla'))
        img = fc.Image('https://ex.com/silla.png?token=SECRETO',
                       method='half')
        monkeypatch.setattr(img, 'bitmap', lambda: None)
        img.error = 'no se pudo descargar (HTTP 403)'
        out = img.render(80)
        assert 'silla.png' in out and 'SECRETO' not in out

    def test_paths_unchanged(self):
        assert fc.Image('/tmp/fotos/a?b.png').name == 'a?b.png'
        assert fc.Image('/tmp/fotos/').name == 'fotos'


class TestBackgroundColour:
    """``background`` takes any colour the library draws (names, ``#rgb``,
    ``color:N``, ``greyNN``, ``on <colour>``) or an RGB tuple; a named one
    raised ValueError while drawing."""

    @pytest.mark.parametrize('colour, rgb', [
        ('#fff', (255, 255, 255)), ('fff', (255, 255, 255)),
        ('#336699', (51, 102, 153)), ((1, 2, 3), (1, 2, 3)),
        ([1, 2, 3], (1, 2, 3)), ('white', None), ('on white', None),
        ('bright_red', None), ('grey50', None), ('color:15', None),
        (' #FFFFFF ', (255, 255, 255)), ('#ff000080', (255, 0, 0)),
    ])
    def test_parsed(self, colour, rgb):
        from flexablelib_tui.accessibility import parse_color
        got = fc.media._rgb(colour)
        name = str(colour).replace('on ', '').strip() \
            if not isinstance(colour, (tuple, list)) else None
        assert got == (rgb or parse_color(name))

    @pytest.mark.parametrize('method', ['half', 'braille', 'sixel', 'kitty'])
    def test_named_colour_renders(self, monkeypatch, method):
        use(monkeypatch, info(kitty=True, kitty_placeholders=True,
                              sixel=True))
        clear = I.Bitmap(4, 4, bytes(64))
        img = fc.Image(clear, background='white', method=method,
                       use_colors=True)
        img.render(8, 4)
        assert img.used_method == method

    def test_named_colour_is_used(self, monkeypatch):
        use(monkeypatch, info())
        clear = I.Bitmap(2, 2, bytes(16))
        out = fc.Image(clear, background='on #ff0000', method='half',
                       use_colors=True, width=2).render(2, 1)
        assert '38;2;255;0;0' in out

    def test_unknown_colour_is_refused_up_front(self):
        with pytest.raises(ValueError):
            fc.Image(blank(2, 2), background='blanco hueso')
        with pytest.raises(ValueError):
            fc.Image(blank(2, 2), background='#12')
