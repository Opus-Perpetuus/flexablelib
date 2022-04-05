**POSSIBLE STYLES**
===================
### PLAIN
```
>>> from prettyTables import Table
>>> new_table = Table()
>>> new_table.missing_val = 'n/a'
>>> new_table.add_row(data=[1])
>>> new_table.add_column(data=['Kg', 'ml'])
>>> new_table.show_headers = True
>>> new_table.style_name = 'plain'
... column 1 column 2
...
... 1        Kg
... n/a      ml
>>> new_table.show_headers = False
>>> new_table
... 1   Kg
... n/a ml
```

---------------
### PRETTY_GRID
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'pretty_grid'
... ╒══════════╤══════════╕
... │ column 1 │ column 2 │
... ╞══════════╪══════════╡
... │ 1        │ Kg       │
... ├──────────┼──────────┤
... │ n/a      │ ml       │
... ╘══════════╧══════════╛
>>> new_table.show_headers = False
>>> new_table
... ╒═════╤════╕
... │ 1   │ Kg │
... ├─────┼────┤
... │ n/a │ ml │
... ╘═════╧════╛
```

---------------
### PRETTY_COLUMNS
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'pretty_columns'
... ╒══════════╤══════════╕
... │ column 1 │ column 2 │
... ╞══════════╪══════════╡
... │ 1        │ Kg       │
... │ n/a      │ ml       │
... ╘══════════╧══════════╛
>>> new_table.show_headers = False
>>> new_table
... ╒═════╤════╕
... │ 1   │ Kg │
... │ n/a │ ml │
... ╘═════╧════╛
```

---------------
### BOLD_HEADER
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'bold_header'
... ╔══════════╦══════════╗
... ║ column 1 ║ column 2 ║
... ╚══════════╩══════════╝
... │ 1        │ Kg       │
... ├──────────┼──────────┤
... │ n/a      │ ml       │
... └──────────┴──────────┘
>>> new_table.show_headers = False
>>> new_table
... ┌─────┬────┐
... │ 1   │ Kg │
... ├─────┼────┤
... │ n/a │ ml │
... └─────┴────┘
```

---------------
### BHEADER_COLUMNS
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'bheader_columns'
... ╔══════════╦══════════╗
... ║ column 1 ║ column 2 ║
... ╚══════════╩══════════╝
... │ 1        │ Kg       │
... │ n/a      │ ml       │
... └──────────┴──────────┘
>>> new_table.show_headers = False
>>> new_table
... ┌─────┬────┐
... │ 1   │ Kg │
... │ n/a │ ml │
... └─────┴────┘
```

---------------
### BOLD_EHEADER
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'bold_eheader'
... ╔═════════════════════╗
... ║ column 1   column 2 ║
... ╚═════════════════════╝
... │ 1        │ Kg       │
... ├──────────┼──────────┤
... │ n/a      │ ml       │
... └──────────┴──────────┘
>>> new_table.show_headers = False
>>> new_table
... ┌─────┬────┐
... │ 1   │ Kg │
... ├─────┼────┤
... │ n/a │ ml │
... └─────┴────┘
```

---------------
### BEHEADER_COLUMNS
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'beheader_columns'
... ╔═════════════════════╗
... ║ column 1   column 2 ║
... ╚═════════════════════╝
... │ 1        │ Kg       │
... │ n/a      │ ml       │
... └──────────┴──────────┘
>>> new_table.show_headers = False
>>> new_table
... ┌─────┬────┐
... │ 1   │ Kg │
... │ n/a │ ml │
... └─────┴────┘
```

---------------
### BHEADER_EBODY
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'bheader_ebody'
... ╔═════════════════════╗
... ║ column 1   column 2 ║
... ╚═════════════════════╝
... │ 1          Kg       │
... │ n/a        ml       │
... └─────────────────────┘
>>> new_table.show_headers = False
>>> new_table
... ┌──────────┐
... │ 1     Kg │
... │ n/a   ml │
... └──────────┘
```

---------------
### ROUND_EDGES
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'round_edges'
... ╭──────────┬──────────╮
... │ column 1 │ column 2 │
... ╞══════════╪══════════╡
... │ 1        │ Kg       │
... │ n/a      │ ml       │
... ╰──────────┴──────────╯
>>> new_table.show_headers = False
>>> new_table
... ╭─────┬────╮
... │ 1   │ Kg │
... │ n/a │ ml │
... ╰─────┴────╯
```

