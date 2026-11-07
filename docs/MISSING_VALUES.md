# Missing cells (2.3.0)

## Display and migration

An explicit `None`, a padded absent cell, and `table.missing` all render as
`table.missing_value`, whose default is `''` (blank). This is a visible change
from 2.2.4, where explicit `None` printed as the text `None`.

- Set `table.missing_value = '?'` (or constructor `missing_val='?'`) to label
  missing cells. Changing it affects later renders, not stored values.
- Store the string `'None'` if you need the literal word.
- An empty string remains an empty string; this change does not parse text.

The same rules apply to `print(table)`/`str(table)`, `compose()`, `paginate()`,
`stream()` and the table returned by `transpose()`/`rotate()`, in all styles.
Numeric columns ignore missing cells when determining their type. A float
column containing `None` stays decimal-aligned instead of becoming wrappable
text. Numeric size limits still obey the existing rules: floats can give up
decimal precision but are not arbitrarily split or cut.

## Raw data and round-trips

`table.rows`, `to_records()` and exports keep their existing missing-data
contract. Raw gaps are `None` (file formats may encode these as empty fields).
Even `to_records(formatted=True)` keeps a missing cell as `None`, rather than
exporting its display placeholder as real data.

```python
from flexablelib import Table

t = Table(rows=[[924.87], [None], [1.25]])
assert Table(rows=t.rows).compose() == t.compose()
assert t.rows == [[924.87], [None], [1.25]]
t.missing_value = '?'
assert t.to_records()[1] == {t.headers[0]: None}
```

The `rows` property is data, not a display-settings snapshot. Copy matching
headers, style and display options when reconstructing a customized table.
Filtering, sorting, hiding empty rows and color callbacks retain their
existing contracts; this change concerns missing-cell display and typing.
