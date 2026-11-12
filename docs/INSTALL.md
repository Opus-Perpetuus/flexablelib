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
| `components` | `flexablelib-components` + `flexablelib-tui` | the 83 components in [COMPONENTS.md](COMPONENTS.md). Pure Python. |
| `speed` | `flexablelib-speedups` | C code for interface frames ([ACCELERATION.md](ACCELERATION.md)). Prebuilt wheels for CPython 3.8–3.14 on Linux (manylinux, musllinux x86_64), Windows x64 and macOS arm64; elsewhere it compiles from source, and without a compiler it installs without the C module and flexablelib keeps its Python frame code. |
| `pandas`, `excel`, `html` | pandas, openpyxl, lxml | readers and writers. |
| `all` | all of the above | |

```
pip install "flexablelib[tui]"
pip install "flexablelib[components,speed]"
pip install "flexablelib[all]"
```

(Quote the brackets in zsh and other shells that expand them.)

## Checking what is active

```python
from flexablelib.fast import implementation   # text measurement
from flexablelib import _frames                # interface frames
print(implementation(), _frames.BACKEND)       # 'C extension' 'c'
```

`FLEXABLELIB_FRAMES=python` forces the Python frame code even when the C
package is installed.

## Without the extras

`from flexablelib import ProgressBar, Screen, Live, ...` keeps working on a
bare install: flexablelib carries a frozen copy of the 3.2.0 widgets and
warns once (`DeprecationWarning`) that they now live in `flexablelib[tui]`.
`App`, `Component`, `ScrollView` and the other `flexablelib-tui` names raise
an `ImportError` that names the extra to install. Components are imported
from `flexablelib_components` (`import flexablelib_components as C`); once
installed they are also reachable as `flexablelib.DataTable` and so on.
