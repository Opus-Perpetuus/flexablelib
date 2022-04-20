**prettyTables**
============

This library is under development, and may suffer changes.

Feel free to make issues, suggestions, or pull requests.

# Instalation

### Windows

``pip install prettyTables``

### Ubuntu

``pip3 install prettyTables``

# Usage
For now it's possible to use it in two ways.

## 1. Directly passing arguments to the Table class
In this way, you can define the table instance having already the values you want at creation.
```
from prettyTables import Table

headers = ['STRING', 'LEN', 'TYPE', 'ID']

data = [['gamelang Word', 13, 'Phrase', '1e8ñrz8ty136s66ñ4b8k38qn9ñadryzb5'],
        ['gameless Elongated', 18, 'Phrase', '4j4ycaicwenh2ñs25ñmmmr239ñ23w0bn803hcs'],
        ['gamelike', 8, 'Word', 'p2in3782mub17480eq72mq3pc7v9zon'],
        ['Gamelion', 8, 'String', '4hv2d710s6vsñ8n0ybfms2c301qr7dj'], 
        ['gamelotte', 9, 'Word', '1tg5y3jn7xf9046681qe8o1pul50c046w29xz'],
        ['gamely', 6, 'String', 'mq58xu8vq84x784ngcw44w5410u28fñ'],
        ['gamene', 6, 'Word', '98r75qj996c379tg1kñpz10dw534m22a'], 
        ['gameness', 8, 'String', 'yfv5886ff04sp7a1t8z30tugq3bx47jd'], 
        ['gamesome', 8, 'Word', 'owus19312vy2hube4rdha0ej9s98v28fz'], 
        ['gamesomely', 10, 'String', '0ms888ib3768p3khz32f8272456v219']]

style = 'bold_borderline'

new_table = Table(headers=headers, rows=data, style_name=style)
print(new_table)
  
```

#### Output
```
╔════════════════════╤═════╤════════╤════════════════════════════════════════╗
║ STRING             │ LEN │ TYPE   │ ID                                     ║
╠════════════════════╪═════╪════════╪════════════════════════════════════════╣
║ gamelang Word      │  13 │ Phrase │ 1e8ñrz8ty136s66ñ4b8k38qn9ñadryzb5      ║
╟────────────────────┼─────┼────────┼────────────────────────────────────────╢
║ gameless Elongated │  18 │ Phrase │ 4j4ycaicwenh2ñs25ñmmmr239ñ23w0bn803hcs ║
╟────────────────────┼─────┼────────┼────────────────────────────────────────╢
║ gamelike           │   8 │ Word   │ p2in3782mub17480eq72mq3pc7v9zon        ║
╟────────────────────┼─────┼────────┼────────────────────────────────────────╢
║ Gamelion           │   8 │ String │ 4hv2d710s6vsñ8n0ybfms2c301qr7dj        ║
╟────────────────────┼─────┼────────┼────────────────────────────────────────╢
║ gamelotte          │   9 │ Word   │ 1tg5y3jn7xf9046681qe8o1pul50c046w29xz  ║
╟────────────────────┼─────┼────────┼────────────────────────────────────────╢
║ gamely             │   6 │ String │ mq58xu8vq84x784ngcw44w5410u28fñ        ║
╟────────────────────┼─────┼────────┼────────────────────────────────────────╢
║ gamene             │   6 │ Word   │ 98r75qj996c379tg1kñpz10dw534m22a       ║
╟────────────────────┼─────┼────────┼────────────────────────────────────────╢
║ gameness           │   8 │ String │ yfv5886ff04sp7a1t8z30tugq3bx47jd       ║
╟────────────────────┼─────┼────────┼────────────────────────────────────────╢
║ gamesome           │   8 │ Word   │ owus19312vy2hube4rdha0ej9s98v28fz      ║
╟────────────────────┼─────┼────────┼────────────────────────────────────────╢
║ gamesomely         │  10 │ String │ 0ms888ib3768p3khz32f8272456v219        ║
╚════════════════════╧═════╧════════╧════════════════════════════════════════╝
```
## 2. Using the **add** functions included and setting values

We can change some of the properties of a Table instance. ``missing_val`` by default is ``''``, but accpets any value. Setting ``style_name`` tells the Table class which style to look at, but if it doesnt exist it picks ``grid_eheader`` by default. [Here](/style_examples.md)  you can see a list of style examples.

