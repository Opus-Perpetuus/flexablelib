# Benchmarks

One job measured: turning tabular data already in memory into a formatted
string. Best of 5 runs per library, same data for all.

Reproduce:

```bash
pip install tabulate prettytable rich pandas
python3 tools/benchmark.py           # C extension (wheels ship it)
python3 tools/benchmark.py --pure    # pure-Python fallback
```

## Results (2026-10-31)

Machine: 8-vCPU Intel Xeon (cloud VM), Linux, CPython 3.13.5.
Versions: flexablelib 2.0.17 (dev tree), tabulate 0.10.0, prettytable 3.18.0,
rich 15.0.0, pandas 3.1.0. Times in milliseconds, lower is better.

### flexablelib with the C extension

| Library | 100 × 4 | 2,000 × 4 | 10,000 × 6 |
| --- | ---: | ---: | ---: |
| pandas `DataFrame.to_string()` | 0.8 | 9.8 | 84.5 |
| **flexablelib** | **1.0** | **18.2** | **156.6** |
| prettytable (default style) | 1.1 | 20.6 | 155.5 |
| tabulate (`tablefmt="grid"`) | 1.5 | 29.3 | 206.1 |
| rich `Table` (no colour, width 200) | 17.8 | 370.7 | 2,843.7 |

### flexablelib pure Python (no compiler, no wheel)

| Library | 100 × 4 | 2,000 × 4 | 10,000 × 6 |
| --- | ---: | ---: | ---: |
| **flexablelib** | **1.1** | **19.8** | **172.3** |
| prettytable | 1.1 | 20.7 | 155.5 |
| tabulate | 1.6 | 29.5 | 206.4 |

## Reading the numbers

- flexablelib and prettytable are effectively tied; flexablelib is about
  1.3× faster than tabulate and 15–20× faster than rich's table renderer.
- pandas is roughly 2× faster at this one task. `to_string` is a convenience
  inside an analysis engine whose columns are already typed arrays; it has no
  border styles, colours or merges. This says nothing about groupby or joins.
- rich does much more per cell (markup parsing, styled segments, a generic
  layout engine), so the gap is the cost of that generality, not a defect.
- 2.0.17 removed a per-cell vertical-alignment lookup that 2.0.14 added to
  every render; 10,000 × 6 went from ~187 ms to ~157 ms.
- Each library renders with its own defaults beyond the noted format, so the
  output strings are not byte-identical. Run-to-run noise is about ±3 %.