---------------
### RE_EHEADER
```
>>> new_table.show_headers = True
>>> new_table.style_name = 're_eheader'
... ╭─────────────────────╮
... │ column 1   column 2 │
... ╞══════════╤══════════╡
... │ 1        │ Kg       │
... │ n/a      │ ml       │
... ╰──────────┴──────────╯
>>> new_table.show_headers = False
>>> new_table
... ╭─────┬────╮
... │ 1   │ Kg │
... │ n/a │ ml │
... ╰─────┴────╯
```

---------------
### RE_EBODY
```
>>> new_table.show_headers = True
>>> new_table.style_name = 're_ebody'
... ╭─────────────────────╮
... │ column 1   column 2 │
... ╞═════════════════════╡
... │ 1          Kg       │
... │ n/a        ml       │
... ╰─────────────────────╯
>>> new_table.show_headers = False
>>> new_table
... ╭──────────╮
... │ 1     Kg │
... │ n/a   ml │
... ╰──────────╯
```

---------------
### THIN_BORDERLINE
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'thin_borderline'
... ┌──────────┬──────────┐
... │ column 1 │ column 2 │
... ╞══════════╪══════════╡
... │ 1        │ Kg       │
... ├──────────┼──────────┤
... │ n/a      │ ml       │
... └──────────┴──────────┘
>>> new_table.show_headers = False
>>> new_table
... ┌─────┬────┐
... │ 1   │ Kg │
... ├─────┼────┤
... │ n/a │ ml │
... └─────┴────┘
```

---------------
### TH_BD_EHEADER
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'th_bd_eheader'
... ┌─────────────────────┐
... │ column 1   column 2 │
... ╞══════════╤══════════╡
... │ 1        │ Kg       │
... ├──────────┼──────────┤
... │ n/a      │ ml       │
... └──────────┴──────────┘
>>> new_table.show_headers = False
>>> new_table
... ┌─────┬────┐
... │ 1   │ Kg │
... ├─────┼────┤
... │ n/a │ ml │
... └─────┴────┘
```

---------------
### TH_BD_EBODY
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'th_bd_ebody'
... ┌──────────┬──────────┐
... │ column 1 │ column 2 │
... ╞══════════╧══════════╡
... │ 1          Kg       │
... │ n/a        ml       │
... └─────────────────────┘
>>> new_table.show_headers = False
>>> new_table
... ┌──────────┐
... │ 1     Kg │
... │ n/a   ml │
... └──────────┘
```

---------------
### TH_BD_EMPTY
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'th_bd_empty'
... ┌─────────────────────┐
... │ column 1   column 2 │
... ╞═════════════════════╡
... │ 1          Kg       │
... │ n/a        ml       │
... └─────────────────────┘
>>> new_table.show_headers = False
>>> new_table
... ┌──────────┐
... │ 1     Kg │
... │ n/a   ml │
... └──────────┘
```

---------------
### BOLD_BORDERLINE
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'bold_borderline'
... ╔══════════╤══════════╗
... ║ column 1 │ column 2 ║
... ╠══════════╪══════════╣
... ║ 1        │ Kg       ║
... ╟──────────┼──────────╢
... ║ n/a      │ ml       ║
... ╚══════════╧══════════╝
>>> new_table.show_headers = False
>>> new_table
... ╔═════╤════╗
... ║ 1   │ Kg ║
... ╟─────┼────╢
... ║ n/a │ ml ║
... ╚═════╧════╝
```

---------------
### BD_BL_EHEADER
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'bd_bl_eheader'
... ╔═════════════════════╗
... ║ column 1   column 2 ║
... ╠══════════╤══════════╣
... ║ 1        │ Kg       ║
... ╟──────────┼──────────╢
... ║ n/a      │ ml       ║
... ╚══════════╧══════════╝
>>> new_table.show_headers = False
>>> new_table
... ╔═════╤════╗
... ║ 1   │ Kg ║
... ╟─────┼────╢
... ║ n/a │ ml ║
... ╚═════╧════╝
```

