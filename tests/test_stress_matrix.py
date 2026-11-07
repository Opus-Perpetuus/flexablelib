"""Reduced 30x50 style x feature matrix (full run: python tools/stress_matrix.py).

Every style renders the 30-column x 50-row mixed table (CJK, emoji,
multi-line, None, an empty row and column) once plain, then a pairwise
covering set of the feature options is spread across the styles, plus the
'everything at once' combos on a few styles. Each render is checked for:
no exception, equal line widths, connected box junctions (relative to the
style's own design), visible rows matching row_filter / sort_by,
to_records() order matching the render, and determinism.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
import stress_matrix as matrix  # noqa: E402

PAIRWISE = matrix.pairwise(matrix.factor_labels(), seed=3)
CASES = (
    [(style, {}) for style in matrix.STYLES]
    + [('theme:' + theme, {}) for theme in matrix.THEMES]
    + [(matrix.STYLES[i * 7 % len(matrix.STYLES)],
        {k: v for k, v in case.items() if v != 'off'})
       for i, case in enumerate(PAIRWISE)]
    + [(style, dict(combo, mode=mode))
       for style in ('rounded', 'grid', 'plain')
       for combo in matrix.EVERYTHING
       for mode in ('compose', 'paginate')]
)


def _id(case):
    style, config = case
    return style + ':' + ','.join('%s=%s' % kv for kv in sorted(config.items()))


@pytest.mark.parametrize('case', CASES, ids=[_id(c) for c in CASES])
def test_render_invariants(case):
    style, config = case
    assert matrix.run_case(style, config) == []


@pytest.mark.parametrize('style', ['rounded', 'grid', 'markdown'])
@pytest.mark.parametrize('combo', range(len(matrix.EVERYTHING)))
def test_exports_round_trip(style, combo):
    assert matrix.check_exports(style, matrix.EVERYTHING[combo]) == []