To add columns or rows you can use both ``add_column`` and ``add_row`` indiscriminately.
```
from prettyTables import Table
new_table = Table()
new_table.missing_val = 'Unknown'
new_table.style_name = 'round_edges'
new_table.add_column('Name', ['Juan', 'Sam', 'Audrey'])
new_table.add_column('age', [19, 25, 21, 33, 34])
new_table.add_column('can pass', [False, True, True, True, False])
new_table.add_row(['Jean', 25, True])
print(new_table)
```


#### Output
```
╭─────────┬─────┬──────────╮
│ Name    │ age │ can pass │
╞═════════╪═════╪══════════╡
│ Juan    │  19 │    False │
│ Sam     │  25 │     True │
│ Audrey  │  21 │     True │
│ Unknown │  33 │     True │
│ Unknown │  34 │    False │
│ Jean    │  25 │     True │
╰─────────┴─────┴──────────╯
```
If for some reason a column or row bigger than the previus gets added, the Table class will adjust the rest for you because you may know what you are doing. Also, you can just get crazy and add empty ones. Let's see it working with the previus example.
```
new_table.add_row(['Jade', 26, True, 'What!?'])
new_table.add_column()
print(new_table)
```

#### Output
```
╭─────────┬─────┬──────────┬──────────┬──────────╮
│ Name    │ age │ can pass │ column 4 │ column 5 │
╞═════════╪═════╪══════════╪══════════╪══════════╡
│ Juan    │  19 │    False │ Unknown  │  Unknown │
│ Sam     │  25 │     True │ Unknown  │  Unknown │
│ Audrey  │  21 │     True │ Unknown  │  Unknown │
│ Unknown │  33 │     True │ Unknown  │  Unknown │
│ Unknown │  34 │    False │ Unknown  │  Unknown │
│ Jean    │  25 │     True │ Unknown  │  Unknown │
│ Jade    │  26 │     True │ What!?   │  Unknown │
╰─────────┴─────┴──────────┴──────────┴──────────╯
```
The class also sets _**automatic titles**_ for those columns that weren't assigned with one.

If you don't want to see titles at all you can hide them setting the ``show_headers`` property to ``False``.
```
new_table.show_headers = False
print(new_table)
```

#### Output
```
╭─────────┬────┬───────┬─────────┬─────────╮
│ Juan    │ 19 │ False │ Unknown │ Unknown │
│ Sam     │ 25 │  True │ Unknown │ Unknown │
│ Audrey  │ 21 │  True │ Unknown │ Unknown │
│ Unknown │ 33 │  True │ Unknown │ Unknown │
│ Unknown │ 34 │ False │ Unknown │ Unknown │
│ Jean    │ 25 │  True │ Unknown │ Unknown │
│ Jade    │ 26 │  True │ What!?  │ Unknown │
╰─────────┴────┴───────┴─────────┴─────────╯
```
---

### Showing row indexes
Using another example to show the usage of the ``show_index`` option. You can also set the start of the count and the step if you want.
```
from prettyTables import Table

new_table = Table()
new_table.index_step = 3
new_table.index_start = 6
new_table.add_column('Topic', ['Matter State', 'Check'])
new_table.add_column('Borium', [1, True])
new_table.add_column('Helium', [2, True])
new_table.add_column('Corium', [7, False])
new_table.add_column('Uranium', [-1, True])
new_table.add_row(['Bus', 25, 115, 30, 31])
new_table.add_row(['Set', int(4e2), int(25e-1), int(21e-6), int(1e2)])
new_table.add_row(['Critic Mass', False, False, False, False])
new_table.add_row(['Critic Heat', False, False, True, True])
new_table.add_row(['Critic Pressure', False, False, False, True])
new_table.add_row(['Urgent Cleaning', False, False, True, False])
new_table.add_row(['Cuadrant vals', 10, 1, 11, 12])
new_table.add_row(['Inherent mass', 425345, -2, 453213453, 242224532])
new_table.add_row(['Calamity count', 0, 0, 999, 0])
new_table.add_row(['Calamity count', 0, 0, 999, 0])
new_table.style_name = 'simple'

new_table.show_headers = False
new_table.show_index = True
print(new_table)
```

