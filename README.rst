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

We can change some of the properties of a Table instance. ``missing_val`` by default is ``''``, but accpets any value. Setting ``style_name`` tells the Table class which style to look at, but if it doesnt exist it picks ``grid_eheader`` by default. Here you can see a list of style examples.

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


# Known Issues
- Alignment is still incomplete. It wont work with all data types and it hasn't been tested if it is possible to change.
- Table doesn't adjust to console size (previusly did).
- Setting the missing value after adding data working in unintended ways.
