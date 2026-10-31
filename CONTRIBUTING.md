# Contributing to flexablelib

Thanks for helping! Bug reports, docs fixes, new styles and features are all
welcome.

## Quick start

```bash
git clone https://github.com/Opus-Perpetuus/flexablelib
cd flexablelib
python -m venv .venv && . .venv/bin/activate
pip install -e .                  # also builds the optional C extension
pip install -r requirements-dev.txt
python -m pytest                  # run from the repository root
```

The package has **no runtime dependencies**; please keep it that way. Code
that needs a third-party library belongs behind an extra in `setup.py`
(`extras_require`) and an import inside the function that uses it.

## Reporting a bug

Open an [issue](https://github.com/Opus-Perpetuus/flexablelib/issues/new/choose)
with the smallest script that reproduces it, what you expected, what you got
(paste the table), your OS, terminal, Python version, and the output of:

```python
import flexablelib, sys
from flexablelib.fast import implementation
print(sys.version, implementation())
```

## Pull requests

1. Open the PR against `main`. Keep it focused on one change.
2. Add a test in `tests/` that fails without your change. Golden-output tests
   (compare the rendered string) are the norm here.
3. `python -m pytest` must pass; CI runs Python 3.8 – 3.14 plus a job with the
   C extension. The C and pure-Python measurement paths must agree exactly
   (`flexablelib/fast.py`, `text_width.py`).
4. Public behaviour changes go into `CHANGELOG.md` under an *Unreleased*
   heading. Don't bump the version; maintainers do that at release time.
5. Use conventional commit messages (`fix: …`, `feat: …`, `docs: …`).

## Adding a border style

Styles are data in `flexablelib/style_compositions.py`. See
[ARCHITECTURE.md](ARCHITECTURE.md) for the field meanings, then regenerate
`style_examples.md` and add the name to the style tests.

## Regenerating README images

```bash
pip install pillow
python3 tools/readme_gallery.py   # writes docs/img/*.png from the current code
```

## Versioning

flexablelib follows [semantic versioning](https://semver.org). Within a major
version, public `Table` attributes and methods are not removed or renamed
without a deprecation warning in at least one prior release.

## License

By contributing you agree that your contributions are licensed under the
[MIT License](LICENSE).