#### Output
```
---------------------------------------------------------------
  6   Matter State           1       2           7          -1
  9   Check               True    True       False        True
 12   Bus                   25     115          30          31
 15   Set                  400       2           0         100
 18   Critic Mass        False   False       False       False
 21   Critic Heat        False   False        True        True
 24   Critic Pressure    False   False       False        True
 27   Urgent Cleaning    False   False        True       False
 30   Cuadrant vals         10       1          11          12
 33   Inherent mass     425345      -2   453213453   242224532
 36   Calamity count         0       0         999           0
 39   Calamity count         0       0         999           0
---------------------------------------------------------------
```
A column of integers is placed on the left of the table. For now, try no not name columns ``"i"`` as that may conflict with the index column, directly not showing the column you added (if named like that) when ``show_index`` is set to ``True``.

Is possible to hide again the index column.
```
new_table.show_index = False
print(new_table)
```

#### Output
```
----------------------------------------------------------
 Matter State           1       2           7          -1
 Check               True    True       False        True
 Bus                   25     115          30          31
 Set                  400       2           0         100
 Critic Mass        False   False       False       False
 Critic Heat        False   False        True        True
 Critic Pressure    False   False       False        True
 Urgent Cleaning    False   False        True       False
 Cuadrant vals         10       1          11          12
 Inherent mass     425345      -2   453213453   242224532
 Calamity count         0       0         999           0
 Calamity count         0       0         999           0
----------------------------------------------------------
```

Here the index and headers are put back.
```
new_table.show_headers = True
new_table.show_index = True
print(new_table)
```

#### Output
```
----------------------------------------------------------------
  i   Topic             Borium   Helium      Corium     Uranium
----------------------------------------------------------------
  6   Matter State           1        2           7          -1
  9   Check               True     True       False        True
 12   Bus                   25      115          30          31
 15   Set                  400        2           0         100
 18   Critic Mass        False    False       False       False
 21   Critic Heat        False    False        True        True
 24   Critic Pressure    False    False       False        True
 27   Urgent Cleaning    False    False        True       False
 30   Cuadrant vals         10        1          11          12
 33   Inherent mass     425345       -2   453213453   242224532
 36   Calamity count         0        0         999           0
 39   Calamity count         0        0         999           0
----------------------------------------------------------------
```

And the index column is removed once again.
```
new_table.show_index = False
print(new_table)
```

#### Output
```
-----------------------------------------------------------
 Topic             Borium   Helium      Corium     Uranium
-----------------------------------------------------------
 Matter State           1        2           7          -1
 Check               True     True       False        True
 Bus                   25      115          30          31
 Set                  400        2           0         100
 Critic Mass        False    False       False       False
 Critic Heat        False    False        True        True
 Critic Pressure    False    False       False        True
 Urgent Cleaning    False    False        True       False
 Cuadrant vals         10        1          11          12
 Inherent mass     425345       -2   453213453   242224532
 Calamity count         0        0         999           0
 Calamity count         0        0         999           0
-----------------------------------------------------------
```
---
### Hiding empty columns and rows
As previously mentioned, empty rows and/or columns are allowed. There's also a way of hidding them by setting ``show_empty_rows`` and ``show_empty_columns`` to ``False``.

This example shows also how some of the metadata of the table changes (and can be obtained).
```
from prettyTables import Table

new_table = Table()
new_table.show_empty_columns = False
new_table.show_empty_rows = False
new_table.add_column('Topic', ['Matter State', 'Check'])
new_table.add_column('Borium', [1, True])
new_table.add_column('Helium', [2, True])
new_table.add_column('Corium', [7, False])
new_table.add_column('Uranium', [-1, True])
new_table.add_row(['Bus', 25, 115, 30, 31])
new_table.add_row(['Set', 400, 2, 0, 100])
new_table.add_row()
new_table.add_row()
new_table.add_row()
new_table.add_row(['Critic Mass', False, False, False, False])
new_table.add_row(['Critic Heat', False, False, True, True])
new_table.add_row(['Critic Pressure', False, False, False, True])
new_table.add_row(['Urgent Cleaning', False, False, True, False])
new_table.add_row(['Cuadrant vals', 10, 1, 11, 12])
new_table.add_row()
new_table.add_row()
new_table.add_row(['Inherent mass', 425345, -2, 453213453, 242224532])
new_table.add_row(['Calamity count', 0, 0, 999, 0])
new_table.add_row()
new_table.add_row(['Calamity count', 0, 0, 999, 0])
new_table.add_column()
new_table.add_column()
new_table.add_column()
new_table.style_name = 'bheader_columns'
new_table.show_index = True

print(new_table)
print('columns: ', new_table.column_count)
print('rows: ', new_table.row_count)
print('internal count of columns: ', new_table.internal_column_count)
print('internal count of rows: ', new_table.internal_row_count)
print('empty column indexes: ', new_table.empty_columns_i)
print('empty row indexes: ', new_table.empty_rows_i)
new_table.show_index = False
new_table.show_empty_columns = True
new_table.show_empty_rows = True
print(new_table)
print('columns: ', new_table.column_count)
print('rows: ', new_table.row_count)
print('internal count of columns: ', new_table.internal_column_count)
print('internal count of rows: ', new_table.internal_row_count)
```