---------------
### BD_BL_EBODY
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'bd_bl_ebody'
... ╔══════════╤══════════╗
... ║ column 1 │ column 2 ║
... ╠══════════╧══════════╣
... ║ 1          Kg       ║
... ║ n/a        ml       ║
... ╚═════════════════════╝
>>> new_table.show_headers = False
>>> new_table
... ╔══════════╗
... ║ 1     Kg ║
... ║ n/a   ml ║
... ╚══════════╝
```

---------------
### BD_BL_EMPTY
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'bd_bl_empty'
... ╔═════════════════════╗
... ║ column 1   column 2 ║
... ╠═════════════════════╣
... ║ 1          Kg       ║
... ║ n/a        ml       ║
... ╚═════════════════════╝
>>> new_table.show_headers = False
>>> new_table
... ╔══════════╗
... ║ 1     Kg ║
... ║ n/a   ml ║
... ╚══════════╝
```

---------------
### PWRSHLL_ALIKE
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'pwrshll_alike'
... column 1 column 2
... -------- --------
... 1        Kg
... n/a      ml
>>> new_table.show_headers = False
>>> new_table
... 1   Kg
... n/a ml
```

---------------
### PRESTO
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'presto'
...  column 1 | column 2
... ----------+----------
...  1        | Kg
...  n/a      | ml
>>> new_table.show_headers = False
>>> new_table
...  1   | Kg
...  n/a | ml
```

---------------
### GRID
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'grid'
... +----------+----------+
... | column 1 | column 2 |
... +==========+==========+
... | 1        | Kg       |
... +----------+----------+
... | n/a      | ml       |
... +----------+----------+
>>> new_table.show_headers = False
>>> new_table
... +-----+----+
... | 1   | Kg |
... +-----+----+
... | n/a | ml |
... +-----+----+
```

---------------
### GRID_EHEADER (DEFAULT STYLE)
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'grid_eheader'
... +---------------------+
... | column 1   column 2 |
... +==========+==========+
... | 1        | Kg       |
... | n/a      | ml       |
... +----------+----------+
>>> new_table.show_headers = False
>>> new_table
... +-----+----+
... | 1   | Kg |
... | n/a | ml |
... +-----+----+
```

---------------
### GRID_EBODY
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'grid_ebody'
... +----------+----------+
... | column 1 | column 2 |
... +==========+==========+
... | 1          Kg       |
... | n/a        ml       |
... +---------------------+
>>> new_table.show_h
```eaders = False
>>> new_table
... +----------+
... | 1     Kg |
... | n/a   ml |
... +----------+
```

---------------
### GRID_EMPTY
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'grid_empty'
... +---------------------+
... | column 1   column 2 |
... +=====================+
... | 1          Kg       |
... | n/a        ml       |
... +---------------------+
>>> new_table.show_headers = False
>>> new_table
... +----------+
... | 1     Kg |
... | n/a   ml |
... +----------+
```

---------------
### PIPES
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'pipes'
... | column 1 | column 2 |
... |----------|----------|
... | 1        | Kg       |
... | n/a      | ml       |
>>> new_table.show_headers = False
>>> new_table
... |-----|----|
... | 1   | Kg |
... | n/a | ml |
```

---------------
### TILDE_GRID
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'tilde_grid'
... +----------+----------+
... | column 1 | column 2 |
... O~~~~~~~~~~O~~~~~~~~~~O
... | 1        | Kg       |
... +----------+----------+
... | n/a      | ml       |
... O~~~~~~~~~~O~~~~~~~~~~O
>>> new_table.show_headers = False
>>> new_table
... O~~~~~O~~~~O
... | 1   | Kg |
... +-----+----+
... | n/a | ml |
... O~~~~~O~~~~O
```

---------------
### TILG_EHEADER
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'tilg_eheader'
... +---------------------+
... | column 1   column 2 |
... O~~~~~~~~~~O~~~~~~~~~~O
... | 1        | Kg       |
... +----------+----------+
... | n/a      | ml       |
... O~~~~~~~~~~O~~~~~~~~~~O
>>> new_table.show_headers = False
>>> new_table
... O~~~~~O~~~~O
... | 1   | Kg |
... +-----+----+
... | n/a | ml |
... O~~~~~O~~~~O
```

