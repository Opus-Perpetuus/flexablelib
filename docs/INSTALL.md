# Installing flexablelib and its optional packages

The core package has no dependencies:

```
pip install flexablelib
```

Everything else is an extra. The terminal-application layers are separate
distributions released together with the core (same version number), so an
extra always installs the matching release.

| Extra | Installs | What you get |
| --- | --- | --- |
| `tui` | `flexablelib-tui` | `App` (focus, key bindings, dialogs, notifications, ticks, resize), keyboard input on Linux, macOS and Windows, `ScrollView`, and the widgets/`Screen`/`Live` (moved here in 3.3.0; still importable from `flexablelib`). Pure Python. |
| `components` | `flexablelib-components` + `flexablelib-tui` | the 85 components in [COMPONENTS.md](COMPONENTS.md), including `Image` (PNG, GIF, BMP and PPM decode without dependencies). Pure Python. |
| `images` | Pillow + `flexablelib-components` | pictures in JPEG, WebP, TIFF, ICO and every Pillow format, faster decoding ([IMAGES.md](IMAGES.md)). |
| `svg` | cairosvg | SVG pictures (needs the cairo system library; `rsvg-convert` works without it). |
| `speed` | `flexablelib-speedups` | C code for interface frames and pictures (resize, quantization, sixel, blocks) ([ACCELERATION.md](ACCELERATION.md)). Prebuilt wheels for CPython 3.8–3.14 on Linux x86_64 and aarch64 (manylinux and musllinux/Alpine), Windows x64 and macOS (arm64 and Intel x86_64); elsewhere it compiles from source, and without a compiler it installs without the C module and flexablelib keeps its Python frame code. |
| `pandas`, `excel`, `html` | pandas, openpyxl, lxml | readers and writers. |
| `all` | all of the above except `svg` | |

```
pip install "flexablelib[tui]"
pip install "flexablelib[components,speed]"
pip install "flexablelib[images]"
pip install "flexablelib[all]"
```

(Quote the brackets in zsh and other shells that expand them.)

## Prebuilt wheels

`flexablelib` (its text-measurement extension) and `flexablelib-speedups`
ship binary wheels for CPython 3.8–3.14 on:

| Platform | Wheel tag |
| --- | --- |
| Linux x86_64 (glibc: Debian, Ubuntu, RHEL, Amazon Linux...) | `manylinux_2_17_x86_64` / `manylinux2014_x86_64` |
| Linux x86_64 (musl: Alpine) | `musllinux_1_2_x86_64` |
| Linux aarch64 / arm64 (glibc: Graviton, Ampere, Raspberry Pi OS 64-bit...) | `manylinux_2_17_aarch64` / `manylinux2014_aarch64` |
| Linux aarch64 / arm64 (musl: Alpine) | `musllinux_1_2_aarch64` |
| Windows x64 | `win_amd64` |
| macOS Apple silicon | `macosx_11_0_arm64` |
| macOS Intel | `macosx_10_9_x86_64` (`macosx_10_13` for the newest Pythons) |

Every wheel is built on a native machine of its architecture and tested
there: the C code must load and give the same results as the pure Python
code on random input (`tools/wheel_check.py`). `flexablelib-tui` and
`flexablelib-components` are pure Python (`py3-none-any`). On any other
platform pip builds from the sdist, and without a compiler everything still
works in pure Python.

## Checking what is active

```python
from flexablelib.fast import implementation   # text measurement
from flexablelib import _frames                # interface frames
print(implementation(), _frames.BACKEND)       # 'C extension' 'c'
```

`FLEXABLELIB_FRAMES=python` forces the Python frame code even when the C
package is installed; `FLEXABLELIB_IMAGES=python` does the same for the
picture code (`flexablelib._images.BACKEND`).

What the terminal can show as pictures:

```python
from flexablelib_tui import detect_graphics
print('\n'.join(detect_graphics().summary()))
```

## Without the extras

`from flexablelib import ProgressBar, Screen, Live, ...` keeps working on a
bare install: flexablelib carries a frozen copy of the 3.2.0 widgets and
warns once (`DeprecationWarning`) that they now live in `flexablelib[tui]`.
`App`, `Component`, `ScrollView` and the other `flexablelib-tui` names raise
an `ImportError` that names the extra to install. Components are imported
from `flexablelib_components` (`import flexablelib_components as C`); once
installed they are also reachable as `flexablelib.DataTable` and so on.