#### Output
```
╔════╦═════════════════╦════════╦════════╦═══════════╦═══════════╗
║  i ║ Topic           ║ Borium ║ Helium ║    Corium ║   Uranium ║
╚════╩═════════════════╩════════╩════════╩═══════════╩═══════════╝
│  0 │ Matter State    │      1 │      2 │         7 │        -1 │
│  1 │ Check           │   True │   True │     False │      True │
│  2 │ Bus             │     25 │    115 │        30 │        31 │
│  3 │ Set             │    400 │      2 │         0 │       100 │
│  4 │ Critic Mass     │  False │  False │     False │     False │
│  5 │ Critic Heat     │  False │  False │      True │      True │
│  6 │ Critic Pressure │  False │  False │     False │      True │
│  7 │ Urgent Cleaning │  False │  False │      True │     False │
│  8 │ Cuadrant vals   │     10 │      1 │        11 │        12 │
│  9 │ Inherent mass   │ 425345 │     -2 │ 453213453 │ 242224532 │
│ 10 │ Calamity count  │      0 │      0 │       999 │         0 │
│ 11 │ Calamity count  │      0 │      0 │       999 │         0 │
└────┴─────────────────┴────────┴────────┴───────────┴───────────┘
columns:  5
rows:  12
internal count of columns:  9
internal count of rows:  18
empty column indexes:  [5, 6, 7]
empty row indexes:  [4, 5, 6, 12, 13, 16]
╔═════════════════╦════════╦════════╦═══════════╦═══════════╦══════════╦══════════╦══════════╗
║ Topic           ║ Borium ║ Helium ║    Corium ║   Uranium ║ column 6 ║ column 7 ║ column 8 ║
╚═════════════════╩════════╩════════╩═══════════╩═══════════╩══════════╩══════════╩══════════╝
│ Matter State    │      1 │      2 │         7 │        -1 │          │          │          │
│ Check           │   True │   True │     False │      True │          │          │          │
│ Bus             │     25 │    115 │        30 │        31 │          │          │          │
│ Set             │    400 │      2 │         0 │       100 │          │          │          │
│                 │        │        │           │           │          │          │          │
│                 │        │        │           │           │          │          │          │
│                 │        │        │           │           │          │          │          │
│ Critic Mass     │  False │  False │     False │     False │          │          │          │
│ Critic Heat     │  False │  False │      True │      True │          │          │          │
│ Critic Pressure │  False │  False │     False │      True │          │          │          │
│ Urgent Cleaning │  False │  False │      True │     False │          │          │          │
│ Cuadrant vals   │     10 │      1 │        11 │        12 │          │          │          │
│                 │        │        │           │           │          │          │          │
│                 │        │        │           │           │          │          │          │
│ Inherent mass   │ 425345 │     -2 │ 453213453 │ 242224532 │          │          │          │
│ Calamity count  │      0 │      0 │       999 │         0 │          │          │          │
│                 │        │        │           │           │          │          │          │
│ Calamity count  │      0 │      0 │       999 │         0 │          │          │          │
└─────────────────┴────────┴────────┴───────────┴───────────┴──────────┴──────────┴──────────┘
columns:  8
rows:  18
internal count of columns:  8
internal count of rows:  18
```


# Known Issues
- Alignment is still incomplete. It wont work with all data types and it hasn't been tested if it is possible to change.
- Table doesn't adjust to console size (previusly did).
- Setting the ``missing_value`` after adding data working in unintended ways.
- Setting the ``index_start`` and ``index_step`` properties after adding data wont make anything
- Naming a column ``"i"`` will cause it to not be shown when the index column is.