---------------
### TILG_COLUMNS
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'tilg_columns'
... +----------+----------+
... | column 1 | column 2 |
... O~~~~~~~~~~O~~~~~~~~~~O
... | 1        | Kg       |
... | n/a      | ml       |
... O~~~~~~~~~~O~~~~~~~~~~O
>>> new_table.show_headers = False
>>> new_table
... O~~~~~O~~~~O
... | 1   | Kg |
... | n/a | ml |
... O~~~~~O~~~~O
```

---------------
### TILG_EMPTY
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'tilg_empty'
... +---------------------+
... | column 1   column 2 |
... O~~~~~~~~~~~~~~~~~~~~~O
... | 1          Kg       |
... | n/a        ml       |
... O~~~~~~~~~~~~~~~~~~~~~O
>>> new_table.show_headers = False
>>> new_table
... O~~~~~~~~~~O
... | 1     Kg |
... | n/a   ml |
... O~~~~~~~~~~O
```

---------------
### ORGTBL
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'orgtbl'
... | column 1 | column 2 |
... |----------+----------|
... | 1        | Kg       |
... | n/a      | ml       |
>>> new_table.show_headers = False
>>> new_table
... | 1   | Kg |
... | n/a | ml |
```

---------------
### CLEAN
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'clean'
... column 1 column 2
... ──────── ────────
... 1        Kg
... n/a      ml
... ──────── ────────
>>> new_table.show_headers = False
>>> new_table
... ─── ──
... 1   Kg
... n/a ml
... ─── ──
```

---------------
### SIMPLE
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'simple'
... ---------------------
...  column 1   column 2
... ---------------------
...  1          Kg
...  n/a        ml
... ---------------------
>>> new_table.show_headers = False
>>> new_table
... ----------
...  1     Kg
...  n/a   ml
... ----------
```

---------------
### SIMPLE_BOLD
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'simple_bold'
... =====================
...  column 1   column 2
... =====================
...  1          Kg
...  n/a        ml
... =====================
>>> new_table.show_headers = False
>>> new_table
... ==========
...  1     Kg
...  n/a   ml
... ==========
```

---------------
### SIMPLE_HEAD
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'simple_head'
...  column 1   column 2
... ---------------------
...  1          Kg
...  n/a        ml
>>> new_table.show_headers = False
>>> new_table
...  1     Kg
...  n/a   ml
```

---------------
### SIMPLE_HEAD_BOLD
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'simple_head_bold'
...  column 1   column 2
... =====================
...  1          Kg
...  n/a        ml
>>> new_table.show_headers = False
>>> new_table
...  1     Kg
...  n/a   ml
```

---------------
### SIM_TH_BL
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'sim_th_bl'
... ─────────────────────
...  column 1   column 2
... ─────────────────────
...  1          Kg
...  n/a        ml
... ─────────────────────
>>> new_table.show_headers = False
>>> new_table
... ──────────
...  1     Kg
...  n/a   ml
... ──────────
```

---------------
### SIM_BD_BL
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'sim_bd_bl'
... ═════════════════════
...  column 1   column 2
... ═════════════════════
...  1          Kg
...  n/a        ml
... ═════════════════════
>>> new_table.show_headers = False
>>> new_table
... ══════════
...  1     Kg
...  n/a   ml
... ══════════
```

---------------
### SIM_HEAD_TH_BL
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'sim_head_th_bl'
...  column 1   column 2
... ─────────────────────
...  1          Kg
...  n/a        ml
>>> new_table.show_headers = False
>>> new_table
...  1     Kg
...  n/a   ml
```

---------------
### SIM_HEAD_BD_BL
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'sim_head_bd_bl'
...  column 1   column 2
... ═════════════════════
...  1          Kg
...  n/a        ml
>>> new_table.show_headers = False
>>> new_table
...  1     Kg
...  n/a   ml
```

---------------
### DASHES
```
>>> new_table.show_headers = True
>>> new_table.style_name = 'dashes'
... ┌┄┄┄┄┄┄┄┄┄┄┬┄┄┄┄┄┄┄┄┄┄┐
... ┊ column 1 ┊ column 2 ┊
... ┝╍╍╍╍╍╍╍╍╍╍┿╍╍╍╍╍╍╍╍╍╍┥
... ┊ 1        ┊ Kg       ┊
... ┊ n/a      ┊ ml       ┊
... └┄┄┄┄┄┄┄┄┄┄┴┄┄┄┄┄┄┄┄┄┄┘
>>> new_table.show_headers = False
>>> new_table
... ┌┄┄┄┄┄┬┄┄┄┄┐
... ┊ 1   ┊ Kg ┊
... ┊ n/a ┊ ml ┊
... └┄┄┄┄┄┴┄┄┄┄┘
```
